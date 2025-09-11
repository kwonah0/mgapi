# MGAPI

A powerful CLI tool for managing and interacting with TCL-based MGAPI servers.

## Features

- **Server Management**: Start TCL servers with monitoring and auto-detection
- **Health Monitoring**: Real-time server status checking
- **Batch Processing**: Process CSV files with spec-based transformations
- **Configuration Management**: Flexible configuration with Dynaconf
- **Interactive Queries**: Send queries with rich output formatting
- **Multiple Output Formats**: Rich terminal, JSON, YAML, and plain text
- **Resumable Operations**: Continue interrupted batch processing

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd mgapi

# Install with uv
uv sync --all-extras

# Run the CLI
uv run mgapi --help
```

### Using pip

```bash
# Install in development mode
pip install -e ".[dev]"

# Run the CLI
mgapi --help
```

## Quick Start

### 1. Start a TCL Server

```bash
# Start TCL server (will monitor for mgapi_config.json creation)
mgapi start --command "bsub -q gpu -n 4 python server.py"

# With custom timeout
mgapi start --command "./start_server.sh" --timeout 300

# Force restart
mgapi start --command "tcl_server --port 8080" --force
```

### 2. Check Server Status

```bash
mgapi status
```

### 3. View Available Endpoints

```bash
mgapi endpoints
```

### 4. Send Queries

```bash
# Direct query
mgapi send --query "ping"

# Interactive mode
mgapi send

# Different output format
mgapi send --query "status" --format json
```

### 5. Process CSV Files in Batches

```bash
# Process user specifications
mgapi batch user_spec users.csv

# Process multiple config files
mgapi batch config_spec config1.csv config2.csv config3.csv

# Use wildcards
mgapi batch user_spec users_*.csv

# Preview without executing
mgapi batch config_spec configs.csv --dry-run
```

### 6. Stop the Server

```bash
mgapi close
```

## Commands

### `mgapi start`
Start a TCL server and monitor for readiness.

**Options:**
- `--command, -c`: Server start command (required)
- `--timeout, -t`: Monitoring timeout in seconds (default: 600)
- `--force, -f`: Force start even if server is running

**How it works:**
1. Checks for existing `mgapi_config.json` and tests server health
2. Executes the provided command via subprocess
3. Monitors current directory for `mgapi_config.json` creation/modification
4. Tests server health when config file is detected
5. Displays job information from `/job_info` endpoint

**Examples:**
```bash
mgapi start --command "bsub -q gpu -n 4 python server.py"
mgapi start --command "./start_tcl_server.sh" --timeout 300
```

### `mgapi status`
Check if the MGAPI server is running and healthy.

**Example:**
```bash
mgapi status
```

### `mgapi endpoints`
Display available API endpoints from the server.

**Options:**
- `--format, -f`: Output format (rich, json, yaml, plain)

**Example:**
```bash
mgapi endpoints
mgapi endpoints --format json
```

### `mgapi info [KEYPATH]`
Display configuration information.

**Options:**
- `--format, -f`: Output format (rich, json, yaml, plain)

**Examples:**
```bash
# Show all configuration
mgapi info

# Show specific value
mgapi info mgapi_url
mgapi info batch.chunk_size

# Different formats
mgapi info --format json
```

### `mgapi send`
Send queries to the MGAPI server.

**Options:**
- `--query, -q`: Query to send
- `--format, -f`: Output format (rich, json, yaml, plain)

**Examples:**
```bash
# Command line query
mgapi send --query "echo hello"

# Interactive mode (uses inquirerpy)
mgapi send

# JSON output
mgapi send --query "status" --format json
```

### `mgapi close`
Stop the running MGAPI server using LSF job control.

**How it works:**
1. Gets job ID from `mgapi_config.json` (preferred)
2. Falls back to `/job_info` endpoint if config unavailable
3. Executes `bkill <job_id>`

**Example:**
```bash
mgapi close
```

### `mgapi batch`
Process CSV files using spec-based transformations.

**Arguments:**
- `SPEC_TYPE`: Type of specification (user_spec, config_spec)
- `CSV_FILES`: One or more CSV files (supports wildcards)

**Options:**
- `--dry-run`: Preview commands without execution
- `--continue-on-error`: Continue processing on row errors (default: true)
- `--stop-on-file-error`: Stop if a file fails completely
- `--filter TEXT`: DuckDB WHERE clause to filter rows
- `--resume`: Resume using existing .result.csv files

**Spec Types:**

#### `user_spec`
**Required columns:** username, email, role, action
**Optional columns:** department, full_name

**Example CSV:**
```csv
username,email,role,action,department
john,john@email.com,admin,create,IT
jane,jane@email.com,user,update,HR
bob,bob@email.com,user,delete,
```

#### `config_spec`
**Required columns:** component, key, value, environment
**Optional columns:** action, description, type

**Example CSV:**
```csv
component,key,value,environment,action
database,host,localhost,dev,set
api,timeout,30,prod,set
cache,enabled,true,staging,set
```

**Examples:**
```bash
# Single file
mgapi batch user_spec users.csv

# Multiple files
mgapi batch config_spec config1.csv config2.csv

# Wildcards
mgapi batch user_spec users_*.csv

