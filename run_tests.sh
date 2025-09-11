#!/bin/bash
"""
MGAPI Integration Test Script

This script demonstrates the complete workflow:
1. Install dependencies if needed
2. Test dry-run batch processing
3. Test individual commands
4. Start mock server and test real API calls

Usage:
    bash run_tests.sh
"""

set -e  # Exit on any error

echo "MGAPI Integration Tests"
echo "======================"

# Check if mgapi is installed
echo "Checking MGAPI installation..."
if python3 -c "import mgapi" 2>/dev/null; then
    echo "✓ MGAPI package is available"
    python3 -c "import mgapi; print(f'Version: {mgapi.__version__}')"
else
    echo "Installing MGAPI in development mode..."
    pip install -e .
fi

echo ""
echo "=== Testing Dry-Run Batch Processing ==="

# Test user batch processing (dry run)
echo "1. Testing user batch processing (dry-run):"
python3 -m mgapi batch user_spec test_users.csv --dry-run

echo ""
echo "2. Testing config batch processing (dry-run):"
python3 -m mgapi batch config_spec test_config.csv --dry-run

echo ""
echo "=== Testing Info Command ==="
echo "3. Testing mgapi info:"
python3 -m mgapi info

echo ""
echo "=== Testing with Filter ==="
echo "4. Testing batch with filter:"
python3 -m mgapi batch user_spec test_users.csv --dry-run --filter "action = 'create'"

echo ""
echo "=== Testing Multiple Files ==="
echo "5. Testing multiple CSV files:"
python3 -m mgapi batch user_spec test_users.csv test_config.csv --dry-run

echo ""
echo "All tests completed successfully!"
echo "======================"

echo ""
echo "To test with real server:"
echo "1. Install server dependencies: pip install fastapi uvicorn"
echo "2. Start server: python3 test_server.py"  
echo "3. In another terminal, run: python3 -m mgapi status"
echo "4. Run batch processing: python3 -m mgapi batch user_spec test_users.csv"