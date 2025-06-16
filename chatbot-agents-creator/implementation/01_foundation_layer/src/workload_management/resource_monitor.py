import time
import boto3
from threading import Thread
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import numpy as np
from sklearn.linear_model import LinearRegression

class ResourceMonitor:
    """
    Monitors and manages system resources to ensure optimal utilization
    and prevent resource exhaustion. Supports CloudWatch integration,
    resource forecasting, auto-scaling, and client-specific monitoring.
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.resources = {}
        self.thresholds = {}
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = {}
        self.client_resources = {}  # client_id -> resource_id -> usage history
        self.forecast_models = {}  # resource_id -> forecasting model
        self.cloudwatch_client = None
        self.auto_scaling_client = None
        
        # Initialize AWS clients if configured
        if self.config.get('use_aws', False):
            self._initialize_aws_clients()
            
    def _initialize_aws_clients(self):
        """Initialize AWS clients for CloudWatch and Auto Scaling"""
        try:
            region = self.config.get('aws_region', 'us-east-1')
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
            self.auto_scaling_client = boto3.client('autoscaling', region_name=region)
        except Exception as e:
            print(f"Error initializing AWS clients: {str(e)}")
            
    def register_resource(self, resource_id: str, initial_capacity: float, 
                         warning_threshold: float = 0.8, critical_threshold: float = 0.95,
                         client_id: Optional[str] = None):
        """
        Register a resource to be monitored
        
        Args:
            resource_id: Unique identifier for the resource
            initial_capacity: Initial capacity of the resource
            warning_threshold: Threshold for warning alerts (0.0-1.0)
            critical_threshold: Threshold for critical alerts (0.0-1.0)
            client_id: Optional client ID for client-specific resources
        """
        self.resources[resource_id] = {
            'capacity': initial_capacity,
            'used': 0,
            'utilization': 0.0,
            'status': 'normal',
            'client_id': client_id,
            'history': [],  # List of (timestamp, usage) tuples
            'auto_scaling_group': None  # Auto Scaling group name if applicable
        }
        
        self.thresholds[resource_id] = {
            'warning': warning_threshold,
            'critical': critical_threshold
        }
        
        # Initialize client-specific tracking
        if client_id:
            if client_id not in self.client_resources:
                self.client_resources[client_id] = {}
            self.client_resources[client_id][resource_id] = []
            
        # Initialize forecasting model
        self.forecast_models[resource_id] = LinearRegression()
        
    def update_resource_usage(self, resource_id: str, usage: float, client_id: Optional[str] = None):
        """
        Update the current usage of a resource
        
        Args:
            resource_id: ID of the resource
            usage: Current usage value
            client_id: Optional client ID for client-specific resources
        """
        if resource_id in self.resources:
            resource = self.resources[resource_id]
            resource['used'] = usage
            capacity = resource['capacity']
            
            if capacity > 0:
                utilization = usage / capacity
                resource['utilization'] = utilization
                
                # Record usage history
                timestamp = datetime.now()
                resource['history'].append((timestamp, usage))
                
                # Update client-specific history
                if client_id and client_id in self.client_resources:
                    if resource_id in self.client_resources[client_id]:
                        self.client_resources[client_id][resource_id].append((timestamp, usage))
                
                # Update status based on thresholds
                if utilization >= self.thresholds[resource_id]['critical']:
                    new_status = 'critical'
                elif utilization >= self.thresholds[resource_id]['warning']:
                    new_status = 'warning'
                else:
                    new_status = 'normal'
                
                old_status = resource['status']
                resource['status'] = new_status
                
                # Send metrics to CloudWatch
                if self.cloudwatch_client:
                    self._send_cloudwatch_metrics(resource_id, utilization, client_id)
                
                # Check auto-scaling conditions
                if resource['auto_scaling_group']:
                    self._check_auto_scaling(resource_id, utilization)
                
                # Trigger callbacks if status changed
                if old_status != new_status and resource_id in self.callbacks:
                    for callback in self.callbacks.get(resource_id, []):
                        callback(resource_id, new_status, utilization)
                        
    def _send_cloudwatch_metrics(self, resource_id: str, utilization: float, client_id: Optional[str] = None):
        """Send resource metrics to CloudWatch"""
        try:
            metric_data = [{
                'MetricName': 'ResourceUtilization',
                'Value': utilization,
                'Unit': 'Percent',
                'Dimensions': [
                    {'Name': 'ResourceId', 'Value': resource_id}
                ],
                'Timestamp': datetime.now()
            }]
            
            if client_id:
                metric_data[0]['Dimensions'].append({
                    'Name': 'ClientId',
                    'Value': client_id
                })
            
            self.cloudwatch_client.put_metric_data(
                Namespace='AgentBuilder/Resources',
                MetricData=metric_data
            )
        except Exception as e:
            print(f"Error sending metrics to CloudWatch: {str(e)}")
            
    def _check_auto_scaling(self, resource_id: str, utilization: float):
        """Check and trigger auto-scaling actions if needed"""
        try:
            resource = self.resources[resource_id]
            auto_scaling_group = resource['auto_scaling_group']
            
            if not auto_scaling_group or not self.auto_scaling_client:
                return
                
            # Get current auto scaling group state
            response = self.auto_scaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[auto_scaling_group]
            )
            
            if not response['AutoScalingGroups']:
                return
                
            asg = response['AutoScalingGroups'][0]
            current_capacity = asg['DesiredCapacity']
            
            # Scale up if utilization is high
            if utilization >= self.thresholds[resource_id]['critical']:
                new_capacity = min(
                    current_capacity + 1,
                    asg['MaxSize']
                )
                if new_capacity > current_capacity:
                    self.auto_scaling_client.set_desired_capacity(
                        AutoScalingGroupName=auto_scaling_group,
                        DesiredCapacity=new_capacity
                    )
                    
            # Scale down if utilization is low
            elif utilization < self.thresholds[resource_id]['warning'] * 0.5:
                new_capacity = max(
                    current_capacity - 1,
                    asg['MinSize']
                )
                if new_capacity < current_capacity:
                    self.auto_scaling_client.set_desired_capacity(
                        AutoScalingGroupName=auto_scaling_group,
                        DesiredCapacity=new_capacity
                    )
                    
        except Exception as e:
            print(f"Error in auto-scaling check: {str(e)}")
            
    def set_auto_scaling_group(self, resource_id: str, auto_scaling_group: str):
        """Set the Auto Scaling group for a resource"""
        if resource_id in self.resources:
            self.resources[resource_id]['auto_scaling_group'] = auto_scaling_group
            
    def forecast_resource_usage(self, resource_id: str, hours_ahead: int = 24) -> List[float]:
        """
        Forecast resource usage for the specified number of hours ahead
        
        Args:
            resource_id: ID of the resource to forecast
            hours_ahead: Number of hours to forecast ahead
            
        Returns:
            List of forecasted usage values
        """
        if resource_id not in self.resources:
            return []
            
        resource = self.resources[resource_id]
        history = resource['history']
        
        if len(history) < 24:  # Need at least 24 hours of history
            return []
            
        # Prepare training data
        X = np.array([(t - history[0][0]).total_seconds() / 3600 for t, _ in history]).reshape(-1, 1)
        y = np.array([u for _, u in history])
        
        # Train model
        model = self.forecast_models[resource_id]
        model.fit(X, y)
        
        # Generate forecast timestamps
        last_time = history[-1][0]
        forecast_times = [last_time + timedelta(hours=i) for i in range(1, hours_ahead + 1)]
        X_forecast = np.array([(t - history[0][0]).total_seconds() / 3600 for t in forecast_times]).reshape(-1, 1)
        
        # Generate forecasts
        forecasts = model.predict(X_forecast)
        
        return forecasts.tolist()
        
    def get_client_resource_usage(self, client_id: str) -> Dict[str, List[float]]:
        """
        Get resource usage history for a specific client
        
        Args:
            client_id: Client ID to get usage for
            
        Returns:
            Dictionary mapping resource IDs to usage history
        """
        if client_id not in self.client_resources:
            return {}
            
        return {
            resource_id: [usage for _, usage in history]
            for resource_id, history in self.client_resources[client_id].items()
        }
        
    def get_resource_forecast(self, resource_id: str, hours_ahead: int = 24) -> Dict[str, Any]:
        """
        Get detailed resource forecast including confidence intervals
        
        Args:
            resource_id: ID of the resource to forecast
            hours_ahead: Number of hours to forecast ahead
            
        Returns:
            Dictionary containing forecast data
        """
        forecasts = self.forecast_resource_usage(resource_id, hours_ahead)
        
        if not forecasts:
            return {
                'forecasts': [],
                'confidence_intervals': [],
                'resource_id': resource_id,
                'hours_ahead': hours_ahead
            }
            
        # Calculate confidence intervals (simple implementation)
        std_dev = np.std(forecasts)
        confidence_intervals = [
            (max(0, f - 1.96 * std_dev), f + 1.96 * std_dev)
            for f in forecasts
        ]
        
        return {
            'forecasts': forecasts,
            'confidence_intervals': confidence_intervals,
            'resource_id': resource_id,
            'hours_ahead': hours_ahead
        }
        
    def register_threshold_callback(self, resource_id: str, callback):
        """
        Register a callback to be called when resource utilization crosses a threshold
        
        Args:
            resource_id: ID of the resource to monitor
            callback: Function to call when threshold is crossed
                      Function signature: callback(resource_id, status, utilization)
        """
        if resource_id not in self.callbacks:
            self.callbacks[resource_id] = []
            
        self.callbacks[resource_id].append(callback)
        
    def start_monitoring(self, interval: int = 5):
        """
        Start the monitoring thread
        
        Args:
            interval: Monitoring interval in seconds
        """
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = Thread(target=self._monitor_loop, args=(interval,))
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            
    def _monitor_loop(self, interval: int):
        """Internal monitoring loop"""
        while self.monitoring:
            # Collect metrics from CloudWatch if available
            if self.cloudwatch_client:
                self._collect_cloudwatch_metrics()
            
            # Update forecasting models
            self._update_forecast_models()
            
            time.sleep(interval)
            
    def _collect_cloudwatch_metrics(self):
        """Collect metrics from CloudWatch for all resources"""
        try:
            for resource_id, resource in self.resources.items():
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AgentBuilder/Resources',
                    MetricName='ResourceUtilization',
                    Dimensions=[{'Name': 'ResourceId', 'Value': resource_id}],
                    StartTime=datetime.now() - timedelta(minutes=5),
                    EndTime=datetime.now(),
                    Period=300,
                    Statistics=['Average']
                )
                
                if response['Datapoints']:
                    latest = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                    self.update_resource_usage(
                        resource_id,
                        latest['Average'] * resource['capacity'],
                        resource.get('client_id')
                    )
        except Exception as e:
            print(f"Error collecting CloudWatch metrics: {str(e)}")
            
    def _update_forecast_models(self):
        """Update forecasting models with recent data"""
        for resource_id, resource in self.resources.items():
            if len(resource['history']) >= 24:  # Need at least 24 hours of history
                X = np.array([(t - resource['history'][0][0]).total_seconds() / 3600 
                            for t, _ in resource['history']]).reshape(-1, 1)
                y = np.array([u for _, u in resource['history']])
                
                self.forecast_models[resource_id].fit(X, y)
                
    def get_resource_status(self, resource_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current status of resources
        
        Args:
            resource_id: Optional specific resource to get status for
            
        Returns:
            Dictionary of resource status information
        """
        if resource_id:
            return self.resources.get(resource_id, {})
        return self.resources