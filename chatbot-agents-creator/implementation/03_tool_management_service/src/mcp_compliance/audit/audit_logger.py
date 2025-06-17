"""
Audit Logger for MCP Compliance Layer.

This module handles audit logging for the Tool Management Service.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

class AuditLogger:
    """
    Handles audit logging for the Tool Management Service.
    
    This class manages logging of security-relevant events and actions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the audit logger.
        
        Args:
            config: Audit logging configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AWS clients
        self._init_aws_clients()
        
    def _init_aws_clients(self):
        """Initialize AWS clients for audit logging."""
        self.cloudwatch = boto3.client('cloudwatch')
        self.firehose = boto3.client('firehose')
        
    def log_event(self, event_type: str, user_id: str, action: str,
                  resource: str, details: Dict[str, Any] = None) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of event (e.g., 'auth', 'access', 'modification')
            user_id: ID of the user performing the action
            action: Action performed
            resource: Resource affected
            details: Additional event details
        """
        try:
            # Create event record
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'details': details or {}
            }
            
            # Send to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace=self.config.get('cloudwatch_namespace', 'ToolManagementService/Audit'),
                MetricData=[{
                    'MetricName': event_type,
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'UserID', 'Value': user_id},
                        {'Name': 'Action', 'Value': action},
                        {'Name': 'Resource', 'Value': resource}
                    ]
                }]
            )
            
            # Send to Firehose for long-term storage
            self.firehose.put_record(
                DeliveryStreamName=self.config['audit_stream_name'],
                Record={'Data': json.dumps(event) + '\n'}
            )
            
            # Log locally
            self.logger.info(f"Audit event: {json.dumps(event)}")
        except Exception as e:
            self.logger.error(f"Audit logging failed: {e}")
            raise 