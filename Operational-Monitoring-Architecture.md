# Operational Monitoring & Alerting Architecture: DevOS

## Executive Summary

This document defines a comprehensive operational monitoring and alerting architecture for DevOS, providing real-time visibility into system performance, user experience, security events, and cost optimization. The architecture integrates multiple monitoring tools and implements proactive alerting to ensure high availability and optimal performance.

## 1. Monitoring Architecture Overview

### 1.1 Multi-Layered Monitoring Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                  User Experience Layer                      │
├─────────────────────────────────────────────────────────────┤
│   Response Time  │   Success Rate   │   User Satisfaction  │
│  ┌─────────────┐  │  ┌─────────────┐ │  ┌─────────────────┐ │
│  │ Command     │  │  │ API Success │ │  │ NPS Tracking    │ │
│  │ Latency     │  │  │ Rate        │ │  │ Feature Usage   │ │
│  │ 95th %ile   │  │  │ Error Rate  │ │  │ Satisfaction    │ │
│  └─────────────┘  │  └─────────────┘ │  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Application Performance Layer                │
├─────────────────────────────────────────────────────────────┤
│  Service Health   │  Memory Agent    │  LLM Performance    │
│  ┌─────────────┐  │  ┌─────────────┐ │  ┌─────────────────┐ │
│  │ CPU Usage   │  │  │ Vector DB   │ │  │ Token Usage     │ │
│  │ Memory Use  │  │  │ Query Time  │ │  │ Model Latency   │ │
│  │ Disk I/O    │  │  │ Index Size  │ │  │ Cost per Query  │ │
│  │ Network     │  │  │ Embedding   │ │  │ Rate Limits     │ │
│  └─────────────┘  │  └─────────────┘ │  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                         │
├─────────────────────────────────────────────────────────────┤
│  AWS Resources   │  Network Layer   │  Security Events     │
│  ┌─────────────┐  │  ┌─────────────┐ │  ┌─────────────────┐ │
│  │ EC2 Health  │  │  │ VPC Flow    │ │  │ Auth Failures   │ │
│  │ EBS IOPS    │  │  │ Load Bal.   │ │  │ Unauthorized    │ │
│  │ RDS Conn.   │  │  │ CloudFront  │ │  │ Access          │ │
│  │ S3 Latency  │  │  │ DNS Res.    │ │  │ Data Anomalies  │ │
│  └─────────────┘  │  └─────────────┘ │  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Business Metrics Layer                    │
├─────────────────────────────────────────────────────────────┤
│  Cost Tracking   │  Usage Analytics │  Compliance Metrics │
│  ┌─────────────┐  │  ┌─────────────┐ │  ┌─────────────────┐ │
│  │ LLM Costs   │  │  │ Active Users│ │  │ Audit Logs     │ │
│  │ Infra Costs │  │  │ Commands/Hr │ │  │ Data Retention │ │
│  │ Cost/User   │  │  │ Feature Use │ │  │ Privacy Events │ │
│  └─────────────┘  │  └─────────────┘ │  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Monitoring Data Flow

```
[DevOS Services] → [Metrics Collectors] → [Data Stores] → [Visualization/Alerting]
        │                    │                 │                    │
        ├─ Application       ├─ Prometheus     ├─ CloudWatch       ├─ Grafana
        │  Metrics           ├─ CloudWatch     ├─ New Relic        ├─ New Relic UI
        │                    │  Agent          ├─ Splunk           ├─ Splunk Dashboards
        ├─ System Logs       ├─ Fluentd        ├─ Elasticsearch    ├─ Custom Dashboards
        │                    ├─ Vector         │                   │
        ├─ Security Events   ├─ SIEM Agents    ├─ SIEM Platform    ├─ Alert Manager
        │                    │                 │                   ├─ PagerDuty
        └─ Business Events   └─ Custom         └─ Time Series DB   └─ Slack/Teams
                                Collectors
```

## 2. Metrics and Data Collection

### 2.1 Core System Metrics

