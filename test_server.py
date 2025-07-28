#!/usr/bin/env python3
"""
Test script to validate the server starts and responds
"""
import asyncio
import httpx
import subprocess
import time
import sys
import os

async def test_server():
    """Test that the server starts and responds to health checks"""
    print("Testing DevOS MVP server startup...")
    
    # Start the server in a subprocess
    env = os.environ.copy()
    env['LOG_LEVEL'] = 'ERROR'  # Reduce log noise
    
    process = subprocess.Popen([
        sys.executable, '-m', 'src.main'
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8080/health", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Health check passed: {data}")
                    
                    # Test root endpoint
                    response = await client.get("http://localhost:8080/", timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Root endpoint passed: {data}")
                        return True
                    else:
                        print(f"❌ Root endpoint failed: {response.status_code}")
                        return False
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
            except httpx.RequestError as e:
                print(f"❌ Request failed: {e}")
                return False
    finally:
        # Clean up process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def main():
    """Run the server test"""
    try:
        result = asyncio.run(test_server())
        if result:
            print("\n✅ Server test passed - DevOS MVP ready!")
            return 0
        else:
            print("\n❌ Server test failed")
            return 1
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())