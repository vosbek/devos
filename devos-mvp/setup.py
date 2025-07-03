"""
Setup script for DevOS MVP
"""

from setuptools import setup, find_packages

setup(
    name="devos-mvp",
    version="0.1.0",
    description="DevOS - LLM-powered Developer Operating System (MVP)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DevOS Team",
    author_email="devos@example.com",
    url="https://github.com/devos-team/devos",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        # Core Framework
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "pydantic==2.5.0",
        
        # AWS Integration
        "boto3==1.34.0",
        "botocore==1.34.0",
        
        # Database
        "sqlalchemy==2.0.23",
        "alembic==1.13.1",
        
        # System Monitoring
        "psutil==5.9.6",
        "watchdog==3.0.0",
        
        # File Processing
        "aiofiles==23.2.1",
        
        # Configuration
        "pyyaml==6.0.1",
        "python-dotenv==1.0.0",
        
        # Logging
        "structlog==23.2.0",
        
        # Async Support
        "aiohttp==3.9.1",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "pytest-cov==4.1.0",
            "black==23.11.0",
            "isort==5.12.0",
            "flake8==6.1.0",
            "mypy==1.7.1",
        ],
        "enterprise": [
            "kubernetes==28.1.0",
            "jira==3.5.0",
            "requests==2.31.0",
            "newrelic==9.2.0",
            "splunk-sdk==1.7.4",
        ],
    },
    entry_points={
        "console_scripts": [
            "devos=daemon.main:main",
            "devos-cli=cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="devops llm automation ai development",
    project_urls={
        "Bug Reports": "https://github.com/devos-team/devos/issues",
        "Source": "https://github.com/devos-team/devos",
        "Documentation": "https://devos.readthedocs.io",
    },
)