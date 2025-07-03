# Software Bill of Materials (SBOM): DevOS - LLM-Powered Developer OS

## Document Information

**SBOM Format**: SPDX 2.3  
**Creation Date**: 2025-07-02  
**Document Version**: 1.0  
**Creator**: DevOS Development Team  
**License**: MIT  

## Product Overview

**Product Name**: DevOS (LLM-Powered Developer Operating System)  
**Product Version**: 1.0.0  
**Supplier**: Internal Development  
**Download Location**: Custom AMI (to be created)  

## Core System Components

### Operating System Base
| Component | Version | License | Source | Purpose |
|-----------|---------|---------|---------|---------|
| Ubuntu Server | 22.04.3 LTS | GPL-2.0+ | Canonical | Base operating system |
| Linux Kernel | 5.15.0+ | GPL-2.0 | kernel.org | System kernel |
| systemd | 249.11 | LGPL-2.1+ | systemd.io | Service management |
| D-Bus | 1.12.20 | GPL-2.0+ | freedesktop.org | Inter-process communication |
| OpenSSL | 3.0.2 | Apache-2.0 | openssl.org | Cryptographic library |

### Python Runtime Environment
| Component | Version | License | Source | Purpose |
|-----------|---------|---------|---------|---------|
| Python | 3.11.0+ | PSF-2.0 | python.org | Primary runtime |
| pip | 23.0+ | MIT | PyPA | Package manager |
| virtualenv | 20.21.0 | MIT | PyPA | Environment isolation |
| setuptools | 67.0.0 | MIT | PyPA | Package building |

## Core Application Dependencies

### LLM OS Daemon (Primary Service)
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| fastapi | ^0.104.0 | MIT | pypi.org/project/fastapi | REST API framework |
| uvicorn | ^0.24.0 | BSD-3-Clause | pypi.org/project/uvicorn | ASGI server |
| pydantic | ^2.5.0 | MIT | pypi.org/project/pydantic | Data validation |
| sqlalchemy | ^2.0.0 | MIT | pypi.org/project/sqlalchemy | Database ORM |
| alembic | ^1.13.0 | MIT | pypi.org/project/alembic | Database migrations |
| asyncio | built-in | PSF-2.0 | python.org | Async programming |
| aiofiles | ^23.2.1 | Apache-2.0 | pypi.org/project/aiofiles | Async file operations |
| websockets | ^12.0 | BSD-3-Clause | pypi.org/project/websockets | WebSocket support |

### AWS Integration Libraries
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| boto3 | ^1.34.0 | Apache-2.0 | pypi.org/project/boto3 | AWS SDK |
| botocore | ^1.34.0 | Apache-2.0 | pypi.org/project/botocore | AWS low-level SDK |
| aioboto3 | ^12.0.0 | Apache-2.0 | pypi.org/project/aioboto3 | Async AWS SDK |

### Natural Language Processing
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| openai | ^1.3.0 | MIT | pypi.org/project/openai | OpenAI client (fallback) |
| tiktoken | ^0.5.2 | MIT | pypi.org/project/tiktoken | Token counting |
| nltk | ^3.8.1 | Apache-2.0 | pypi.org/project/nltk | NLP utilities |
| spacy | ^3.7.0 | MIT | pypi.org/project/spacy | Advanced NLP |
| transformers | ^4.36.0 | Apache-2.0 | pypi.org/project/transformers | Local model support |

### Speech Processing
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| speechrecognition | ^3.10.0 | BSD-3-Clause | pypi.org/project/speechrecognition | Speech-to-text |
| pyaudio | ^0.2.11 | MIT | pypi.org/project/pyaudio | Audio I/O |
| pyttsx3 | ^2.90 | MPL-2.0 | pypi.org/project/pyttsx3 | Text-to-speech |
| sounddevice | ^0.4.6 | MIT | pypi.org/project/sounddevice | Audio device access |

### System Monitoring & Context
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| psutil | ^5.9.6 | BSD-3-Clause | pypi.org/project/psutil | System monitoring |
| watchdog | ^3.0.0 | Apache-2.0 | pypi.org/project/watchdog | File system monitoring |
| dbus-python | ^1.3.2 | MIT | pypi.org/project/dbus-python | D-Bus integration |
| pygit2 | ^1.13.0 | GPL-2.0 | pypi.org/project/pygit2 | Git integration |
| gitpython | ^3.1.40 | BSD-3-Clause | pypi.org/project/gitpython | Git operations |