```python
class DevOSMetricsCollector:
    """Comprehensive metrics collection for DevOS components"""
    
    def __init__(self):
        self.prometheus_client = PrometheusClient()
        self.cloudwatch_client = boto3.client('cloudwatch')
        self.newrelic_client = NewRelicClient()
        
        # Define metric categories
        self.metric_definitions = {
            "system_performance": [
                "cpu_usage_percent",
                "memory_usage_percent", 
                "disk_io_read_bytes_per_sec",
                "disk_io_write_bytes_per_sec",
                "network_bytes_in_per_sec",
                "network_bytes_out_per_sec"
            ],
            "application_performance": [
                "command_processing_time_ms",
                "llm_inference_time_ms", 
                "memory_search_time_ms",
                "api_response_time_ms",
                "concurrent_users",
                "commands_per_minute"
            ],
            "llm_metrics": [
                "llm_tokens_consumed",
                "llm_cost_per_request",
                "llm_success_rate",
                "llm_model_latency_ms",
                "llm_rate_limit_hits",
                "llm_error_rate"
            ],
            "memory_agent_metrics": [
                "vector_db_query_time_ms",
                "vector_db_size_mb",
                "embedding_generation_time_ms",
                "memory_items_stored_per_hour",
                "memory_search_accuracy",
                "memory_cache_hit_rate"
            ],
            "business_metrics": [
                "active_users_daily",
                "feature_usage_by_type",
                "user_satisfaction_score",
                "productivity_gain_percent",
                "cost_per_user_monthly"
            ]
        }
    
    async def collect_system_metrics(self):
        """Collect system-level performance metrics"""
        
        system_stats = psutil.cpu_percent(), psutil.virtual_memory().percent
        
        metrics = {
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg()[0],
            "open_files": len(psutil.Process().open_files()),
            "network_connections": len(psutil.net_connections())
        }
        
        # Send to multiple monitoring systems
        await self.send_to_prometheus(metrics, "system")
        await self.send_to_cloudwatch(metrics, "DevOS/System")
        await self.send_to_newrelic(metrics, "system_performance")
        
        return metrics
    
    async def collect_application_metrics(self, component: str):
        """Collect application-specific metrics"""
        
        if component == "llm_os_daemon":
            metrics = await self.collect_daemon_metrics()
        elif component == "memory_agent":
            metrics = await self.collect_memory_metrics()
        elif component == "context_engine":
            metrics = await self.collect_context_metrics()
        else:
            metrics = {}
        
        await self.send_metrics_to_monitoring_systems(metrics, component)
        return metrics
    
    async def collect_daemon_metrics(self):
        """Collect metrics from the main DevOS daemon"""
        
        return {
            "active_sessions": self.get_active_session_count(),
            "commands_processed_total": self.get_command_counter(),
            "commands_in_queue": self.get_queue_size(),
            "average_response_time_ms": self.get_avg_response_time(),
            "error_rate_percent": self.get_error_rate(),
            "approval_requests_pending": self.get_pending_approvals()
        }
    
    async def collect_memory_metrics(self):
        """Collect metrics from the memory agent"""
        
        return {
            "vector_db_size_mb": self.get_vector_db_size(),
            "total_memories_stored": self.get_memory_count(),
            "search_queries_per_minute": self.get_search_rate(),
            "average_search_time_ms": self.get_avg_search_time(),
            "embedding_cache_hit_rate": self.get_cache_hit_rate(),
            "memory_ingestion_rate": self.get_ingestion_rate()
        }
    
    async def collect_llm_metrics(self):
        """Collect LLM usage and performance metrics"""
        
        return {
            "bedrock_requests_per_minute": self.get_bedrock_request_rate(),
            "total_tokens_consumed": self.get_token_usage(),
            "average_llm_latency_ms": self.get_llm_latency(),
            "llm_cost_current_hour": self.calculate_hourly_llm_cost(),
            "model_usage_distribution": self.get_model_usage_stats(),
            "llm_error_rate": self.get_llm_error_rate()
        }

class CustomMetricsEmitter:
    """Custom business metrics specific to DevOS"""
    
    def __init__(self):
        self.business_metrics = {}
        
    async def emit_productivity_metrics(self, user_id: str, session_data: dict):
        """Track developer productivity improvements"""
        
        productivity_metrics = {
            "tasks_completed_per_hour": session_data.get("tasks_completed", 0),
            "time_saved_minutes": self.calculate_time_saved(session_data),
            "commands_automated": session_data.get("automated_commands", 0),
            "context_switches_reduced": self.calculate_context_reduction(session_data),
            "error_resolution_time_minutes": session_data.get("debug_time", 0)
        }
        
        # Emit to monitoring systems
        await self.emit_to_all_systems(productivity_metrics, "productivity")
    
    async def emit_cost_metrics(self):
        """Track cost metrics for optimization"""
        
        cost_metrics = {
            "llm_cost_per_user_daily": await self.calculate_daily_llm_cost_per_user(),
            "infrastructure_cost_daily": await self.get_infrastructure_costs(),
            "cost_efficiency_ratio": await self.calculate_cost_efficiency(),
            "budget_utilization_percent": await self.get_budget_utilization()
        }
        
        await self.emit_to_all_systems(cost_metrics, "cost_tracking")
```

