# DevOS System Architecture Diagrams

## High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI1[Global Hotkey System<br/>Ctrl+Alt+Space]
        UI2[Desktop Widget<br/>Always-visible UI]
        UI3[Terminal Integration<br/>Shell plugins]
        UI4[Web Interface<br/>Local API access]
    end
    
    subgraph "Command Processing Layer"
        CP1[Natural Language Router<br/>Command interpretation]
        CP2[Model Selection Engine<br/>Cost optimization]
        CP3[Approval Manager<br/>Risk assessment]
        CP4[Cost Optimizer<br/>Usage tracking]
    end
    
    subgraph "Core Services Layer"
        CS1[llm-os-daemon<br/>Central orchestrator]
        CS2[Context Engine<br/>System state monitoring]
        CS3[Memory Agent<br/>Pattern learning]
        CS4[Command Executor<br/>Secure execution]
    end
    
    subgraph "Data Layer"
        DL1[(PostgreSQL<br/>Structured data)]
        DL2[(ChromaDB<br/>Vector embeddings)]
        DL3[File System<br/>Context monitoring]
        DL4[Process Monitor<br/>System state]
    end
    
    subgraph "Integration Layer"
        IL1[Enterprise Tools<br/>Jira, ServiceNow]
        IL2[Development Tools<br/>Git, Docker]
        IL3[AWS Services<br/>Bedrock, CloudWatch]
        IL4[MCP Protocol<br/>Tool extensions]
    end
    
    subgraph "Security & Deployment"
        SD1[Podman Container<br/>Isolation boundary]
        SD2[Apigee Gateway<br/>API management]
        SD3[Microsoft SSO<br/>Enterprise auth]
        SD4[Audit System<br/>Compliance logging]
    end
    
    UI1 --> CP1
    UI2 --> CP1
    UI3 --> CP1
    UI4 --> CP1
    
    CP1 --> CP2
    CP2 --> CP3
    CP3 --> CS1
    CP4 --> CS1
    
    CS1 --> CS2
    CS1 --> CS3
    CS1 --> CS4
    
    CS2 --> DL1
    CS2 --> DL3
    CS2 --> DL4
    CS3 --> DL2
    CS4 --> DL1
    
    CS1 --> IL1
    CS1 --> IL2
    CS1 --> IL3
    CS1 --> IL4
    
    CS1 --> SD1
    IL1 --> SD2
    IL3 --> SD2
    SD2 --> SD3
    CS1 --> SD4
    
    style UI1 fill:#e1f5fe
    style UI2 fill:#e1f5fe
    style UI3 fill:#e1f5fe
    style UI4 fill:#e1f5fe
    style CS1 fill:#fff3e0
    style DL1 fill:#f3e5f5
    style DL2 fill:#f3e5f5
    style SD1 fill:#ffebee
```

## Detailed Component Architecture with Data Flows

```mermaid
graph LR
    subgraph "DevOS Container Environment"
        subgraph "API Layer"
            API[FastAPI Server<br/>Port 8080]
            WS[WebSocket Handler<br/>Real-time updates]
            REST[REST Endpoints<br/>Command submission]
        end
        
        subgraph "Core Daemon"
            DAEMON[llm-os-daemon<br/>Main orchestrator]
            CONFIG[Configuration Manager<br/>Settings & preferences]
            LOGGER[Audit Logger<br/>Compliance tracking]
        end
        
        subgraph "LLM Integration"
            ROUTER[Model Router<br/>Intelligence selection]
            BEDROCK[Bedrock Client<br/>AWS integration]
            PROMPT[Prompt Templates<br/>Context formatting]
            COST[Cost Estimator<br/>Usage optimization]
        end
        
        subgraph "Context System"
            FILE_MON[File Monitor<br/>inotify watcher]
            PROC_MON[Process Monitor<br/>psutil integration]
            GIT_MON[Git Monitor<br/>Repository tracking]
            CONTEXT_DB[(PostgreSQL<br/>Context storage)]
        end
        
        subgraph "Execution Engine"
            EXECUTOR[Command Executor<br/>Secure shell execution]
            SANDBOX[Security Sandbox<br/>Podman isolation]
            VALIDATOR[Command Validator<br/>Safety checks]
        end
        
        subgraph "Approval System"
            APPROVAL[Approval Manager<br/>Risk assessment]
            RISK[Risk Classifier<br/>Safety scoring]
            PREFS[User Preferences<br/>Learning system]
        end
        
        subgraph "Memory System"
            MEMORY[Memory Agent<br/>Pattern storage]
            VECTOR_DB[(ChromaDB<br/>Semantic search)]
            EMBEDDINGS[Embedding Engine<br/>Similarity matching]
        end
    end
    
    subgraph "External Systems"
        AWS_BEDROCK[AWS Bedrock<br/>LLM Models]
        ENTERPRISE[Enterprise Tools<br/>Jira, ServiceNow]
        DEV_TOOLS[Development Tools<br/>Git, Docker, K8s]
        APIGEE[Google Apigee<br/>API Gateway]
        AZURE_AD[Microsoft SSO<br/>Authentication]
    end
    
    API --> DAEMON
    WS --> DAEMON
    REST --> DAEMON
    
    DAEMON --> ROUTER
    DAEMON --> CONTEXT_DB
    DAEMON --> EXECUTOR
    DAEMON --> APPROVAL
    DAEMON --> MEMORY
    
    ROUTER --> BEDROCK
    ROUTER --> COST
    ROUTER --> PROMPT
    BEDROCK --> AWS_BEDROCK
    
    FILE_MON --> CONTEXT_DB
    PROC_MON --> CONTEXT_DB
    GIT_MON --> CONTEXT_DB
    
    EXECUTOR --> SANDBOX
    EXECUTOR --> VALIDATOR
    
    APPROVAL --> RISK
    APPROVAL --> PREFS
    
    MEMORY --> VECTOR_DB
    MEMORY --> EMBEDDINGS
    
    DAEMON --> APIGEE
    APIGEE --> ENTERPRISE
    APIGEE --> DEV_TOOLS
    APIGEE --> AZURE_AD
    
    style DAEMON fill:#fff3e0
    style CONTEXT_DB fill:#f3e5f5
    style VECTOR_DB fill:#f3e5f5
    style AWS_BEDROCK fill:#e8f5e8
    style APIGEE fill:#ffebee
