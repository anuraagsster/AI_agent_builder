import time
from threading import Thread

class ResourceMonitor:
    """
    Monitors and manages system resources to ensure optimal utilization
    and prevent resource exhaustion.
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.resources = {}
        self.thresholds = {}
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = {}
        
    def register_resource(self, resource_id, initial_capacity, warning_threshold=0.8, critical_threshold=0.95):
        """
        Register a resource to be monitored
        
        Args:
            resource_id: Unique identifier for the resource
            initial_capacity: Initial capacity of the resource
            warning_threshold: Threshold for warning alerts (0.0-1.0)
            critical_threshold: Threshold for critical alerts (0.0-1.0)
        """
        self.resources[resource_id] = {
            'capacity': initial_capacity,
            'used': 0,
            'utilization': 0.0,
            'status': 'normal'
        }
        
        self.thresholds[resource_id] = {
            'warning': warning_threshold,
            'critical': critical_threshold
        }
        
    def update_resource_usage(self, resource_id, usage):
        """
        Update the current usage of a resource
        
        Args:
            resource_id: ID of the resource
            usage: Current usage value
        """
        if resource_id in self.resources:
            self.resources[resource_id]['used'] = usage
            capacity = self.resources[resource_id]['capacity']
            
            if capacity > 0:
                utilization = usage / capacity
                self.resources[resource_id]['utilization'] = utilization
                
                # Update status based on thresholds
                if utilization >= self.thresholds[resource_id]['critical']:
                    new_status = 'critical'
                elif utilization >= self.thresholds[resource_id]['warning']:
                    new_status = 'warning'
                else:
                    new_status = 'normal'
                
                old_status = self.resources[resource_id]['status']
                self.resources[resource_id]['status'] = new_status
                
                # Trigger callbacks if status changed
                if old_status != new_status and resource_id in self.callbacks:
                    for callback in self.callbacks.get(resource_id, []):
                        callback(resource_id, new_status, utilization)
        
    def register_threshold_callback(self, resource_id, callback):
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
        
    def start_monitoring(self, interval=5):
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
            
    def _monitor_loop(self, interval):
        """Internal monitoring loop"""
        while self.monitoring:
            # In a real implementation, this would collect actual resource metrics
            # For now, we'll just sleep
            time.sleep(interval)
            
    def get_resource_status(self, resource_id=None):
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