### Security & Authentication
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| cryptography | ^41.0.0 | Apache-2.0 | pypi.org/project/cryptography | Encryption |
| keyring | ^24.3.0 | MIT | pypi.org/project/keyring | Credential storage |
| python-jose | ^3.3.0 | MIT | pypi.org/project/python-jose | JWT handling |
| passlib | ^1.7.4 | BSD-2-Clause | pypi.org/project/passlib | Password hashing |

### Configuration & Logging
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| pyyaml | ^6.0.1 | MIT | pypi.org/project/pyyaml | YAML parsing |
| python-dotenv | ^1.0.0 | BSD-3-Clause | pypi.org/project/python-dotenv | Environment variables |
| loguru | ^0.7.2 | MIT | pypi.org/project/loguru | Enhanced logging |
| structlog | ^23.2.0 | MIT | pypi.org/project/structlog | Structured logging |

### Desktop Integration
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| pydbus | ^0.6.0 | LGPL-2.1+ | pypi.org/project/pydbus | D-Bus Python bindings |
| plyer | ^2.1.0 | MIT | pypi.org/project/plyer | Desktop notifications |
| pynput | ^1.7.6 | LGPL-3.0 | pypi.org/project/pynput | Keyboard/mouse control |

## System Dependencies

### Ubuntu System Packages
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| python3-dev | 3.11+ | PSF-2.0 | ubuntu | Python development headers |
| python3-pip | 23.0+ | MIT | ubuntu | Python package installer |
| build-essential | 12.9+ | GPL-2.0+ | ubuntu | Compilation tools |
| pkg-config | 0.29+ | GPL-2.0+ | ubuntu | Library configuration |
| libffi-dev | 3.4+ | MIT | ubuntu | Foreign function interface |
| libssl-dev | 3.0+ | Apache-2.0 | ubuntu | SSL development headers |
| libasound2-dev | 1.2+ | LGPL-2.1+ | ubuntu | Audio system development |
| portaudio19-dev | 19.6+ | MIT | ubuntu | Audio I/O development |
| libpulse-dev | 15.0+ | LGPL-2.1+ | ubuntu | PulseAudio development |
| libdbus-1-dev | 1.12+ | GPL-2.0+ | ubuntu | D-Bus development headers |
| libgirepository1.0-dev | 1.72+ | LGPL-2.0+ | ubuntu | GObject introspection |

### Development Tools
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| git | 2.34+ | GPL-2.0 | ubuntu | Version control |
| curl | 7.81+ | MIT | ubuntu | HTTP client |
| wget | 1.21+ | GPL-3.0+ | ubuntu | File downloader |
| jq | 1.6+ | MIT | ubuntu | JSON processor |
| sqlite3 | 3.37+ | Public Domain | ubuntu | Database engine |
| redis-server | 6.2+ | BSD-3-Clause | ubuntu | In-memory database |

### Desktop Environment Components
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| gnome-shell | 42.0+ | GPL-2.0+ | ubuntu | Desktop shell |
| gnome-shell-extensions | 42.0+ | GPL-2.0+ | ubuntu | Shell extensions |
| dbus-x11 | 1.12+ | GPL-2.0+ | ubuntu | D-Bus X11 support |
| notification-daemon | 3.20+ | GPL-2.0+ | ubuntu | Desktop notifications |
| libnotify-bin | 0.7+ | LGPL-2.1+ | ubuntu | Notification utilities |

## AWS Services Dependencies

### Amazon Bedrock Models
| Model | Provider | Version | License | Purpose |
|-------|----------|---------|---------|---------|
| Claude 3.5 Sonnet | Anthropic | 20241022 | Commercial | Complex reasoning tasks |
| Claude 3 Haiku | Anthropic | 20240307 | Commercial | Fast, simple tasks |
| Titan Text Express | Amazon | v1 | Commercial | Basic text generation |
| Titan Text Lite | Amazon | v1 | Commercial | Simple text tasks |

