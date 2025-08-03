from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

# Persistent models (stored in database)


class Endpoint(SQLModel, table=True):
    __tablename__ = "endpoints"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, description="Human-readable name for the endpoint")
    url: str = Field(max_length=1000, description="URL to monitor")
    check_interval: int = Field(default=300, description="Check interval in seconds")
    is_active: bool = Field(default=True, description="Whether monitoring is enabled")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Expected response configuration
    expected_status_code: Optional[int] = Field(default=200, description="Expected HTTP status code")
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    # Additional metadata
    description: str = Field(default="", max_length=500, description="Optional description")
    tags: List[str] = Field(default=[], sa_column=Column(JSON), description="Tags for grouping endpoints")

    # Relationships
    health_checks: List["HealthCheck"] = Relationship(back_populates="endpoint")


class HealthCheck(SQLModel, table=True):
    __tablename__ = "health_checks"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint_id: int = Field(foreign_key="endpoints.id")
    checked_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Response data
    status_code: Optional[int] = Field(default=None, description="HTTP status code received")
    response_time_ms: Optional[Decimal] = Field(default=None, description="Response time in milliseconds")
    is_successful: bool = Field(default=False, description="Whether the check was successful")

    # Error information
    error_message: Optional[str] = Field(default=None, max_length=1000, description="Error message if check failed")
    error_type: Optional[str] = Field(
        default=None, max_length=100, description="Type of error (timeout, connection, etc.)"
    )

    # Additional metrics
    dns_lookup_time_ms: Optional[Decimal] = Field(default=None, description="DNS lookup time in milliseconds")
    tcp_connect_time_ms: Optional[Decimal] = Field(default=None, description="TCP connection time in milliseconds")
    tls_handshake_time_ms: Optional[Decimal] = Field(default=None, description="TLS handshake time in milliseconds")

    # Response details
    response_size_bytes: Optional[int] = Field(default=None, description="Response size in bytes")
    response_headers: Optional[Dict[str, str]] = Field(
        default=None, sa_column=Column(JSON), description="Response headers"
    )

    # Relationships
    endpoint: Endpoint = Relationship(back_populates="health_checks")


class UptimeMetric(SQLModel, table=True):
    __tablename__ = "uptime_metrics"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint_id: int = Field(foreign_key="endpoints.id", index=True)

    # Time period
    period_start: datetime = Field(index=True, description="Start of the metric period")
    period_end: datetime = Field(index=True, description="End of the metric period")
    period_type: str = Field(max_length=20, description="Type of period (hour, day, week, month)")

    # Uptime statistics
    total_checks: int = Field(default=0, description="Total number of checks in period")
    successful_checks: int = Field(default=0, description="Number of successful checks")
    uptime_percentage: Decimal = Field(default=Decimal("0"), description="Uptime percentage for the period")

    # Response time statistics
    avg_response_time_ms: Optional[Decimal] = Field(default=None, description="Average response time in milliseconds")
    min_response_time_ms: Optional[Decimal] = Field(default=None, description="Minimum response time in milliseconds")
    max_response_time_ms: Optional[Decimal] = Field(default=None, description="Maximum response time in milliseconds")
    p95_response_time_ms: Optional[Decimal] = Field(default=None, description="95th percentile response time")
    p99_response_time_ms: Optional[Decimal] = Field(default=None, description="99th percentile response time")

    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemConfig(SQLModel, table=True):
    __tablename__ = "system_config"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, max_length=100, description="Configuration key")
    value: str = Field(max_length=1000, description="Configuration value")
    value_type: str = Field(max_length=20, default="string", description="Type of the value (string, int, bool, json)")
    description: str = Field(default="", max_length=500, description="Description of the configuration")
    is_system: bool = Field(default=False, description="Whether this is a system configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint_id: int = Field(foreign_key="endpoints.id")

    # Alert details
    alert_type: str = Field(max_length=50, description="Type of alert (down, slow, error)")
    severity: str = Field(max_length=20, default="medium", description="Alert severity (low, medium, high, critical)")
    title: str = Field(max_length=200, description="Alert title")
    message: str = Field(max_length=1000, description="Alert message")

    # Status and timing
    is_active: bool = Field(default=True, description="Whether the alert is still active")
    triggered_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    resolved_at: Optional[datetime] = Field(default=None, description="When the alert was resolved")

    # Trigger conditions
    trigger_data: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON), description="Data that triggered the alert"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)


class EndpointCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    url: str = Field(max_length=1000)
    check_interval: int = Field(default=300, ge=60, le=3600)  # Between 1 minute and 1 hour
    expected_status_code: Optional[int] = Field(default=200, ge=100, le=599)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    description: str = Field(default="", max_length=500)
    tags: List[str] = Field(default=[])


class EndpointUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=200)
    url: Optional[str] = Field(default=None, max_length=1000)
    check_interval: Optional[int] = Field(default=None, ge=60, le=3600)
    expected_status_code: Optional[int] = Field(default=None, ge=100, le=599)
    timeout_seconds: Optional[int] = Field(default=None, ge=1, le=300)
    description: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[List[str]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class HealthCheckResult(SQLModel, table=False):
    endpoint_id: int
    status_code: Optional[int] = Field(default=None)
    response_time_ms: Optional[Decimal] = Field(default=None)
    is_successful: bool
    error_message: Optional[str] = Field(default=None, max_length=1000)
    error_type: Optional[str] = Field(default=None, max_length=100)
    dns_lookup_time_ms: Optional[Decimal] = Field(default=None)
    tcp_connect_time_ms: Optional[Decimal] = Field(default=None)
    tls_handshake_time_ms: Optional[Decimal] = Field(default=None)
    response_size_bytes: Optional[int] = Field(default=None)
    response_headers: Optional[Dict[str, str]] = Field(default=None)


class EndpointStatus(SQLModel, table=False):
    endpoint: Endpoint
    latest_check: Optional[HealthCheck] = Field(default=None)
    uptime_24h: Optional[Decimal] = Field(default=None)
    uptime_7d: Optional[Decimal] = Field(default=None)
    uptime_30d: Optional[Decimal] = Field(default=None)
    avg_response_time_24h: Optional[Decimal] = Field(default=None)
    is_down: bool = Field(default=False)
    consecutive_failures: int = Field(default=0)


class UptimeStats(SQLModel, table=False):
    endpoint_id: int
    period: str  # "24h", "7d", "30d"
    uptime_percentage: Decimal
    total_checks: int
    successful_checks: int
    avg_response_time_ms: Optional[Decimal] = Field(default=None)
    min_response_time_ms: Optional[Decimal] = Field(default=None)
    max_response_time_ms: Optional[Decimal] = Field(default=None)


class SystemConfigUpdate(SQLModel, table=False):
    key: str = Field(max_length=100)
    value: str = Field(max_length=1000)
    value_type: str = Field(default="string", max_length=20)
    description: str = Field(default="", max_length=500)


class AlertCreate(SQLModel, table=False):
    endpoint_id: int
    alert_type: str = Field(max_length=50)
    severity: str = Field(default="medium", max_length=20)
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    trigger_data: Optional[Dict[str, Any]] = Field(default=None)