### 2.2 Log Collection and Processing

```python
class LogCollectionPipeline:
    """Centralized log collection and processing"""
    
    def __init__(self):
        self.log_processors = {
            "security": SecurityLogProcessor(),
            "application": ApplicationLogProcessor(), 
            "performance": PerformanceLogProcessor(),
            "audit": AuditLogProcessor()
        }
        
        # Configure log shippers
        self.fluentd_config = self.setup_fluentd()
        self.vector_config = self.setup_vector()
        
    def setup_fluentd(self):
        """Configure Fluentd for log collection"""
        
        fluentd_config = """
<source>
  @type tail
  @label @devos
  path /var/log/devos/*.log
  pos_file /var/log/fluentd/devos.log.pos
  tag devos.*
  format json
  time_key timestamp
  time_format %Y-%m-%dT%H:%M:%S.%NZ
</source>

<label @devos>
  <match devos.security>
    @type copy
    <store>
      @type splunk
      host "#{ENV['SPLUNK_HOST']}"
      port 8088
      token "#{ENV['SPLUNK_TOKEN']}"
      index devos_security
    </store>
    <store>
      @type cloudwatch_logs
      log_group_name /aws/devos/security
      log_stream_name security
      auto_create_stream true
    </store>
  </match>
  
  <match devos.application>
    @type copy
    <store>
      @type newrelic
      license_key "#{ENV['NEWRELIC_LICENSE_KEY']}"
      base_uri https://log-api.newrelic.com/log/v1
    </store>
    <store>
      @type elasticsearch
      host "#{ENV['ELASTICSEARCH_HOST']}"
      port 9200
      index_name devos-application
    </store>
  </match>
  
  <match devos.**>
    @type cloudwatch_logs
    log_group_name /aws/devos/general
    log_stream_name "#{ENV['HOSTNAME']}"
    auto_create_stream true
  </match>
</label>
"""
        return fluentd_config
    
    def setup_vector(self):
        """Configure Vector for high-performance log processing"""
        
        vector_config = """
[sources.devos_logs]
type = "file"
include = ["/var/log/devos/*.log"]
start_at_beginning = true

[transforms.parse_devos_logs]
type = "json_parser"
inputs = ["devos_logs"]

[transforms.enrich_logs]
type = "remap"
inputs = ["parse_devos_logs"]
source = '''
  .hostname = get_hostname!()
  .environment = get_env_var!("ENVIRONMENT")
  .service_version = get_env_var!("SERVICE_VERSION")
  
  # Add severity levels
  if exists(.level) {
    .severity = if .level == "ERROR" { 3 } 
                else if .level == "WARN" { 2 }
                else if .level == "INFO" { 1 }
                else { 0 }
  }
  
  # Extract user context
  if exists(.user_id) {
    .user_context = {
      "user_id": .user_id,
      "session_id": .session_id,
      "organization": get_env_var("ORGANIZATION")
    }
  }
'''

[sinks.cloudwatch]
type = "aws_cloudwatch_logs"
inputs = ["enrich_logs"]
group_name = "/aws/devos/application"
stream_name = "{{ hostname }}"
region = "us-east-1"

[sinks.splunk]
type = "splunk_hec_logs"
inputs = ["enrich_logs"]
endpoint = "https://splunk.company.com:8088"
token = "${SPLUNK_TOKEN}"
index = "devos"

[sinks.newrelic]
type = "new_relic_logs"
inputs = ["enrich_logs"]
license_key = "${NEWRELIC_LICENSE_KEY}"
region = "us"
"""
        return vector_config

class StructuredLogging:
    """Structured logging implementation for DevOS"""
    
    def __init__(self):
        self.logger = structlog.get_logger()
        
        # Configure structured logging
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.ConsoleRenderer() if self.is_development() else structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def log_command_execution(self, command_data: dict):
        """Log command execution with structured data"""
        
        self.logger.info(
            "command_executed",
            command_id=command_data["id"],
            user_id=command_data["user_id"],
            command_type=command_data["type"],
            execution_time_ms=command_data["execution_time"],
            model_used=command_data.get("model"),
            tokens_consumed=command_data.get("tokens", 0),
            cost_usd=command_data.get("cost", 0.0),
            success=command_data["success"],
            error_message=command_data.get("error"),
            context_size=len(command_data.get("context", {}))
        )
    
    def log_security_event(self, event_data: dict):
        """Log security events with proper categorization"""
        
        self.logger.warning(
            "security_event",
            event_type=event_data["type"],
            user_id=event_data.get("user_id"),
            source_ip=event_data.get("ip_address"),
            user_agent=event_data.get("user_agent"),
            severity=event_data["severity"],
            details=event_data["details"],
            action_taken=event_data.get("action_taken"),
            requires_investigation=event_data.get("requires_investigation", False)
        )
```