```

## Command Processing Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Widget as Desktop Widget
    participant Daemon as llm-os-daemon
    participant Context as Context Engine
    participant Router as Model Router
    participant Bedrock as AWS Bedrock
    participant Approval as Approval Manager
    participant Executor as Command Executor
    participant Memory as Memory Agent
    participant System as OS/Container
    
    User->>Widget: Ctrl+Alt+Space + "organize files by date"
    Widget->>Daemon: POST /api/v1/commands
    
    Daemon->>Context: get_current_context()
    Context->>Context: Gather file system state
    Context->>Context: Check running processes
    Context->>Context: Get Git repository status
    Context->>Daemon: Return aggregated context
    
    Daemon->>Memory: find_similar_commands(command, context)
    Memory->>Memory: Search vector database
    Memory->>Daemon: Return similar patterns
    
    Daemon->>Router: select_model(command, context)
    Router->>Router: Analyze complexity score
    Router->>Router: Calculate cost estimate
    Router->>Daemon: Return model selection
    
    Daemon->>Bedrock: generate_commands(prompt, context, model)
    Bedrock->>Daemon: Return command sequence
    
    Daemon->>Approval: assess_risk(commands, context)
    Approval->>Approval: Classify operation risk
    
    alt Safe Operation
        Approval->>Daemon: Auto-approve execution
    else Requires User Approval
        Approval->>Widget: Request user confirmation
        Widget->>User: Show approval dialog
        User->>Widget: Approve/Reject
        Widget->>Approval: User decision
        Approval->>Daemon: Approval result
    end
    
    alt Approved
        Daemon->>Executor: execute_commands(commands, context)
        Executor->>System: Execute shell commands
        System->>Executor: Return execution results
        Executor->>Daemon: Command results
        
        Daemon->>Memory: store_command_pattern(command, context, result)
        Memory->>Memory: Update learning database
        
        Daemon->>Widget: Return success response
        Widget->>User: Display completion status
    else Rejected
        Daemon->>Widget: Return rejection response
        Widget->>User: Show rejection reason
    end
```

## Container Deployment Architecture