# With filtering
mgapi batch config_spec configs.csv --filter "environment='prod'"

# Dry run
mgapi batch user_spec users.csv --dry-run

# Resume interrupted processing
mgapi batch user_spec users.csv --resume
```

### Result Files

Batch processing creates `.result.csv` files with additional columns:
- `exit_code`: Exit code from server response or client error
- `message`: Response message or error description  
- `processed_at`: Timestamp of processing

**Exit Codes:**
- `0`: Success
- `>0`: Server error (from API response)
- `-1`: No response from server
- `-2`: Validation error (client-side)
- `-3`: Exception occurred
- `-4`: Dry run (not executed)

Existing result files are backed up with timestamps: `filename.result.csv.backup.20240101_143022`

## Configuration

MGAPI uses Dynaconf for flexible configuration management.

### Configuration Files (in order of precedence)

1. **Environment variables** (`.env`)
2. **Client settings** (`settings.toml`)
3. **Secrets file** (`.secrets.toml`)
4. **Server info** (`mgapi_config.json` - created by TCL server)

### Client Configuration (`settings.toml`)

```toml
[default]
# Logging settings
log_level = "INFO"
log_file = "logs/mgapi.log"

# API client settings
timeout = 30
retry_count = 3
retry_delay = 1

# Output settings
output_format = "rich"

# Batch processing settings
[default.batch]
chunk_size = 100
save_intermediate = true
max_retries = 3

[development]
log_level = "DEBUG"

[production]
log_level = "WARNING"
```

### Server Configuration (`mgapi_config.json`)

This file is automatically created by the TCL server:

```json
{
  "mgapi_url": "http://server-host:8080",
  "bjob_id": "12345"
}
```

### Environment Variables

```bash
# API Configuration
MGAPI_URL=http://localhost:8000

# Logging
MGAPI_LOG_LEVEL=DEBUG
MGAPI_LOG_FILE=logs/mgapi.log

# Environment switching
ENV_FOR_DYNACONF=development
```

## API Endpoints

When the TCL server is running, these endpoints are available:

- `GET /` - API information and endpoints list
- `GET /health` - Health check
- `GET /job_info` - LSF job information
- `POST /execute` - Execute queries

## Development

### Project Structure

```
mgapi/
├── src/mgapi/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry point
│   ├── config.py                 # Dynaconf configuration
│   ├── api_client.py             # HTTP client
│   ├── commands/                 # CLI commands
│   │   ├── status.py
│   │   ├── info.py
│   │   ├── start.py
│   │   ├── close.py
│   │   ├── send.py
│   │   ├── endpoints.py
│   │   └── batch.py
│   ├── processors/               # CSV spec processors
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user_spec.py
│   │   └── config_spec.py
│   └── utils/                    # Utilities
│       ├── logger.py
│       ├── validators.py
│       ├── formatters.py
│       └── file_manager.py
├── tests/                        # Test suite
├── settings.toml                 # Client configuration
├── mgapi_config.json            # Server information (sample)
└── pyproject.toml               # Package configuration
```

### Running Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=src/mgapi --cov-report=html

# Run specific test
uv run pytest tests/test_cli.py
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/
```

## Workflow

### Typical Usage Flow

1. **Start TCL Server**: Use `mgapi start` with appropriate bsub/LSF command
2. **Monitor**: Server creates `mgapi_config.json` when ready
3. **Verify**: Check server status with `mgapi status`
4. **Interact**: Send queries with `mgapi send` or process batches with `mgapi batch`
5. **Batch Process**: Transform CSV specifications into server commands
6. **Results**: Review `.result.csv` files with exit codes and messages
7. **Cleanup**: Stop server with `mgapi close`

### Batch Processing Workflow

1. **Prepare CSV**: Create CSV with spec-appropriate columns
2. **Validate**: Use `--dry-run` to preview generated commands
3. **Process**: Run batch command to execute against server
4. **Review**: Check `.result.csv` for exit codes and messages
5. **Resume**: Use `--resume` flag to continue interrupted processing

## Troubleshooting

### Server Issues
- **Server not starting**: Check command syntax and LSF availability
- **Timeout during start**: Increase `--timeout` value
- **Config file not created**: Verify TCL server writes to current directory

### Batch Processing Issues  
- **Validation failures**: Check required columns and data formats
- **Processing stopped**: Use `--continue-on-error` flag
- **Resume not working**: Ensure `.result.csv` exists and is valid

### Configuration Issues
- **Config not loading**: Check file permissions and syntax
- **Wrong environment**: Set `ENV_FOR_DYNACONF` variable
- **Missing values**: Use `mgapi info` to debug configuration

### Connection Issues
- **No server response**: Verify URL in `mgapi_config.json`
- **Permission denied**: Check LSF permissions for bkill command
- **Timeouts**: Adjust client timeout settings

## Dependencies

- **click**: CLI framework
- **httpx**: Async HTTP client
- **dynaconf**: Configuration management  
- **rich**: Terminal formatting
- **pandas**: Data processing
- **duckdb**: In-memory SQL processing
- **watchdog**: File monitoring
- **inquirerpy**: Interactive prompts
- **pydantic**: Data validation

## License

[Specify your license]

## Contributing

[Add contribution guidelines]