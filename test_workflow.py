#!/usr/bin/env python3
"""
Test Workflow Script

This script demonstrates the complete MGAPI workflow:
1. Start mock server
2. Test all mgapi commands
3. Test batch processing
4. Clean up

Usage:
    python test_workflow.py
"""

import json
import subprocess
import time
import sys
from pathlib import Path
import signal
import os


def run_command(cmd, check=True, capture_output=True):
    """Run a command and return result."""
    print(f"$ {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        if capture_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if capture_output and e.stdout:
            print(f"STDOUT: {e.stdout}")
        if capture_output and e.stderr:
            print(f"STDERR: {e.stderr}")
        return e


def wait_for_config_file(timeout=10):
    """Wait for mgapi_config.json to be created."""
    config_file = Path("mgapi_config.json")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if config_file.exists():
            print("✓ mgapi_config.json created")
            return True
        time.sleep(0.5)
    
    print("✗ Timeout waiting for mgapi_config.json")
    return False


def test_server_commands():
    """Test all mgapi commands against the mock server."""
    print("\n=== Testing MGAPI Commands ===")
    
    # Test status command
    print("\n1. Testing mgapi status:")
    run_command("python -m mgapi status")
    
    # Test info command
    print("\n2. Testing mgapi info:")
    run_command("python -m mgapi info")
    
    # Test info with specific key
    print("\n3. Testing mgapi info mgapi_url:")
    run_command("python -m mgapi info mgapi_url")
    
    # Test execute command
    print("\n4. Testing mgapi execute ping:")
    run_command("python -m mgapi execute ping")
    
    print("\n5. Testing mgapi execute status:")
    run_command("python -m mgapi execute status")


def test_batch_processing():
    """Test batch processing with CSV files."""
    print("\n=== Testing Batch Processing ===")
    
    # Test user batch processing (dry run)
    print("\n1. Testing user batch (dry run):")
    run_command("python -m mgapi batch user_spec test_users.csv --dry-run")
    
    # Test config batch processing (dry run)
    print("\n2. Testing config batch (dry run):")
    run_command("python -m mgapi batch config_spec test_config.csv --dry-run")
    
    # Test actual batch processing (if server is running)
    print("\n3. Testing user batch (actual):")
    run_command("python -m mgapi batch user_spec test_users.csv")
    
    print("\n4. Testing config batch (actual):")
    run_command("python -m mgapi batch config_spec test_config.csv")


def test_with_mock_server():
    """Test complete workflow with mock server."""
    print("=== Starting Mock Server Test ===")
    
    # Check if dependencies are installed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("Installing test dependencies...")
        run_command("pip install fastapi uvicorn")
    
    server_process = None
    try:
        # Start mock server
        print("\nStarting mock server...")
        server_process = subprocess.Popen(
            ["python3", "test_server.py", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if config file was created
        if wait_for_config_file():
            # Run tests
            test_server_commands()
            test_batch_processing()
        else:
            print("Server startup failed - config file not created")
            
    except Exception as e:
        print(f"Error during testing: {e}")
        
    finally:
        # Clean up server
        if server_process:
            print("\nStopping mock server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
        
        # Clean up config file
        config_file = Path("mgapi_config.json")
        if config_file.exists():
            config_file.unlink()
            print("✓ Cleaned up mgapi_config.json")


def test_without_server():
    """Test dry-run functionality without server."""
    print("=== Testing Dry-Run Functionality ===")
    
    print("\n1. Testing batch processing in dry-run mode:")
    test_batch_processing()
    
    print("\n2. Testing info command (should show default config):")
    run_command("python -m mgapi info")


def main():
    """Main test function."""
    print("MGAPI Workflow Test")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir(Path(__file__).parent)
    
    # Check if we can import mgapi
    try:
        result = run_command("python -c 'import mgapi; print(mgapi.__version__)'")
        if result.returncode == 0:
            print(f"✓ MGAPI package is available")
        else:
            print("✗ MGAPI package not found - installing in development mode...")
            run_command("pip install -e .")
    except:
        print("✗ Cannot test mgapi import")
    
    # Test dry-run functionality first
    test_without_server()
    
    # Test with mock server if possible
    if Path("test_server.py").exists():
        test_with_mock_server()
    else:
        print("\n✗ test_server.py not found - skipping server tests")
    
    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)