## 3. Monitoring Tools Integration

### 3.1 New Relic Integration

```python
class NewRelicIntegration:
    """New Relic integration for application performance monitoring"""
    
    def __init__(self):
        self.newrelic_client = newrelic.agent
        self.insights_client = InsightsClient()
        
    def setup_custom_metrics(self):
        """Set up custom metrics for DevOS in New Relic"""
        
        custom_metrics = {
            "DevOS/Commands/Processed": "count",
            "DevOS/LLM/TokensConsumed": "gauge",
            "DevOS/Memory/SearchTime": "histogram",
            "DevOS/Users/Active": "gauge",
            "DevOS/Cost/PerHour": "gauge"
        }
        
        for metric_name, metric_type in custom_metrics.items():
            self.register_custom_metric(metric_name, metric_type)
    
    @newrelic.agent.function_trace()
    def track_command_execution(self, command_function):
        """Decorator to track command execution in New Relic"""
        
        def wrapper(*args, **kwargs):
            with newrelic.agent.FunctionTrace(name="command_execution"):
                # Add custom attributes
                newrelic.agent.add_custom_attribute("command_type", kwargs.get("command_type"))
                newrelic.agent.add_custom_attribute("user_id", kwargs.get("user_id"))
                
                # Execute command
                result = command_function(*args, **kwargs)
                
                # Record custom metrics
                self.record_custom_metric("DevOS/Commands/Processed", 1)
                if result.get("tokens_used"):
                    self.record_custom_metric("DevOS/LLM/TokensConsumed", result["tokens_used"])
                
                return result
        
        return wrapper
    
    def create_custom_dashboards(self):
        """Create New Relic dashboards for DevOS monitoring"""
        
        dashboard_config = {
            "name": "DevOS Operations Dashboard",
            "description": "Comprehensive monitoring for DevOS platform",
            "pages": [
                {
                    "name": "System Overview",
                    "widgets": [
                        {
                            "title": "Command Processing Rate",
                            "visualization": {"id": "viz.line"},
                            "rawConfiguration": {
                                "nrqlQueries": [
                                    {
                                        "query": "SELECT rate(count(*), 1 minute) FROM Custom WHERE name = 'DevOS/Commands/Processed' TIMESERIES",
                                        "accountId": self.account_id
                                    }
                                ]
                            }
                        },
                        {
                            "title": "LLM Token Usage",
                            "visualization": {"id": "viz.area"},
                            "rawConfiguration": {
                                "nrqlQueries": [
                                    {
                                        "query": "SELECT sum(value) FROM Custom WHERE name = 'DevOS/LLM/TokensConsumed' TIMESERIES",
                                        "accountId": self.account_id
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "name": "Performance Metrics",
                    "widgets": [
                        {
                            "title": "Response Time Distribution",
                            "visualization": {"id": "viz.histogram"},
                            "rawConfiguration": {
                                "nrqlQueries": [
                                    {
                                        "query": "SELECT histogram(duration) FROM Transaction WHERE appName = 'DevOS' FACET name",
                                        "accountId": self.account_id
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        
        return self.create_dashboard(dashboard_config)

class NewRelicAlerting:
    """New Relic alerting configuration"""
    
    def __init__(self):
        self.alerts_client = AlertsClient()
        
    def setup_alert_policies(self):
        """Configure alert policies for DevOS"""
        
        policies = [
            {
                "name": "DevOS Critical Alerts",
                "incident_preference": "PER_CONDITION_AND_TARGET",
                "conditions": [
                    {
                        "name": "High Command Failure Rate",
                        "type": "NRQL",
                        "query": "SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'DevOS'",
                        "threshold": {"critical": 5.0, "warning": 2.0},
                        "operator": "above"
                    },
                    {
                        "name": "LLM Service Unavailable",
                        "type": "NRQL", 
                        "query": "SELECT count(*) FROM Transaction WHERE appName = 'DevOS' AND name = 'LLM/Request' AND error IS true",
                        "threshold": {"critical": 10},
                        "operator": "above"
                    },
                    {
                        "name": "Memory Agent High Latency",
                        "type": "NRQL",
                        "query": "SELECT average(duration) FROM Custom WHERE name = 'DevOS/Memory/SearchTime'",
                        "threshold": {"critical": 5000, "warning": 2000},
                        "operator": "above"
                    }
                ]
            },
            {
                "name": "DevOS Performance Alerts",
                "incident_preference": "PER_CONDITION",
                "conditions": [
                    {
                        "name": "High Resource Usage",
                        "type": "NRQL",
                        "query": "SELECT average(cpuPercent) FROM SystemSample WHERE hostname LIKE '%devos%'",
                        "threshold": {"critical": 90.0, "warning": 80.0},
                        "operator": "above"
                    }
                ]
            }
        ]
        
        for policy in policies:
            self.create_alert_policy(policy)
```