```mermaid
graph TB
    subgraph "Host System - Ubuntu 22.04"
        HOST[Host Operating System<br/>Ubuntu 22.04 LTS]
        PODMAN[Podman Engine<br/>Container runtime]
        VOLUMES[Persistent Volumes<br/>Data persistence]
        NETWORK[Host Network<br/>Desktop integration]
    end
    
    subgraph "DevOS Container Stack"
        subgraph "Application Layer"
            DEVOS[DevOS Daemon<br/>Python 3.11 + FastAPI]
            API[Local API Server<br/>Port 8080]
            WIDGET[Desktop Widget<br/>GTK4 + X11/Wayland]
        end
        
        subgraph "Runtime Layer"
            PYTHON[Python Runtime<br/>3.11 + Dependencies]
            DEPS[System Dependencies<br/>psutil, inotify, git]
            CONFIG[Configuration<br/>YAML + Environment]
        end
        
        subgraph "System Layer"
            UBUNTU[Ubuntu 22.04 Base<br/>Container OS]
            SYSTEMD[systemd Services<br/>Daemon management]
            DBUS[D-Bus Integration<br/>Desktop communication]
        end
    end
    
    subgraph "Database Services"
        POSTGRES[PostgreSQL 15<br/>Structured data storage]
        CHROMADB[ChromaDB<br/>Vector embeddings]
        PG_DATA[(PostgreSQL Data<br/>Persistent volume)]
        CHROMA_DATA[(ChromaDB Data<br/>Persistent volume)]
    end
    
    subgraph "External Services"
        AWS[AWS Bedrock<br/>LLM Models]
        ENTERPRISE[Enterprise APIs<br/>Jira, ServiceNow]
        APIGEE[Google Apigee<br/>API Gateway]
        AZURE_AD[Microsoft SSO<br/>Authentication]
    end
    
    HOST --> PODMAN
    PODMAN --> DEVOS
    PODMAN --> POSTGRES
    PODMAN --> CHROMADB
    
    VOLUMES --> PG_DATA
    VOLUMES --> CHROMA_DATA
    VOLUMES --> CONFIG
    
    POSTGRES --> PG_DATA
    CHROMADB --> CHROMA_DATA
    
    DEVOS --> POSTGRES
    DEVOS --> CHROMADB
    
    NETWORK --> API
    NETWORK --> WIDGET
    
    DEVOS --> APIGEE
    APIGEE --> AWS
    APIGEE --> ENTERPRISE
    APIGEE --> AZURE_AD
    
    style HOST fill:#e3f2fd
    style DEVOS fill:#fff3e0
    style POSTGRES fill:#f3e5f5
    style CHROMADB fill:#f3e5f5
    style AWS fill:#e8f5e8
    style APIGEE fill:#ffebee
```

## Enterprise Integration Architecture

```mermaid
graph TB
    subgraph "DevOS Core"
        DAEMON[llm-os-daemon<br/>Central orchestrator]
        INTEGRATIONS[Integration Manager<br/>Enterprise connectors]
        AUTH[Authentication Handler<br/>SSO integration]
    end
    
    subgraph "API Gateway Layer - Google Apigee"
        APIGEE[Apigee Proxy<br/>API management]
        RATE_LIMIT[Rate Limiting<br/>Quota management]
        ANALYTICS[API Analytics<br/>Usage monitoring]
        SECURITY[Security Policies<br/>Threat protection]
    end
    
    subgraph "Authentication Layer"
        AZURE_AD[Microsoft Azure AD<br/>Identity provider]
        SSO[Single Sign-On<br/>OIDC/OAuth2]
        ROLES[Role Management<br/>RBAC permissions]
    end
    
    subgraph "Enterprise Tools"
        JIRA[Atlassian Jira<br/>Issue tracking]
        SERVICENOW[ServiceNow<br/>ITSM platform]
        SPLUNK[Splunk<br/>Log analytics]
        NEWRELIC[New Relic<br/>APM monitoring]
        SHAREPOINT[SharePoint<br/>Document management]
    end
    
    subgraph "Compliance & Audit"
        AUDIT_DB[(Audit Database<br/>PostgreSQL)]
        COMPLIANCE[Compliance Reporter<br/>Regulatory tracking]
        GOVERNANCE[Governance Engine<br/>Policy enforcement]
    end
    
    DAEMON --> AUTH
    DAEMON --> INTEGRATIONS
    
    INTEGRATIONS --> APIGEE
    AUTH --> AZURE_AD
    
    APIGEE --> RATE_LIMIT
    APIGEE --> ANALYTICS
    APIGEE --> SECURITY
    
    AZURE_AD --> SSO
    SSO --> ROLES
    
    APIGEE --> JIRA
    APIGEE --> SERVICENOW
    APIGEE --> SPLUNK
    APIGEE --> NEWRELIC
    APIGEE --> SHAREPOINT
    
    DAEMON --> AUDIT_DB
    AUDIT_DB --> COMPLIANCE
    COMPLIANCE --> GOVERNANCE
    
    style DAEMON fill:#fff3e0
    style APIGEE fill:#ffebee
    style AZURE_AD fill:#e1f5fe
    style AUDIT_DB fill:#f3e5f5
```

## Data Flow Architecture

