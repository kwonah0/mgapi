"""Base processor class for spec processing."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

import duckdb
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..utils.file_manager import ResultFileManager

console = Console()

# Client-side exit codes (negative)
CLIENT_EXIT_CODES = {
    -1: "No response from server",
    -2: "Validation failed (client-side)",
    -3: "Exception occurred",
    -4: "Dry run (not executed)"
}


class BaseSpecProcessor(ABC):
    """Base class for all spec processors."""
    
    # Subclasses must define these
    spec_type: str = None
    required_columns: List[str] = []
    
    def __init__(self, csv_file: Path, client):
        """Initialize processor.
        
        Args:
            csv_file: Path to CSV file to process
            client: MGAPIClient instance
        """
        self.csv_file = Path(csv_file)
        self.client = client
        self.conn = duckdb.connect(':memory:')
        self.file_manager = ResultFileManager(self.csv_file)
        self.load_data()
    
    def load_data(self):
        """Load CSV data and validate columns."""
        df = pd.read_csv(self.csv_file)
        
        # Check required columns
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Add result columns if not present
        result_columns = ['exit_code', 'message', 'processed_at']
        for col in result_columns:
            if col not in df.columns:
                if col == 'exit_code':
                    df[col] = pd.NA
                elif col == 'processed_at':
                    df[col] = pd.NaT
                else:
                    df[col] = ''
        
        # Load into DuckDB
        self.conn.execute("CREATE TABLE spec_data AS SELECT * FROM df")
    
    @abstractmethod
    def validate_row(self, row: dict) -> Tuple[bool, str]:
        """Validate a row of data.
        
        Args:
            row: Row data as dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def row_to_command(self, row: dict) -> str:
        """Convert row data to command.
        
        Args:
            row: Row data as dictionary
            
        Returns:
            Command string to execute
        """
        pass
    
    def process_response(self, response: Dict[str, Any]) -> Tuple[int, str]:
        """Process API response and extract exit code and message.
        
        Args:
            response: Response from API
            
        Returns:
            Tuple of (exit_code, message)
        """
        if not response:
            return -1, "No response from server"
        
        # Server should provide exit_code in response
        exit_code = response.get('exit_code', 0)
        
        # Get message from response
        message = (
            response.get('message', '') or 
            response.get('result', '') or 
            response.get('error', '')
        )
        
        return exit_code, str(message)
    
    def process(self, dry_run: bool = False, continue_on_error: bool = True) -> Tuple[Path, Dict]:
        """Process all rows in the CSV.
        
        Args:
            dry_run: If True, don't actually execute commands
            continue_on_error: If True, continue processing on errors
            
        Returns:
            Tuple of (result_file_path, statistics_dict)
        """
        df = self.conn.execute("SELECT * FROM spec_data").fetchdf()
        
        stats = {
            'total': len(df),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'validation_failed': 0,
            'no_response': 0,
            'exception': 0,
            'dry_run': 0
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
        ) as progress:
            task = progress.add_task(
                f"Processing {self.csv_file.name}...", 
                total=len(df)
            )
            
            for idx, row in df.iterrows():
                row_dict = row.fillna('').to_dict()
                
                # Skip already processed rows
                if pd.notna(df.at[idx, 'exit_code']):
                    stats['skipped'] += 1
                    progress.update(task, advance=1)
                    continue
                
                # Validate row
                is_valid, validation_msg = self.validate_row(row_dict)
                if not is_valid:
                    df.at[idx, 'exit_code'] = -2
                    df.at[idx, 'message'] = f"Validation failed: {validation_msg}"
                    df.at[idx, 'processed_at'] = datetime.now()
                    stats['validation_failed'] += 1
                    progress.update(task, advance=1)
                    continue
                
                try:
                    # Generate command
                    command = self.row_to_command(row_dict)
                    
                    if dry_run:
                        console.print(f"[cyan][DRY RUN] {command[:100]}...[/cyan]")
                        df.at[idx, 'exit_code'] = -4
                        df.at[idx, 'message'] = "Dry run - not executed"
                        stats['dry_run'] += 1
                    else:
                        # Execute command
                        response = self.client.execute_query(command)
                        exit_code, message = self.process_response(response)
                        
                        df.at[idx, 'exit_code'] = exit_code
                        df.at[idx, 'message'] = message
                        
                        # Update statistics
                        if exit_code == 0:
                            stats['success'] += 1
                        elif exit_code == -1:
                            stats['no_response'] += 1
                        else:
                            stats['failed'] += 1
                        
                        if not continue_on_error and exit_code != 0:
                            console.print("[red]Stopping due to error[/red]")
                            break
                    
                except Exception as e:
                    df.at[idx, 'exit_code'] = -3
                    df.at[idx, 'message'] = f"Exception: {str(e)}"
                    stats['exception'] += 1
                    
                    if not continue_on_error:
                        console.print(f"[red]Stopping due to exception: {e}[/red]")
                        break
                
                df.at[idx, 'processed_at'] = datetime.now()
                progress.update(task, advance=1)
        
        # Save results
        result_path = self.file_manager.save_results(df)
        
        return result_path, stats