### AWS Infrastructure Services
| Service | Purpose | Billing Model |
|---------|---------|---------------|
| Amazon Bedrock | LLM model hosting and inference | Pay-per-token |
| AWS IAM | Identity and access management | Free |
| Amazon CloudWatch | Monitoring and logging | Pay-per-use |
| AWS Systems Manager | Configuration management | Free for basic use |
| AWS Secrets Manager | Credential storage | Pay-per-secret |

## Security Considerations

### Vulnerability Management
- **Dependency Scanning**: Regular scans using `pip-audit` and `safety`
- **CVE Monitoring**: Automated alerts for known vulnerabilities
- **Update Policy**: Security patches applied within 48 hours
- **License Compliance**: All dependencies use OSI-approved licenses

### Supply Chain Security
- **Package Verification**: SHA256 checksums for all packages
- **Repository Pinning**: Specific versions pinned in requirements.txt
- **Private Registry**: Option to use private PyPI mirror
- **Build Reproducibility**: Deterministic builds with locked dependencies

## Testing Dependencies

### Test Framework
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| pytest | ^7.4.0 | MIT | pypi.org/project/pytest | Test framework |
| pytest-asyncio | ^0.21.0 | Apache-2.0 | pypi.org/project/pytest-asyncio | Async testing |
| pytest-cov | ^4.1.0 | MIT | pypi.org/project/pytest-cov | Coverage reporting |
| pytest-mock | ^3.11.1 | MIT | pypi.org/project/pytest-mock | Mocking utilities |
| httpx | ^0.25.0 | BSD-3-Clause | pypi.org/project/httpx | HTTP client for testing |
| factory-boy | ^3.3.0 | MIT | pypi.org/project/factory-boy | Test data generation |

### Code Quality Tools
| Package | Version | License | PyPI/Source | Purpose |
|---------|---------|---------|-------------|---------|
| black | ^23.0.0 | MIT | pypi.org/project/black | Code formatting |
| isort | ^5.12.0 | MIT | pypi.org/project/isort | Import sorting |
| flake8 | ^6.1.0 | MIT | pypi.org/project/flake8 | Linting |
| mypy | ^1.7.0 | MIT | pypi.org/project/mypy | Type checking |
| bandit | ^1.7.5 | Apache-2.0 | pypi.org/project/bandit | Security linting |

## Enterprise Integration Dependencies

### Container Orchestration
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| kubectl | 1.28+ | Apache-2.0 | kubernetes | Kubernetes CLI |
| helm | 3.12+ | Apache-2.0 | helm.sh | Kubernetes package manager |
| rancher-cli | 2.7+ | Apache-2.0 | rancher.com | Rancher management CLI |
| docker.io | 24.0+ | Apache-2.0 | ubuntu | Container runtime |
| docker-compose | 2.0+ | Apache-2.0 | ubuntu | Multi-container orchestration |

### Infrastructure as Code
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| aws-cdk | 2.100+ | Apache-2.0 | npm | AWS CDK framework |
| aws-cli | 2.13+ | Apache-2.0 | pypi | AWS command line interface |
| terraform | 1.5+ | MPL-2.0 | hashicorp | Infrastructure provisioning |
| pulumi | 3.80+ | Apache-2.0 | pulumi.com | Modern infrastructure as code |

### Business Process Integration
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| jira-python | ^3.4.0 | BSD-2-Clause | pypi | Jira API client |
| requests-oauthlib | ^1.3.0 | ISC | pypi | OAuth authentication |
| microsoft-graph-api | ^1.0.0 | MIT | pypi | SharePoint/Teams integration |
| python-sharepoint | ^2.0.0 | MIT | pypi | SharePoint document management |

### IT Service Management
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| pyservicenow | ^1.0.0 | MIT | pypi | ServiceNow API client |
| snow-api | ^2.1.0 | Apache-2.0 | pypi | ServiceNow REST client |

### Observability and Monitoring
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| newrelic | ^9.0.0 | Apache-2.0 | pypi | New Relic monitoring |
| splunk-sdk | ^1.7.0 | Apache-2.0 | pypi | Splunk log analysis |
| datadog | ^0.46.0 | BSD-3-Clause | pypi | Datadog monitoring |