### 3.2 Splunk Integration

```python
class SplunkIntegration:
    """Splunk integration for log analysis and security monitoring"""
    
    def __init__(self):
        self.splunk_client = SplunkClient()
        self.hec_client = SplunkHECClient()
        
    def setup_indexes_and_sourcetypes(self):
        """Configure Splunk indexes and sourcetypes for DevOS"""
        
        indexes = [
            {
                "name": "devos_application",
                "maxDataSize": "100GB",
                "maxHotBuckets": 10,
                "maxWarmDBCount": 300
            },
            {
                "name": "devos_security",
                "maxDataSize": "500GB", 
                "maxHotBuckets": 20,
                "maxWarmDBCount": 500
            },
            {
                "name": "devos_performance",
                "maxDataSize": "50GB",
                "maxHotBuckets": 5,
                "maxWarmDBCount": 200
            }
        ]
        
        sourcetypes = [
            {
                "name": "devos:application",
                "category": "Application",
                "description": "DevOS application logs"
            },
            {
                "name": "devos:security", 
                "category": "Security",
                "description": "DevOS security events"
            },
            {
                "name": "devos:memory_agent",
                "category": "Application",
                "description": "Memory agent operations"
            }
        ]
        
        for index in indexes:
            self.create_index(index)
            
        for sourcetype in sourcetypes:
            self.create_sourcetype(sourcetype)
    
    def create_security_dashboards(self):
        """Create security monitoring dashboards in Splunk"""
        
        security_dashboard = {
            "name": "DevOS Security Monitoring",
            "panels": [
                {
                    "title": "Authentication Events",
                    "search": '''
                        index=devos_security sourcetype=devos:security event_type=authentication
                        | timechart span=5m count by result
                        | eval failed=if(result="failed", count, 0)
                        | eval successful=if(result="success", count, 0)
                    ''',
                    "visualization": "line_chart"
                },
                {
                    "title": "Suspicious User Activity",
                    "search": '''
                        index=devos_security sourcetype=devos:security
                        | stats count by user_id, source_ip, event_type
                        | where count > 100
                        | sort -count
                    ''',
                    "visualization": "table"
                },
                {
                    "title": "PII Detection Events",
                    "search": '''
                        index=devos_application sourcetype=devos:application pii_detected=true
                        | timechart span=1h count by pii_type
                    ''',
                    "visualization": "column_chart"
                }
            ]
        }
        
        return self.create_dashboard(security_dashboard)
    
    def setup_security_alerts(self):
        """Configure security alerts in Splunk"""
        
        security_alerts = [
            {
                "name": "Multiple Failed Logins",
                "search": '''
                    index=devos_security sourcetype=devos:security event_type=authentication result=failed
                    | stats count by user_id, source_ip
                    | where count > 5
                ''',
                "trigger_conditions": {
                    "schedule": "*/5 * * * *",  # Every 5 minutes
                    "threshold": 1
                },
                "actions": [
                    {"type": "email", "recipients": ["security@company.com"]},
                    {"type": "webhook", "url": "https://hooks.slack.com/security-alerts"}
                ]
            },
            {
                "name": "Unusual LLM Usage Pattern",
                "search": '''
                    index=devos_application sourcetype=devos:application llm_tokens_consumed > 10000
                    | stats sum(llm_tokens_consumed) as total_tokens by user_id
                    | where total_tokens > 100000
                ''',
                "trigger_conditions": {
                    "schedule": "0 */1 * * *",  # Every hour
                    "threshold": 1
                },
                "actions": [
                    {"type": "email", "recipients": ["ops@company.com"]},
                    {"type": "create_incident", "service": "devos"}
                ]
            }
        ]
        
        for alert in security_alerts:
            self.create_saved_search_alert(alert)

class SplunkDataModels:
    """Splunk data models for DevOS analytics"""
    
    def create_devos_data_model(self):
        """Create comprehensive data model for DevOS analytics"""
        
        data_model = {
            "name": "DevOS_Operations",
            "description": "Data model for DevOS operational analytics",
            "objects": [
                {
                    "name": "Commands",
                    "description": "User commands and their execution",
                    "search": "index=devos_application sourcetype=devos:application event=command_executed",
                    "fields": [
                        {"name": "command_id", "type": "string"},
                        {"name": "user_id", "type": "string"},
                        {"name": "command_type", "type": "string"},
                        {"name": "execution_time_ms", "type": "number"},
                        {"name": "success", "type": "boolean"},
                        {"name": "model_used", "type": "string"},
                        {"name": "tokens_consumed", "type": "number"},
                        {"name": "cost_usd", "type": "number"}
                    ]
                },
                {
                    "name": "Memory_Operations",
                    "description": "Memory agent operations and performance",
                    "search": "index=devos_application sourcetype=devos:memory_agent",
                    "fields": [
                        {"name": "operation_type", "type": "string"},
                        {"name": "search_time_ms", "type": "number"},
                        {"name": "results_count", "type": "number"},
                        {"name": "memory_type", "type": "string"},
                        {"name": "user_id", "type": "string"}
                    ]
                }
            ]
        }
        
        return self.create_data_model(data_model)
```

