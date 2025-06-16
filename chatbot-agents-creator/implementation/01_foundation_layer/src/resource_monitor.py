"""
Resource monitoring and management component for the Foundation Layer.
"""

import os
import time
import logging
import boto3
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

class ResourceMonitor:
    """Monitors and manages system resources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the resource monitor."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cloudwatch = boto3.client('cloudwatch')
        self.auto_scaling = boto3.client('autoscaling')
        self.resources = {}
        self.client_resources = {}
        self.metrics_buffer = []
        self.last_metrics_send = time.time()
        self.metrics_send_interval = 60  # seconds
        
    def register_resource(self, resource_id: str, resource_type: str, client_id: Optional[str] = None):
        """Register a resource for monitoring."""
        self.resources[resource_id] = {
            'type': resource_type,
            'client_id': client_id,
            'created_at': datetime.utcnow(),
            'usage_history': []
        }
        
        if client_id:
            if client_id not in self.client_resources:
                self.client_resources[client_id] = []
            self.client_resources[client_id].append(resource_id)
            
        self.logger.info(f"Registered resource {resource_id} of type {resource_type}")
        
    def update_resource_usage(self, resource_id: str, usage: Dict[str, float], client_id: Optional[str] = None):
        """Update resource usage metrics."""
        if resource_id not in self.resources:
            self.logger.warning(f"Resource {resource_id} not registered")
            return
            
        timestamp = datetime.utcnow()
        self.resources[resource_id]['usage_history'].append({
            'timestamp': timestamp,
            'usage': usage
        })
        
        # Keep only last 24 hours of history
        cutoff = timestamp.timestamp() - 86400
        self.resources[resource_id]['usage_history'] = [
            h for h in self.resources[resource_id]['usage_history']
            if h['timestamp'].timestamp() > cutoff
        ]
        
        # Add to metrics buffer
        self.metrics_buffer.append({
            'MetricName': 'ResourceUsage',
            'Value': usage.get('value', 0),
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'ResourceId', 'Value': resource_id},
                {'Name': 'ResourceType', 'Value': self.resources[resource_id]['type']},
                {'Name': 'ClientId', 'Value': client_id or 'default'}
            ],
            'Timestamp': timestamp
        })
        
        # Send metrics if buffer is full or interval has passed
        if len(self.metrics_buffer) >= 20 or (time.time() - self.last_metrics_send) >= self.metrics_send_interval:
            self._send_metrics()
            
    def _send_metrics(self):
        """Send buffered metrics to CloudWatch."""
        if not self.metrics_buffer:
            return
            
        try:
            self.cloudwatch.put_metric_data(
                Namespace='ResourceMonitor',
                MetricData=self.metrics_buffer
            )
            self.metrics_buffer = []
            self.last_metrics_send = time.time()
        except ClientError as e:
            self.logger.error(f"Failed to send metrics: {e}")
            
    def get_resource_usage(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get current resource usage."""
        if resource_id not in self.resources:
            return None
            
        history = self.resources[resource_id]['usage_history']
        if not history:
            return None
            
        return history[-1]['usage']
        
    def get_client_resources(self, client_id: str) -> List[str]:
        """Get all resources associated with a client."""
        return self.client_resources.get(client_id, [])
        
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
    def check_resource_health(self, resource_id: str) -> Dict[str, Any]:
        """Check health status of a resource."""
        if resource_id not in self.resources:
            return {'status': 'unknown', 'message': 'Resource not found'}
            
        usage = self.get_resource_usage(resource_id)
        if not usage:
            return {'status': 'unknown', 'message': 'No usage data available'}
            
        thresholds = self.config.get('resource_thresholds', {})
        resource_type = self.resources[resource_id]['type']
        type_thresholds = thresholds.get(resource_type, {})
        
        status = 'healthy'
        issues = []
        
        for metric, value in usage.items():
            threshold = type_thresholds.get(metric)
            if threshold and value > threshold:
                status = 'unhealthy'
                issues.append(f"{metric} exceeds threshold ({value} > {threshold})")
                
        return {
            'status': status,
            'issues': issues,
            'usage': usage
        }
        
    def get_resource_forecast(self, resource_id: str, hours: int = 24) -> Dict[str, Any]:
        """Forecast resource usage for the next N hours."""
        if resource_id not in self.resources:
            return {'error': 'Resource not found'}
            
        history = self.resources[resource_id]['usage_history']
        if not history:
            return {'error': 'No usage history available'}
            
        # Simple moving average forecast
        window_size = min(len(history), 12)  # Use last 12 data points or all if less
        recent_history = history[-window_size:]
        
        forecast = {}
        for metric in recent_history[0]['usage'].keys():
            values = [h['usage'][metric] for h in recent_history]
            avg = sum(values) / len(values)
            forecast[metric] = avg
            
        return {
            'forecast': forecast,
            'confidence': 0.8,  # Placeholder for actual confidence calculation
            'hours': hours
        }
        
    def update_auto_scaling(self, resource_id: str):
        """Update auto scaling based on resource usage."""
        if resource_id not in self.resources:
            return
            
        usage = self.get_resource_usage(resource_id)
        if not usage:
            return
            
        asg_name = self.config.get('auto_scaling_groups', {}).get(resource_id)
        if not asg_name:
            return
            
        try:
            current_capacity = self.auto_scaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )['AutoScalingGroups'][0]['DesiredCapacity']
            
            # Simple scaling logic - can be made more sophisticated
            if usage.get('value', 0) > 80:  # Scale up at 80% usage
                new_capacity = min(current_capacity + 1, self.config.get('max_capacity', 10))
            elif usage.get('value', 0) < 20:  # Scale down at 20% usage
                new_capacity = max(current_capacity - 1, self.config.get('min_capacity', 1))
            else:
                return
                
            if new_capacity != current_capacity:
                self.auto_scaling.set_desired_capacity(
                    AutoScalingGroupName=asg_name,
                    DesiredCapacity=new_capacity
                )
                self.logger.info(f"Updated {asg_name} capacity to {new_capacity}")
                
        except ClientError as e:
            self.logger.error(f"Failed to update auto scaling: {e}")
            
    def cleanup(self):
        """Clean up resources and send final metrics."""
        self._send_metrics()  # Send any remaining metrics
        self.resources.clear()
        self.client_resources.clear() 