### Model Context Protocol (MCP)
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| mcp-python | ^1.0.0 | MIT | github | MCP protocol implementation |
| websocket-client | ^1.6.0 | Apache-2.0 | pypi | WebSocket client for MCP |
| jsonrpc-requests | ^0.4.0 | Apache-2.0 | pypi | JSON-RPC client |

### Vector Database and Memory Agent
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| chromadb | ^0.4.18 | Apache-2.0 | pypi | Local vector database |
| sentence-transformers | ^2.2.2 | Apache-2.0 | pypi | Text embedding models |
| numpy | ^1.24.0 | BSD-3-Clause | pypi | Numerical computing |
| scikit-learn | ^1.3.0 | BSD-3-Clause | pypi | Machine learning utilities |
| faiss-cpu | ^1.7.4 | MIT | pypi | Similarity search (alternative) |
| hnswlib | ^0.7.0 | Apache-2.0 | pypi | Approximate nearest neighbors |

### Embedding Models and AI
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| transformers | ^4.36.0 | Apache-2.0 | pypi | Transformer models |
| torch | ^2.1.0 | BSD-3-Clause | pypi | PyTorch for ML models |
| openai | ^1.3.0 | MIT | pypi | OpenAI API client (optional) |
| tiktoken | ^0.5.2 | MIT | pypi | Token counting and encoding |

### Memory Storage and Processing
| Package | Version | License | Repository | Purpose |
|---------|---------|---------|------------|---------|
| sqlite3 | built-in | Public Domain | python | Local database storage |
| sqlalchemy-utils | ^0.41.0 | BSD-3-Clause | pypi | Database utilities |
| python-dateutil | ^2.8.2 | Apache-2.0 | pypi | Date/time processing |
| python-magic | ^0.4.27 | MIT | pypi | File type detection |

### Container Base Images
| Image | Version | License | Registry | Purpose |
|-------|---------|---------|----------|---------|
| ubuntu | 22.04 | GPL-2.0+ | docker.io | Base container image |
| python | 3.11-slim | PSF-2.0 | docker.io | Python runtime container |
| rancher/kubectl | latest | Apache-2.0 | docker.io | Kubectl in container |

## Build Tools

### Package Management
| Tool | Version | License | Purpose |
|------|---------|---------|---------|
| pip-tools | ^7.3.0 | BSD-2-Clause | Dependency management |
| poetry | ^1.7.0 | MIT | Alternative package management |
| setuptools-scm | ^8.0.0 | MIT | Version management |

### CI/CD Tools
| Tool | Version | License | Purpose |
|------|---------|---------|---------|
| tox | ^4.11.0 | MIT | Testing across environments |
| pre-commit | ^3.5.0 | MIT | Git hooks |
| twine | ^4.0.0 | Apache-2.0 | Package publishing |

## Installation Requirements

### Minimum System Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 cores, 2.5 GHz
- **Memory**: 8 GB RAM
- **Storage**: 50 GB available space
- **Network**: Broadband internet connection for AWS services

### Recommended System Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 8 cores, 3.0+ GHz
- **Memory**: 16 GB RAM
- **Storage**: 100 GB SSD
- **Network**: High-speed internet connection

## License Summary

### License Distribution
- **MIT**: 45% of dependencies
- **Apache-2.0**: 25% of dependencies
- **BSD-3-Clause**: 15% of dependencies
- **GPL-2.0+**: 10% of dependencies
- **Other OSI-Approved**: 5% of dependencies

### Commercial Dependencies
- **AWS Bedrock Models**: Commercial licensing, pay-per-use
- **AWS Services**: Commercial licensing, pay-per-use

## Maintenance and Updates

### Update Schedule
- **Security Updates**: Weekly automated scans, immediate patching for critical vulnerabilities
- **Dependency Updates**: Monthly review and update cycle
- **Major Version Updates**: Quarterly assessment with testing period
- **OS Updates**: Following Ubuntu LTS maintenance schedule

### Support Matrix
- **Python Versions**: 3.11, 3.12 (planned)
- **Ubuntu Versions**: 22.04 LTS (primary), 24.04 LTS (future)
- **AWS Regions**: All regions with Bedrock availability

This SBOM provides complete transparency into all software components, dependencies, and external services used in DevOS, enabling security assessment, license compliance, and supply chain risk management.