```mermaid
flowchart TD
    subgraph "Input Sources"
        USER_CMD[User Commands<br/>Natural language]
        FILE_EVENTS[File System Events<br/>inotify]
        PROC_EVENTS[Process Events<br/>psutil]
        GIT_EVENTS[Git Events<br/>Hooks]
    end
    
    subgraph "Context Aggregation"
        CONTEXT_ENGINE[Context Engine<br/>Real-time aggregation]
        CONTEXT_DB[(PostgreSQL<br/>Structured context)]
    end
    
    subgraph "Intelligence Layer"
        MODEL_ROUTER[Model Router<br/>Selection logic]
        BEDROCK[AWS Bedrock<br/>LLM processing]
        MEMORY_AGENT[Memory Agent<br/>Pattern matching]
        VECTOR_DB[(ChromaDB<br/>Embeddings)]
    end
    
    subgraph "Decision Layer"
        APPROVAL_MGR[Approval Manager<br/>Risk assessment]
        RISK_CLASSIFIER[Risk Classifier<br/>Safety scoring]
        USER_PREFS[(User Preferences<br/>Learning data)]
    end
    
    subgraph "Execution Layer"
        CMD_EXECUTOR[Command Executor<br/>Secure execution]
        SANDBOX[Podman Sandbox<br/>Isolation]
        AUDIT_LOG[(Audit Log<br/>Compliance)]
    end
    
    subgraph "Output Destinations"
        SYSTEM_OPS[System Operations<br/>File/Process changes]
        USER_FEEDBACK[User Feedback<br/>Results display]
        ENTERPRISE_APIS[Enterprise APIs<br/>Tool integration]
    end
    
    USER_CMD --> CONTEXT_ENGINE
    FILE_EVENTS --> CONTEXT_ENGINE
    PROC_EVENTS --> CONTEXT_ENGINE
    GIT_EVENTS --> CONTEXT_ENGINE
    
    CONTEXT_ENGINE --> CONTEXT_DB
    CONTEXT_DB --> MODEL_ROUTER
    CONTEXT_DB --> MEMORY_AGENT
    
    MODEL_ROUTER --> BEDROCK
    MEMORY_AGENT --> VECTOR_DB
    BEDROCK --> APPROVAL_MGR
    VECTOR_DB --> APPROVAL_MGR
    
    APPROVAL_MGR --> RISK_CLASSIFIER
    RISK_CLASSIFIER --> USER_PREFS
    USER_PREFS --> CMD_EXECUTOR
    
    CMD_EXECUTOR --> SANDBOX
    CMD_EXECUTOR --> AUDIT_LOG
    
    SANDBOX --> SYSTEM_OPS
    CMD_EXECUTOR --> USER_FEEDBACK
    CMD_EXECUTOR --> ENTERPRISE_APIS
    
    style CONTEXT_ENGINE fill:#e1f5fe
    style MODEL_ROUTER fill:#fff3e0
    style APPROVAL_MGR fill:#ffebee
    style CMD_EXECUTOR fill:#e8f5e8
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Boundaries"
        subgraph "Host System Boundary"
            HOST_OS[Host Operating System<br/>Ubuntu 22.04]
            HOST_RESOURCES[Host Resources<br/>Protected]
        end
        
        subgraph "Container Boundary"
            CONTAINER[Podman Container<br/>Isolation layer]
            DEVOS_PROC[DevOS Processes<br/>Sandboxed execution]
        end
        
        subgraph "Application Boundary"
            USER_SPACE[User Space<br/>Command processing]
            SYSTEM_CALLS[System Calls<br/>Controlled access]
        end
    end
    
    subgraph "Security Controls"
        AUTH_LAYER[Authentication Layer<br/>Microsoft SSO]
        AUTHZ_LAYER[Authorization Layer<br/>RBAC permissions]
        AUDIT_LAYER[Audit Layer<br/>Compliance logging]
        APPROVAL_LAYER[Approval Layer<br/>Risk assessment]
    end
    
    subgraph "Threat Mitigation"
        INPUT_VALIDATION[Input Validation<br/>Command sanitization]
        PRIVILEGE_CONTROL[Privilege Control<br/>Least privilege]
        NETWORK_SECURITY[Network Security<br/>API gateway]
        DATA_PROTECTION[Data Protection<br/>Encryption at rest]
    end
    
    HOST_OS --> CONTAINER
    CONTAINER --> DEVOS_PROC
    DEVOS_PROC --> USER_SPACE
    USER_SPACE --> SYSTEM_CALLS
    
    AUTH_LAYER --> AUTHZ_LAYER
    AUTHZ_LAYER --> AUDIT_LAYER
    AUDIT_LAYER --> APPROVAL_LAYER
    
    INPUT_VALIDATION --> PRIVILEGE_CONTROL
    PRIVILEGE_CONTROL --> NETWORK_SECURITY
    NETWORK_SECURITY --> DATA_PROTECTION
    
    DEVOS_PROC --> AUTH_LAYER
    SYSTEM_CALLS --> INPUT_VALIDATION
    
    style HOST_OS fill:#ffebee
    style CONTAINER fill:#fff3e0
    style AUTH_LAYER fill:#e8f5e8
    style INPUT_VALIDATION fill:#e1f5fe
```