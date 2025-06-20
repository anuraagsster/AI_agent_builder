"""
Alert Routing System for the Foundation Layer

This module provides intelligent alert routing capabilities that can route different types
of alerts to appropriate destinations based on severity, type, ownership, and other criteria.
"""

import json
import logging
import time
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from botocore.exceptions import ClientError

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """Alert types"""
    RESOURCE_UTILIZATION = "resource_utilization"
    SYSTEM_ERROR = "system_error"
    SECURITY_BREACH = "security_breach"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    QUALITY_ISSUE = "quality_issue"
    TASK_FAILURE = "task_failure"
    AGENT_OFFLINE = "agent_offline"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ISSUE = "dependency_issue"
    CLIENT_SPECIFIC = "client_specific"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]
    client_id: Optional[str] = None
    owner_id: Optional[str] = None
    resource_id: Optional[str] = None
    agent_id: Optional[str] = None

@dataclass
class AlertDestination:
    """Alert destination configuration"""
    name: str
    type: str  # email, slack, sns, webhook, etc.
    config: Dict[str, Any]
    enabled: bool = True
    filters: Dict[str, Any] = None  # Severity, type, client_id filters

class AlertRouter:
    """
    Intelligent alert routing system that routes alerts to appropriate destinations
    based on severity, type, ownership, and other criteria.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the alert router"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Alert routing configuration
        self.destinations: Dict[str, AlertDestination] = {}
        self.routing_rules: List[Dict[str, Any]] = []
        self.alert_history: List[Alert] = []
        self.max_history_size = self.config.get('max_history_size', 1000)
        
        # AWS clients for notifications
        self.sns_client = None
        self.ses_client = None
        self.slack_webhook_url = None
        
        # Initialize AWS clients if configured
        if self.config.get('use_aws', False):
            self._initialize_aws_clients()
            
        # Load default routing rules
        self._load_default_routing_rules()
        
    def _initialize_aws_clients(self):
        """Initialize AWS clients for notifications"""
        try:
            region = self.config.get('aws_region', 'us-east-1')
            self.sns_client = boto3.client('sns', region_name=region)
            self.ses_client = boto3.client('ses', region_name=region)
        except Exception as e:
            self.logger.error(f"Error initializing AWS clients: {str(e)}")
            
    def _load_default_routing_rules(self):
        """Load default routing rules"""
        default_rules = [
            {
                'name': 'critical_alerts',
                'conditions': {
                    'severity': [AlertSeverity.CRITICAL],
                    'type': [AlertType.SECURITY_BREACH, AlertType.SYSTEM_ERROR]
                },
                'destinations': ['admin_email', 'admin_slack', 'sns_critical'],
                'priority': 1
            },
            {
                'name': 'resource_alerts',
                'conditions': {
                    'type': [AlertType.RESOURCE_UTILIZATION, AlertType.PERFORMANCE_DEGRADATION]
                },
                'destinations': ['ops_slack', 'sns_resources'],
                'priority': 2
            },
            {
                'name': 'client_alerts',
                'conditions': {
                    'client_id': 'not_null'
                },
                'destinations': ['client_notifications'],
                'priority': 3
            },
            {
                'name': 'quality_alerts',
                'conditions': {
                    'type': [AlertType.QUALITY_ISSUE, AlertType.TASK_FAILURE]
                },
                'destinations': ['quality_team_slack'],
                'priority': 4
            },
            {
                'name': 'default_alerts',
                'conditions': {},
                'destinations': ['general_slack'],
                'priority': 5
            }
        ]
        
        for rule in default_rules:
            self.add_routing_rule(rule)
            
    def add_destination(self, destination: AlertDestination):
        """
        Add an alert destination
        
        Args:
            destination: AlertDestination configuration
        """
        self.destinations[destination.name] = destination
        self.logger.info(f"Added alert destination: {destination.name}")
        
    def remove_destination(self, destination_name: str):
        """
        Remove an alert destination
        
        Args:
            destination_name: Name of the destination to remove
        """
        if destination_name in self.destinations:
            del self.destinations[destination_name]
            self.logger.info(f"Removed alert destination: {destination_name}")
            
    def add_routing_rule(self, rule: Dict[str, Any]):
        """
        Add a routing rule
        
        Args:
            rule: Routing rule configuration
        """
        self.routing_rules.append(rule)
        # Sort rules by priority (lower number = higher priority)
        self.routing_rules.sort(key=lambda x: x.get('priority', 999))
        self.logger.info(f"Added routing rule: {rule.get('name', 'unnamed')}")
        
    def remove_routing_rule(self, rule_name: str):
        """
        Remove a routing rule
        
        Args:
            rule_name: Name of the rule to remove
        """
        self.routing_rules = [rule for rule in self.routing_rules if rule.get('name') != rule_name]
        self.logger.info(f"Removed routing rule: {rule_name}")
        
    def route_alert(self, alert: Alert) -> Dict[str, Any]:
        """
        Route an alert to appropriate destinations
        
        Args:
            alert: Alert to route
            
        Returns:
            Dictionary with routing results
        """
        # Add alert to history
        self._add_to_history(alert)
        
        # Find matching routing rules
        matching_rules = self._find_matching_rules(alert)
        
        if not matching_rules:
            self.logger.warning(f"No routing rules matched for alert: {alert.id}")
            return {
                'status': 'failed',
                'error': 'No matching routing rules found',
                'alert_id': alert.id
            }
            
        # Route to destinations based on matching rules
        results = {
            'status': 'routed',
            'alert_id': alert.id,
            'destinations': [],
            'successful': 0,
            'failed': 0
        }
        
        sent_destinations = set()  # Avoid duplicate sends
        
        for rule in matching_rules:
            for dest_name in rule.get('destinations', []):
                if dest_name in sent_destinations:
                    continue
                    
                if dest_name not in self.destinations:
                    self.logger.warning(f"Destination not found: {dest_name}")
                    results['failed'] += 1
                    continue
                    
                destination = self.destinations[dest_name]
                if not destination.enabled:
                    continue
                    
                # Check destination filters
                if not self._check_destination_filters(alert, destination):
                    continue
                    
                # Send alert to destination
                send_result = self._send_to_destination(alert, destination)
                
                results['destinations'].append({
                    'name': dest_name,
                    'type': destination.type,
                    'result': send_result
                })
                
                if send_result.get('status') == 'sent':
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    
                sent_destinations.add(dest_name)
                
        # Update overall status
        if results['failed'] > 0 and results['successful'] == 0:
            results['status'] = 'failed'
        elif results['failed'] > 0:
            results['status'] = 'partial'
            
        return results
        
    def _find_matching_rules(self, alert: Alert) -> List[Dict[str, Any]]:
        """Find routing rules that match the alert"""
        matching_rules = []
        
        for rule in self.routing_rules:
            if self._rule_matches_alert(alert, rule):
                matching_rules.append(rule)
                
        return matching_rules
        
    def _rule_matches_alert(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if a rule matches an alert"""
        conditions = rule.get('conditions', {})
        
        # Check severity
        if 'severity' in conditions:
            if alert.severity not in conditions['severity']:
                return False
                
        # Check type
        if 'type' in conditions:
            if alert.type not in conditions['type']:
                return False
                
        # Check client_id
        if 'client_id' in conditions:
            if conditions['client_id'] == 'not_null':
                if not alert.client_id:
                    return False
            elif alert.client_id != conditions['client_id']:
                return False
                
        # Check owner_id
        if 'owner_id' in conditions:
            if alert.owner_id != conditions['owner_id']:
                return False
                
        # Check resource_id
        if 'resource_id' in conditions:
            if alert.resource_id != conditions['resource_id']:
                return False
                
        # Check agent_id
        if 'agent_id' in conditions:
            if alert.agent_id != conditions['agent_id']:
                return False
                
        return True
        
    def _check_destination_filters(self, alert: Alert, destination: AlertDestination) -> bool:
        """Check if alert passes destination filters"""
        if not destination.filters:
            return True
            
        filters = destination.filters
        
        # Check severity filter
        if 'min_severity' in filters:
            severity_order = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
            min_severity_index = severity_order.index(filters['min_severity'])
            alert_severity_index = severity_order.index(alert.severity)
            if alert_severity_index < min_severity_index:
                return False
                
        # Check type filter
        if 'types' in filters:
            if alert.type not in filters['types']:
                return False
                
        # Check client filter
        if 'client_ids' in filters:
            if alert.client_id not in filters['client_ids']:
                return False
                
        return True
        
    def _send_to_destination(self, alert: Alert, destination: AlertDestination) -> Dict[str, Any]:
        """Send alert to a specific destination"""
        try:
            if destination.type == 'email':
                return self._send_email(alert, destination)
            elif destination.type == 'slack':
                return self._send_slack(alert, destination)
            elif destination.type == 'sns':
                return self._send_sns(alert, destination)
            elif destination.type == 'webhook':
                return self._send_webhook(alert, destination)
            else:
                return {
                    'status': 'failed',
                    'error': f'Unsupported destination type: {destination.type}'
                }
        except Exception as e:
            self.logger.error(f"Error sending to destination {destination.name}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
            
    def _send_email(self, alert: Alert, destination: AlertDestination) -> Dict[str, Any]:
        """Send alert via email"""
        if not self.ses_client:
            return {'status': 'failed', 'error': 'SES client not initialized'}
            
        try:
            to_addresses = destination.config.get('to_addresses', [])
            from_address = destination.config.get('from_address')
            
            if not to_addresses or not from_address:
                return {'status': 'failed', 'error': 'Missing email configuration'}
                
            subject = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = self._format_email_body(alert)
            
            response = self.ses_client.send_email(
                Source=from_address,
                Destination={'ToAddresses': to_addresses},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            
            return {
                'status': 'sent',
                'message_id': response.get('MessageId')
            }
            
        except ClientError as e:
            return {'status': 'failed', 'error': str(e)}
            
    def _send_slack(self, alert: Alert, destination: AlertDestination) -> Dict[str, Any]:
        """Send alert via Slack webhook"""
        import requests
        
        webhook_url = destination.config.get('webhook_url')
        if not webhook_url:
            return {'status': 'failed', 'error': 'Missing Slack webhook URL'}
            
        try:
            # Format Slack message
            color_map = {
                AlertSeverity.INFO: '#36a64f',
                AlertSeverity.WARNING: '#ffa500',
                AlertSeverity.ERROR: '#ff0000',
                AlertSeverity.CRITICAL: '#8b0000'
            }
            
            slack_message = {
                'attachments': [{
                    'color': color_map.get(alert.severity, '#36a64f'),
                    'title': f"[{alert.severity.value.upper()}] {alert.title}",
                    'text': alert.message,
                    'fields': [
                        {
                            'title': 'Source',
                            'value': alert.source,
                            'short': True
                        },
                        {
                            'title': 'Time',
                            'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            'short': True
                        }
                    ],
                    'footer': 'Foundation Layer Alert System'
                }]
            }
            
            # Add client info if available
            if alert.client_id:
                slack_message['attachments'][0]['fields'].append({
                    'title': 'Client ID',
                    'value': alert.client_id,
                    'short': True
                })
                
            response = requests.post(webhook_url, json=slack_message)
            response.raise_for_status()
            
            return {'status': 'sent'}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
            
    def _send_sns(self, alert: Alert, destination: AlertDestination) -> Dict[str, Any]:
        """Send alert via SNS"""
        if not self.sns_client:
            return {'status': 'failed', 'error': 'SNS client not initialized'}
            
        try:
            topic_arn = destination.config.get('topic_arn')
            if not topic_arn:
                return {'status': 'failed', 'error': 'Missing SNS topic ARN'}
                
            message = self._format_sns_message(alert)
            
            response = self.sns_client.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=f"[{alert.severity.value.upper()}] {alert.title}"
            )
            
            return {
                'status': 'sent',
                'message_id': response.get('MessageId')
            }
            
        except ClientError as e:
            return {'status': 'failed', 'error': str(e)}
            
    def _send_webhook(self, alert: Alert, destination: AlertDestination) -> Dict[str, Any]:
        """Send alert via webhook"""
        import requests
        
        webhook_url = destination.config.get('url')
        if not webhook_url:
            return {'status': 'failed', 'error': 'Missing webhook URL'}
            
        try:
            headers = destination.config.get('headers', {})
            payload = {
                'alert_id': alert.id,
                'type': alert.type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'source': alert.source,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata,
                'client_id': alert.client_id,
                'owner_id': alert.owner_id
            }
            
            response = requests.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            
            return {'status': 'sent'}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
            
    def _format_email_body(self, alert: Alert) -> str:
        """Format alert for email body"""
        body = f"""
Alert Details:
==============

Title: {alert.title}
Severity: {alert.severity.value.upper()}
Type: {alert.type.value}
Source: {alert.source}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

"""
        
        if alert.client_id:
            body += f"Client ID: {alert.client_id}\n"
        if alert.owner_id:
            body += f"Owner ID: {alert.owner_id}\n"
        if alert.resource_id:
            body += f"Resource ID: {alert.resource_id}\n"
        if alert.agent_id:
            body += f"Agent ID: {alert.agent_id}\n"
            
        if alert.metadata:
            body += f"\nMetadata:\n{json.dumps(alert.metadata, indent=2)}\n"
            
        return body
        
    def _format_sns_message(self, alert: Alert) -> str:
        """Format alert for SNS message"""
        return json.dumps({
            'alert_id': alert.id,
            'type': alert.type.value,
            'severity': alert.severity.value,
            'title': alert.title,
            'message': alert.message,
            'source': alert.source,
            'timestamp': alert.timestamp.isoformat(),
            'metadata': alert.metadata,
            'client_id': alert.client_id,
            'owner_id': alert.owner_id,
            'resource_id': alert.resource_id,
            'agent_id': alert.agent_id
        }, indent=2)
        
    def _add_to_history(self, alert: Alert):
        """Add alert to history"""
        self.alert_history.append(alert)
        
        # Trim history if it exceeds max size
        if len(self.alert_history) > self.max_history_size:
            self.alert_history = self.alert_history[-self.max_history_size:]
            
    def get_alert_history(self, 
                         severity: Optional[AlertSeverity] = None,
                         alert_type: Optional[AlertType] = None,
                         client_id: Optional[str] = None,
                         hours: Optional[int] = None) -> List[Alert]:
        """
        Get alert history with optional filtering
        
        Args:
            severity: Filter by severity
            alert_type: Filter by alert type
            client_id: Filter by client ID
            hours: Filter by time (last N hours)
            
        Returns:
            List of matching alerts
        """
        filtered_alerts = self.alert_history
        
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
            
        if alert_type:
            filtered_alerts = [a for a in filtered_alerts if a.type == alert_type]
            
        if client_id:
            filtered_alerts = [a for a in filtered_alerts if a.client_id == client_id]
            
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_alerts = [a for a in filtered_alerts if a.timestamp >= cutoff_time]
            
        return filtered_alerts
        
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get alert statistics for the specified time period
        
        Args:
            hours: Time period in hours
            
        Returns:
            Dictionary with alert statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a.timestamp >= cutoff_time]
        
        stats = {
            'total_alerts': len(recent_alerts),
            'by_severity': {},
            'by_type': {},
            'by_client': {},
            'routing_success_rate': 0
        }
        
        # Count by severity
        for severity in AlertSeverity:
            count = len([a for a in recent_alerts if a.severity == severity])
            stats['by_severity'][severity.value] = count
            
        # Count by type
        for alert_type in AlertType:
            count = len([a for a in recent_alerts if a.type == alert_type])
            stats['by_type'][alert_type.value] = count
            
        # Count by client
        client_counts = {}
        for alert in recent_alerts:
            client_id = alert.client_id or 'unknown'
            client_counts[client_id] = client_counts.get(client_id, 0) + 1
        stats['by_client'] = client_counts
        
        return stats
        
    def create_alert(self, 
                    alert_type: AlertType,
                    severity: AlertSeverity,
                    title: str,
                    message: str,
                    source: str,
                    metadata: Optional[Dict[str, Any]] = None,
                    client_id: Optional[str] = None,
                    owner_id: Optional[str] = None,
                    resource_id: Optional[str] = None,
                    agent_id: Optional[str] = None) -> Alert:
        """
        Create and route an alert
        
        Args:
            alert_type: Type of alert
            severity: Alert severity
            title: Alert title
            message: Alert message
            source: Source of the alert
            metadata: Additional metadata
            client_id: Client ID if client-specific
            owner_id: Owner ID if owner-specific
            resource_id: Resource ID if resource-specific
            agent_id: Agent ID if agent-specific
            
        Returns:
            Created Alert object
        """
        alert = Alert(
            id=f"alert_{int(time.time())}_{hash(title) % 10000}",
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata or {},
            client_id=client_id,
            owner_id=owner_id,
            resource_id=resource_id,
            agent_id=agent_id
        )
        
        # Route the alert
        routing_result = self.route_alert(alert)
        self.logger.info(f"Alert {alert.id} routed with result: {routing_result['status']}")
        
        return alert 