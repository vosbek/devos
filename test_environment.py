#!/usr/bin/env python3
"""
Test script to validate the Python environment and dependencies
"""
import sys
import subprocess

def test_python_version():
    """Test Python version"""
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print("✅ Python version OK")
    return True

def test_dependencies():
    """Test required dependencies"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'structlog',
        'python-dotenv',
        'httpx',
        'pytest'
    ]
    
    failed = []
    for package in required_packages:
        try:
            # Handle special package name mappings
            import_name = package.replace('-', '_')
            if package == 'python-dotenv':
                import_name = 'dotenv'
            __import__(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            failed.append(package)
    
    return len(failed) == 0

def test_optional_llm_dependencies():
    """Test LLM service dependencies"""
    print("\nOptional LLM dependencies:")
    
    try:
        import openai
        print("✅ openai - OpenAI integration available")
    except ImportError:
        print("⚠️  openai - OpenAI integration not available")
    
    try:
        import boto3
        print("✅ boto3 - AWS Bedrock integration available")
    except ImportError:
        print("⚠️  boto3 - AWS Bedrock integration not available")

def main():
    """Run all tests"""
    print("DevOS MVP Environment Test")
    print("=" * 30)
    
    all_good = True
    
    all_good &= test_python_version()
    print()
    all_good &= test_dependencies()
    test_optional_llm_dependencies()
    
    print("\n" + "=" * 30)
    if all_good:
        print("✅ Environment ready for DevOS MVP")
        return 0
    else:
        print("❌ Environment issues detected")
        print("Run: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())