### 3.3 CloudWatch and Grafana Integration

```python
class CloudWatchMetrics:
    """CloudWatch metrics and alarms for DevOS"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        
    def setup_custom_metrics(self):
        """Set up custom CloudWatch metrics for DevOS"""
        
        metrics_config = {
            "DevOS/Application": [
                "CommandsProcessed",
                "ResponseTime", 
                "ErrorRate",
                "ActiveUsers"
            ],
            "DevOS/LLM": [
                "TokensConsumed",
                "RequestLatency",
                "CostPerHour",
                "ModelUsageDistribution"
            ],
            "DevOS/Memory": [
                "SearchLatency",
                "DatabaseSize",
                "CacheHitRate",
                "IngestionRate"
            ]
        }
        
        for namespace, metric_names in metrics_config.items():
            for metric_name in metric_names:
                self.register_custom_metric(namespace, metric_name)
    
    def create_cloudwatch_alarms(self):
        """Create CloudWatch alarms for critical DevOS metrics"""
        
        alarms = [
            {
                "AlarmName": "DevOS-High-Error-Rate",
                "MetricName": "ErrorRate",
                "Namespace": "DevOS/Application",
                "Statistic": "Average",
                "Threshold": 5.0,
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:123456789012:devos-critical-alerts"
                ]
            },
            {
                "AlarmName": "DevOS-LLM-High-Cost",
                "MetricName": "CostPerHour", 
                "Namespace": "DevOS/LLM",
                "Statistic": "Sum",
                "Threshold": 100.0,
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 1
            },
            {
                "AlarmName": "DevOS-Memory-High-Latency",
                "MetricName": "SearchLatency",
                "Namespace": "DevOS/Memory",
                "Statistic": "Average", 
                "Threshold": 2000.0,
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 3
            }
        ]
        
        for alarm_config in alarms:
            self.cloudwatch.put_metric_alarm(**alarm_config)

class GrafanaIntegration:
    """Grafana dashboard configuration for DevOS"""
    
    def __init__(self):
        self.grafana_client = GrafanaClient()
        
    def create_operational_dashboard(self):
        """Create comprehensive operational dashboard in Grafana"""
        
        dashboard_config = {
            "dashboard": {
                "title": "DevOS Operational Dashboard",
                "tags": ["devos", "operations"],
                "timezone": "UTC",
                "panels": [
                    {
                        "title": "System Performance Overview",
                        "type": "stat",
                        "targets": [
                            {
                                "datasource": "CloudWatch",
                                "namespace": "DevOS/Application",
                                "metricName": "ResponseTime",
                                "statistic": "Average"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "title": "Command Processing Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "datasource": "Prometheus",
                                "expr": "rate(devos_commands_total[5m])",
                                "legendFormat": "Commands/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "title": "LLM Token Usage",
                        "type": "graph",
                        "targets": [
                            {
                                "datasource": "CloudWatch",
                                "namespace": "DevOS/LLM",
                                "metricName": "TokensConsumed",
                                "statistic": "Sum"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                    },
                    {
                        "title": "Error Rate by Service",
                        "type": "heatmap",
                        "targets": [
                            {
                                "datasource": "Prometheus",
                                "expr": "rate(devos_errors_total[5m]) by (service)"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    {
                        "title": "Cost Tracking",
                        "type": "singlestat",
                        "targets": [
                            {
                                "datasource": "CloudWatch",
                                "namespace": "DevOS/LLM",
                                "metricName": "CostPerHour",
                                "statistic": "Sum"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "30s"
            }
        }
        
        return self.grafana_client.create_dashboard(dashboard_config)
    
    def create_memory_agent_dashboard(self):
        """Create specialized dashboard for memory agent monitoring"""
        
        memory_dashboard = {
            "dashboard": {
                "title": "DevOS Memory Agent Performance",
                "panels": [
                    {
                        "title": "Vector Database Size Growth",
                        "type": "graph",
                        "targets": [
                            {
                                "datasource": "Prometheus",
                                "expr": "devos_memory_db_size_bytes",
                                "legendFormat": "DB Size (bytes)"
                            }
                        ]
                    },
                    {
                        "title": "Search Performance Distribution",
                        "type": "histogram",
                        "targets": [
                            {
                                "datasource": "Prometheus", 
                                "expr": "histogram_quantile(0.95, devos_memory_search_duration_seconds_bucket)",
                                "legendFormat": "95th percentile"
                            }
                        ]
                    },
                    {
                        "title": "Memory Ingestion Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "datasource": "Prometheus",
                                "expr": "rate(devos_memory_items_stored_total[5m])",
                                "legendFormat": "Items/sec"
                            }
                        ]
                    }
                ]
            }
        }
        
        return self.grafana_client.create_dashboard(memory_dashboard)
```

This comprehensive monitoring architecture provides complete visibility into DevOS operations, enabling proactive management, rapid incident response, and continuous optimization of the LLM-powered development environment.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Create Security & Compliance Framework documentation", "status": "completed", "priority": "high"}, {"id": "2", "content": "Design security architecture with SOC 2 compliance", "status": "completed", "priority": "high"}, {"id": "3", "content": "Add GDPR/CCPA data privacy controls", "status": "completed", "priority": "high"}, {"id": "4", "content": "Create Operational Monitoring & Alerting guide", "status": "completed", "priority": "high"}, {"id": "5", "content": "Design monitoring architecture with metrics", "status": "completed", "priority": "high"}, {"id": "6", "content": "Add security incident response procedures", "status": "in_progress", "priority": "medium"}, {"id": "7", "content": "Update Technical Architecture with security layers", "status": "pending", "priority": "medium"}]