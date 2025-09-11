# MGAPI Testing Guide

This guide demonstrates how to test the complete MGAPI workflow including the mock server integration.

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install MGAPI package
pip install -e .

# Install test server dependencies
pip install fastapi uvicorn
```

### 2. Test Dry-Run Mode (No Server Required)

```bash
# Test user batch processing
python -m mgapi batch user_spec test_users.csv --dry-run

# Test config batch processing  
python -m mgapi batch config_spec test_config.csv --dry-run

# Test with filters
python -m mgapi batch user_spec test_users.csv --dry-run --filter "action = 'create'"

# Test info command
python -m mgapi info
```

### 3. Test with Mock Server

#### Terminal 1 - Start Mock Server
```bash
python test_server.py --host 127.0.0.1 --port 8000
```

This will:
- Start the mock server on http://127.0.0.1:8000
- Automatically create `mgapi_config.json`
- Display available endpoints at http://127.0.0.1:8000/docs

#### Terminal 2 - Test MGAPI Commands
```bash
# Test server health
python -m mgapi status

# Test server info
python -m mgapi info

# Test direct command execution
python -m mgapi execute ping
python -m mgapi execute status

# Test batch processing (actual server calls)
python -m mgapi batch user_spec test_users.csv
python -m mgapi batch config_spec test_config.csv
```

## Test Files

### test_users.csv
Sample user management operations:
```csv
username,email,role,action,department
john,john@example.com,admin,create,IT
jane,jane@example.com,user,create,HR
bob,bob@example.com,manager,update,Finance
alice,alice@example.com,user,delete,IT
charlie,charlie@invalid-email,admin,create,Marketing
```

### test_config.csv
Sample configuration management operations:
```csv
component,key,value,environment,action,description
database,host,localhost,dev,set,Database host configuration
api,timeout,30,prod,set,API timeout in seconds
cache,enabled,true,staging,set,Enable caching
invalid_component,,,dev,set,Missing value test
```

## Mock Server Features

The mock server (`test_server.py`) provides:

### Endpoints
- `GET /` - API information and available endpoints
- `GET /health` - Health check
- `GET /job_info` - LSF job information
- `POST /execute` - Execute queries and commands

### Special Test Commands
- `ping` - Returns "pong"
- `echo <text>` - Echoes back the text
- `status` - Returns server status information
- `error` - Simulates a server error
- `timeout` - Simulates a 5-second delay

### Batch Processing Support
The server handles JSON queries from batch processing:
```json
{
  "tool": "user_manager",
  "action": "create",
  "params": {
    "username": "john",
    "email": "john@example.com"
  }
}
```

## Expected Results

### Dry-Run Mode
- Exit code `-4` for all operations (dry-run indicator)
- Message: "Dry run - not executed"
- Creates backup of existing result files

### Server Mode
- Exit code `0` for successful operations
- Exit code `1+` for server errors  
- Exit code `2` for validation failures (e.g., invalid email)
- Real server responses in result files

### Result Files
Processing creates `<original>.result.csv` files with additional columns:
- `exit_code` - Operation result code
- `message` - Server response message
- `processed_at` - Timestamp

Example result file:
```csv
username,email,role,action,department,exit_code,message,processed_at
john,john@example.com,admin,create,IT,0,User 'john' created successfully,2025-09-11 22:27:37.016570
```

## Automated Testing

Run the complete test suite:
```bash
# Basic functionality test
bash run_tests.sh

# Full workflow test including mock server
python test_workflow.py
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Install missing dependencies
   ```bash
   pip install httpx click rich dynaconf pandas duckdb pyyaml watchdog
   ```

2. **Permission Error**: Make scripts executable
   ```bash
   chmod +x run_tests.sh
   ```

3. **Config File Not Found**: The client looks for `mgapi_config.json` in the current directory
   - For testing, start the mock server first
   - For production, ensure your TCL server creates this file

4. **Server Connection Error**: Check if server is running
   ```bash
   curl http://127.0.0.1:8000/health
   ```

### Verification Steps

1. **Test dry-run mode** - Should work without any server
2. **Start mock server** - Should create mgapi_config.json
3. **Test status command** - Should show server health
4. **Test batch processing** - Should create .result.csv files
5. **Check result files** - Should contain exit codes and messages

This testing approach validates the complete workflow from CSV input through server interaction to result file generation.