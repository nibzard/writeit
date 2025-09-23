"""Security audit and monitoring system for WriteIt.

Provides comprehensive security event logging, suspicious activity detection,
and security monitoring capabilities.
"""

import time
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union
from pathlib import Path
import json
import logging
from collections import defaultdict, deque

from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.errors import SecurityError


class SecurityEventType(Enum):
    """Security event types."""
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    FILE_ACCESS_VIOLATION = "file_access_violation"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    DANGEROUS_OPERATION = "dangerous_operation"
    DATA_INTEGRITY_VIOLATION = "data_integrity_violation"
    WORKSPACE_ISOLATION_VIOLATION = "workspace_isolation_violation"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"
    MALICIOUS_INPUT_DETECTED = "malicious_input_detected"
    SYSTEM_COMPROMISE_INDICATOR = "system_compromise_indicator"


class SecurityEventSeverity(Enum):
    """Security event severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SecurityEvent:
    """Security event record."""
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    message: str
    workspace_name: Optional[WorkspaceName] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    resource_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'workspace_name': str(self.workspace_name) if self.workspace_name else None,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'resource_id': self.resource_id,
            'source_ip': self.source_ip,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp,
            'details': self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityEvent':
        """Create event from dictionary."""
        workspace_name = None
        if data.get('workspace_name'):
            workspace_name = WorkspaceName(data['workspace_name'])
        
        return cls(
            event_type=SecurityEventType(data['event_type']),
            severity=SecurityEventSeverity(data['severity']),
            message=data['message'],
            workspace_name=workspace_name,
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            resource_id=data.get('resource_id'),
            source_ip=data.get('source_ip'),
            user_agent=data.get('user_agent'),
            timestamp=data['timestamp'],
            details=data.get('details', {})
        )


@dataclass
class SuspiciousActivityPattern:
    """Pattern for detecting suspicious activity."""
    name: str
    event_types: Set[SecurityEventType]
    threshold_count: int
    time_window_seconds: float
    severity: SecurityEventSeverity
    description: str
    action: Optional[str] = None  # Action to take when pattern is detected


@dataclass
class SecurityMetrics:
    """Security metrics for monitoring."""
    total_events: int = 0
    events_by_type: Dict[SecurityEventType, int] = field(default_factory=lambda: defaultdict(int))
    events_by_severity: Dict[SecurityEventSeverity, int] = field(default_factory=lambda: defaultdict(int))
    events_by_workspace: Dict[WorkspaceName, int] = field(default_factory=lambda: defaultdict(int))
    suspicious_patterns_detected: int = 0
    last_update: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_events': self.total_events,
            'events_by_type': {k.value: v for k, v in self.events_by_type.items()},
            'events_by_severity': {k.value: v for k, v in self.events_by_severity.items()},
            'events_by_workspace': {str(k): v for k, v in self.events_by_workspace.items()},
            'suspicious_patterns_detected': self.suspicious_patterns_detected,
            'last_update': self.last_update
        }


class SecurityAuditLogger:
    """Security audit logging system."""
    
    def __init__(self, log_file_path: Optional[Path] = None):
        """Initialize security audit logger.
        
        Args:
            log_file_path: Path to security log file. If None, uses default location.
        """
        self.log_file_path = log_file_path or Path.home() / '.writeit' / 'security.log'
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up Python logger for security events
        self.logger = logging.getLogger('writeit.security')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if not already exists
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        # Log to Python logger
        log_level = {
            SecurityEventSeverity.LOW: logging.INFO,
            SecurityEventSeverity.MEDIUM: logging.WARNING,
            SecurityEventSeverity.HIGH: logging.ERROR,
            SecurityEventSeverity.CRITICAL: logging.CRITICAL
        }[event.severity]
        
        self.logger.log(log_level, json.dumps(event.to_dict()))
    
    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[SecurityEventType] = None,
        severity: Optional[SecurityEventSeverity] = None,
        workspace_name: Optional[WorkspaceName] = None
    ) -> List[SecurityEvent]:
        """Get recent security events from log file."""
        events = []
        
        try:
            with open(self.log_file_path, 'r') as f:
                lines = deque(f, maxlen=limit * 2)  # Read more lines to account for filtering
            
            for line in reversed(lines):
                try:
                    # Extract JSON from log line
                    json_start = line.find('{')
                    if json_start == -1:
                        continue
                    
                    event_data = json.loads(line[json_start:])
                    event = SecurityEvent.from_dict(event_data)
                    
                    # Apply filters
                    if event_type and event.event_type != event_type:
                        continue
                    if severity and event.severity != severity:
                        continue
                    if workspace_name and event.workspace_name != workspace_name:
                        continue
                    
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
                        
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        except FileNotFoundError:
            pass  # No log file yet
        
        return events


class SuspiciousActivityDetector:
    """Detects suspicious activity patterns."""
    
    def __init__(self):
        """Initialize suspicious activity detector."""
        self.patterns: List[SuspiciousActivityPattern] = []
        self.event_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.detection_callbacks: List[Callable[[SecurityEvent, SuspiciousActivityPattern], None]] = []
        
        # Set up default patterns
        self._setup_default_patterns()
    
    def _setup_default_patterns(self) -> None:
        """Set up default suspicious activity patterns."""
        self.patterns = [
            SuspiciousActivityPattern(
                name="Rapid Access Denials",
                event_types={SecurityEventType.ACCESS_DENIED, SecurityEventType.AUTHORIZATION_FAILURE},
                threshold_count=10,
                time_window_seconds=60,
                severity=SecurityEventSeverity.HIGH,
                description="Multiple access denials in short time period",
                action="rate_limit"
            ),
            SuspiciousActivityPattern(
                name="Path Traversal Attempts",
                event_types={SecurityEventType.PATH_TRAVERSAL_ATTEMPT},
                threshold_count=3,
                time_window_seconds=300,
                severity=SecurityEventSeverity.CRITICAL,
                description="Multiple path traversal attempts detected",
                action="block_ip"
            ),
            SuspiciousActivityPattern(
                name="Workspace Isolation Violations",
                event_types={SecurityEventType.WORKSPACE_ISOLATION_VIOLATION},
                threshold_count=5,
                time_window_seconds=300,
                severity=SecurityEventSeverity.HIGH,
                description="Multiple workspace isolation violations",
                action="suspend_session"
            ),
            SuspiciousActivityPattern(
                name="Resource Limit Abuse",
                event_types={SecurityEventType.RESOURCE_LIMIT_EXCEEDED, SecurityEventType.RATE_LIMIT_EXCEEDED},
                threshold_count=20,
                time_window_seconds=3600,
                severity=SecurityEventSeverity.MEDIUM,
                description="Repeated resource limit violations",
                action="throttle"
            ),
            SuspiciousActivityPattern(
                name="Malicious Input Pattern",
                event_types={SecurityEventType.MALICIOUS_INPUT_DETECTED},
                threshold_count=1,
                time_window_seconds=1,
                severity=SecurityEventSeverity.CRITICAL,
                description="Malicious input detected",
                action="immediate_block"
            )
        ]
    
    def add_pattern(self, pattern: SuspiciousActivityPattern) -> None:
        """Add a custom suspicious activity pattern."""
        self.patterns.append(pattern)
    
    def add_detection_callback(
        self,
        callback: Callable[[SecurityEvent, SuspiciousActivityPattern], None]
    ) -> None:
        """Add callback for when suspicious activity is detected."""
        self.detection_callbacks.append(callback)
    
    def analyze_event(self, event: SecurityEvent) -> List[SuspiciousActivityPattern]:
        """Analyze event for suspicious patterns.
        
        Args:
            event: Security event to analyze
            
        Returns:
            List of triggered patterns
        """
        triggered_patterns = []
        
        # Create key for event grouping (by user, IP, or session)
        event_key = self._get_event_key(event)
        
        # Add event to history
        self.event_history[event_key].append(event)
        
        # Check each pattern
        for pattern in self.patterns:
            if event.event_type in pattern.event_types:
                if self._check_pattern_threshold(pattern, event_key):
                    triggered_patterns.append(pattern)
                    
                    # Create suspicious activity event
                    suspicious_event = SecurityEvent(
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        severity=pattern.severity,
                        message=f"Suspicious pattern detected: {pattern.description}",
                        workspace_name=event.workspace_name,
                        user_id=event.user_id,
                        session_id=event.session_id,
                        resource_id=event.resource_id,
                        source_ip=event.source_ip,
                        user_agent=event.user_agent,
                        details={
                            'pattern_name': pattern.name,
                            'pattern_description': pattern.description,
                            'threshold_count': pattern.threshold_count,
                            'time_window_seconds': pattern.time_window_seconds,
                            'suggested_action': pattern.action,
                            'triggering_event': event.to_dict()
                        }
                    )
                    
                    # Notify callbacks
                    for callback in self.detection_callbacks:
                        try:
                            callback(suspicious_event, pattern)
                        except Exception:
                            pass  # Don't let callback errors break detection
        
        return triggered_patterns
    
    def _get_event_key(self, event: SecurityEvent) -> str:
        """Get grouping key for event."""
        # Group by user_id if available, otherwise by source IP or session
        if event.user_id:
            return f"user:{event.user_id}"
        elif event.source_ip:
            return f"ip:{event.source_ip}"
        elif event.session_id:
            return f"session:{event.session_id}"
        else:
            return "unknown"
    
    def _check_pattern_threshold(
        self,
        pattern: SuspiciousActivityPattern,
        event_key: str
    ) -> bool:
        """Check if pattern threshold is exceeded."""
        current_time = time.time()
        cutoff_time = current_time - pattern.time_window_seconds
        
        # Count events of pattern types within time window
        relevant_events = [
            event for event in self.event_history[event_key]
            if (event.event_type in pattern.event_types and 
                event.timestamp >= cutoff_time)
        ]
        
        return len(relevant_events) >= pattern.threshold_count


class SecurityMonitor:
    """Central security monitoring system."""
    
    def __init__(self, log_file_path: Optional[Path] = None):
        """Initialize security monitor.
        
        Args:
            log_file_path: Path to security log file
        """
        self.audit_logger = SecurityAuditLogger(log_file_path)
        self.activity_detector = SuspiciousActivityDetector()
        self.metrics = SecurityMetrics()
        self._lock = asyncio.Lock()
        
        # Set up detection callback
        self.activity_detector.add_detection_callback(self._handle_suspicious_activity)
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        message: str,
        severity: SecurityEventSeverity = SecurityEventSeverity.MEDIUM,
        workspace_name: Optional[WorkspaceName] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a security event.
        
        Args:
            event_type: Type of security event
            message: Event message
            severity: Event severity
            workspace_name: Associated workspace
            user_id: User identifier
            session_id: Session identifier
            resource_id: Resource identifier
            source_ip: Source IP address
            user_agent: User agent string
            details: Additional event details
        """
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            workspace_name=workspace_name,
            user_id=user_id,
            session_id=session_id,
            resource_id=resource_id,
            source_ip=source_ip,
            user_agent=user_agent,
            details=details or {}
        )
        
        async with self._lock:
            # Log the event
            self.audit_logger.log_event(event)
            
            # Update metrics
            self._update_metrics(event)
            
            # Analyze for suspicious activity
            triggered_patterns = self.activity_detector.analyze_event(event)
            if triggered_patterns:
                self.metrics.suspicious_patterns_detected += len(triggered_patterns)
    
    def _update_metrics(self, event: SecurityEvent) -> None:
        """Update security metrics."""
        self.metrics.total_events += 1
        self.metrics.events_by_type[event.event_type] += 1
        self.metrics.events_by_severity[event.severity] += 1
        
        if event.workspace_name:
            self.metrics.events_by_workspace[event.workspace_name] += 1
        
        self.metrics.last_update = time.time()
    
    def _handle_suspicious_activity(
        self,
        event: SecurityEvent,
        pattern: SuspiciousActivityPattern
    ) -> None:
        """Handle detected suspicious activity."""
        # Log the suspicious activity event
        self.audit_logger.log_event(event)
        
        # In a real implementation, this could trigger:
        # - Rate limiting
        # - IP blocking
        # - Session suspension
        # - Admin notifications
        # - Automated response actions
    
    async def get_security_metrics(self) -> SecurityMetrics:
        """Get current security metrics."""
        async with self._lock:
            return self.metrics
    
    async def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[SecurityEventType] = None,
        severity: Optional[SecurityEventSeverity] = None,
        workspace_name: Optional[WorkspaceName] = None
    ) -> List[SecurityEvent]:
        """Get recent security events."""
        return self.audit_logger.get_recent_events(limit, event_type, severity, workspace_name)
    
    async def check_workspace_security_health(
        self,
        workspace_name: WorkspaceName,
        time_window_hours: float = 24
    ) -> Dict[str, Any]:
        """Check security health for a specific workspace."""
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        # Get recent events for workspace
        events = await self.get_recent_events(
            limit=1000,
            workspace_name=workspace_name
        )
        
        # Filter by time window
        recent_events = [e for e in events if e.timestamp >= cutoff_time]
        
        # Calculate metrics
        total_events = len(recent_events)
        events_by_severity = defaultdict(int)
        events_by_type = defaultdict(int)
        
        for event in recent_events:
            events_by_severity[event.severity] += 1
            events_by_type[event.event_type] += 1
        
        # Calculate security score (0-100)
        security_score = self._calculate_security_score(events_by_severity, total_events)
        
        return {
            'workspace_name': str(workspace_name),
            'time_window_hours': time_window_hours,
            'total_events': total_events,
            'events_by_severity': {k.value: v for k, v in events_by_severity.items()},
            'events_by_type': {k.value: v for k, v in events_by_type.items()},
            'security_score': security_score,
            'security_status': self._get_security_status(security_score),
            'recommendations': self._get_security_recommendations(events_by_type, events_by_severity)
        }
    
    def _calculate_security_score(
        self,
        events_by_severity: Dict[SecurityEventSeverity, int],
        total_events: int
    ) -> float:
        """Calculate security score for workspace."""
        if total_events == 0:
            return 100.0
        
        # Weight events by severity
        severity_weights = {
            SecurityEventSeverity.LOW: 1,
            SecurityEventSeverity.MEDIUM: 3,
            SecurityEventSeverity.HIGH: 7,
            SecurityEventSeverity.CRITICAL: 15
        }
        
        weighted_score = sum(
            count * severity_weights[severity]
            for severity, count in events_by_severity.items()
        )
        
        # Normalize to 0-100 scale
        max_possible_score = total_events * severity_weights[SecurityEventSeverity.CRITICAL]
        if max_possible_score == 0:
            return 100.0
        
        score = 100.0 - (weighted_score / max_possible_score * 100.0)
        return max(0.0, min(100.0, score))
    
    def _get_security_status(self, score: float) -> str:
        """Get security status based on score."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 50:
            return "FAIR"
        elif score >= 25:
            return "POOR"
        else:
            return "CRITICAL"
    
    def _get_security_recommendations(
        self,
        events_by_type: Dict[SecurityEventType, int],
        events_by_severity: Dict[SecurityEventSeverity, int]
    ) -> List[str]:
        """Get security recommendations based on events."""
        recommendations = []
        
        if events_by_type.get(SecurityEventType.ACCESS_DENIED, 0) > 10:
            recommendations.append("Review access permissions and user roles")
        
        if events_by_type.get(SecurityEventType.PATH_TRAVERSAL_ATTEMPT, 0) > 0:
            recommendations.append("Implement stricter input validation and path sanitization")
        
        if events_by_severity.get(SecurityEventSeverity.CRITICAL, 0) > 0:
            recommendations.append("Investigate critical security events immediately")
        
        if events_by_type.get(SecurityEventType.RATE_LIMIT_EXCEEDED, 0) > 20:
            recommendations.append("Consider adjusting rate limits or investigating potential abuse")
        
        return recommendations


# Global security monitor instance
_security_monitor: Optional[SecurityMonitor] = None


def get_security_monitor() -> SecurityMonitor:
    """Get or create the global security monitor."""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityMonitor()
    return _security_monitor


async def log_security_event(
    event_type: SecurityEventType,
    message: str,
    severity: SecurityEventSeverity = SecurityEventSeverity.MEDIUM,
    **kwargs
) -> None:
    """Convenience function to log security events."""
    monitor = get_security_monitor()
    await monitor.log_security_event(event_type, message, severity, **kwargs)