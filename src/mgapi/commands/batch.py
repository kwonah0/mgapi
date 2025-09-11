"""Batch processing command for CSV files."""

import glob
from pathlib import Path
from typing import List

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..api_client import MGAPIClient
from ..processors import get_processor, list_spec_types, SPEC_PROCESSORS
from ..utils.formatters import print_error, print_success
from ..utils.logger import logger

console = Console()


class BatchManager:
    """Manage processing of multiple CSV files."""
    
    def __init__(self, spec_type: str, csv_files: List[Path]):
        """Initialize batch manager.
        
        Args:
            spec_type: Type of spec processor to use
            csv_files: List of CSV files to process
        """
        self.spec_type = spec_type
        self.csv_files = [Path(f) for f in csv_files]
        self.results = []
    
    def process_all(self, dry_run: bool = False, continue_on_error: bool = True, 
                   stop_on_file_error: bool = False) -> List[dict]:
        """Process all CSV files.
        
        Args:
            dry_run: If True, preview commands without execution
            continue_on_error: Continue on row-level errors
            stop_on_file_error: Stop on file-level errors
            
        Returns:
            List of processing results
        """
        console.print(Panel(
            f"[bold]Batch Processing Started[/bold]\n"
            f"Spec Type: {self.spec_type}\n"
            f"Files to process: {len(self.csv_files)}",
            title="Batch Job",
            border_style="blue"
        ))
        
        client = MGAPIClient()
        processor_class = get_processor(self.spec_type)
        
        total_stats = {
            'files_processed': 0,
            'files_failed': 0,
            'total_rows': 0,
            'total_success': 0,
            'total_failed': 0,
            'total_no_response': 0,
            'total_validation_failed': 0,
            'total_exception': 0,
            'total_dry_run': 0,
            'total_skipped': 0
        }
        
        for i, csv_file in enumerate(self.csv_files, 1):
            console.print(f"\n[bold]Processing file {i}/{len(self.csv_files)}: {csv_file.name}[/bold]")
            
            try:
                processor = processor_class(csv_file, client)
                result_path, stats = processor.process(
                    dry_run=dry_run,
                    continue_on_error=continue_on_error
                )
                
                self.results.append({
                    'file': csv_file,
                    'result': result_path,
                    'stats': stats,
                    'status': 'completed'
                })
                
                # Update totals
                total_stats['files_processed'] += 1
                for key in ['total_rows', 'total_success', 'total_failed', 'total_no_response',
                           'total_validation_failed', 'total_exception', 'total_dry_run', 'total_skipped']:
                    stat_key = key.replace('total_', '') if key.startswith('total_') else key
                    if stat_key == 'rows':
                        stat_key = 'total'
                    total_stats[key] += stats.get(stat_key, 0)
                
                # Print file summary
                self._print_file_summary(csv_file, stats)
                
            except Exception as e:
                console.print(f"[red]Error processing {csv_file}: {e}[/red]")
                self.results.append({
                    'file': csv_file,
                    'result': None,
                    'stats': None,
                    'status': 'error',
                    'error': str(e)
                })
                total_stats['files_failed'] += 1
                
                if stop_on_file_error:
                    console.print("[red]Stopping batch due to file error[/red]")
                    break
        
        # Print total summary
        self._print_total_summary(total_stats)
        
        return self.results
    
    def _print_file_summary(self, file: Path, stats: dict):
        """Print summary for a single file."""
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        console.print(f"""
        File: {file.name}
        ├─ Total: {stats['total']} rows
        ├─ Success: {stats['success']} ({success_rate:.1f}%)
        ├─ Failed: {stats['failed']}
        ├─ Validation Failed: {stats['validation_failed']}
        ├─ No Response: {stats['no_response']}
        ├─ Exception: {stats['exception']}
        ├─ Dry Run: {stats['dry_run']}
        └─ Skipped: {stats['skipped']}
        """)
    
    def _print_total_summary(self, stats: dict):
        """Print total batch summary."""
        success_rate = (stats['total_success'] / stats['total_rows'] * 100) if stats['total_rows'] > 0 else 0
        
        console.print(Panel(f"""
        [bold]Batch Processing Complete[/bold]
        
        Files:
        ├─ Processed: {stats['files_processed']}/{len(self.csv_files)}
        └─ Failed: {stats['files_failed']}
        
        Total Rows:
        ├─ Total: {stats['total_rows']}
        ├─ Success: {stats['total_success']} ({success_rate:.1f}%)
        ├─ Failed: {stats['total_failed']}
        ├─ Validation Failed: {stats['total_validation_failed']}
        ├─ No Response: {stats['total_no_response']}
        ├─ Exception: {stats['total_exception']}
        ├─ Dry Run: {stats['total_dry_run']}
        └─ Skipped: {stats['total_skipped']}
        """, title="Batch Summary", border_style="green"))


@click.command()
@click.argument("spec_type")
@click.argument("csv_files", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, help="Preview commands without execution")
@click.option("--continue-on-error", is_flag=True, default=True, 
              help="Continue processing on row errors")
@click.option("--stop-on-file-error", is_flag=True, 
              help="Stop if a file fails completely")
@click.option("--filter", help="DuckDB WHERE clause to filter rows")
@click.option("--resume", is_flag=True, 
              help="Resume processing (use existing .result.csv files)")
def batch(spec_type, csv_files, dry_run, continue_on_error, stop_on_file_error, 
          filter, resume):
    """Process one or more CSV files based on spec type.
    
    SPEC_TYPE: Type of specification (e.g., user_spec, config_spec)
    CSV_FILES: One or more CSV files to process (supports wildcards)
    
    Examples:
        mgapi batch user_spec users.csv
        mgapi batch user_spec users1.csv users2.csv users3.csv
        mgapi batch config_spec configs_*.csv
        mgapi batch user_spec *.csv --dry-run
    
    Results are saved to <filename>.result.csv with exit_code and message columns.
    Exit codes from server response are preserved. Client-side codes are negative.
    """
    
    # Validate spec type
    try:
        processor_class = get_processor(spec_type)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        
        # Show available spec types
        console.print("\n[bold]Available spec types:[/bold]")
        for spec in list_spec_types():
            processor = SPEC_PROCESSORS[spec]
            required_cols = ", ".join(processor.required_columns)
            console.print(f"  [cyan]{spec}[/cyan] - Required columns: {required_cols}")
        
        return 1
    
    # Expand glob patterns and validate files
    expanded_files = []
    for pattern in csv_files:
        if '*' in pattern or '?' in pattern:
            # Glob pattern
            matches = glob.glob(pattern)
            if matches:
                expanded_files.extend([Path(f) for f in matches])
            else:
                console.print(f"[yellow]No files matched pattern: {pattern}[/yellow]")
        else:
            # Direct file path
            file_path = Path(pattern)
            if file_path.exists():
                expanded_files.append(file_path)
            else:
                console.print(f"[red]File not found: {pattern}[/red]")
                return 1
    
    if not expanded_files:
        console.print("[red]No CSV files to process[/red]")
        return 1
    
    # Handle resume option
    if resume:
        processed_files = []
        for csv_file in expanded_files:
            result_file = csv_file.parent / f"{csv_file.stem}.result.csv"
            if result_file.exists():
                console.print(f"[yellow]Resuming with result file: {result_file}[/yellow]")
                processed_files.append(result_file)
            else:
                processed_files.append(csv_file)
        expanded_files = processed_files
    
    # Process files
    if len(expanded_files) == 1:
        # Single file processing
        csv_file = expanded_files[0]
        console.print(f"Processing single file: {csv_file}")
        
        try:
            client = MGAPIClient()
            processor = processor_class(csv_file, client)
            
            # Apply filter if specified
            if filter:
                console.print(f"[cyan]Applying filter: {filter}[/cyan]")
                try:
                    processor.conn.execute(f"""
                        CREATE OR REPLACE TABLE spec_data AS 
                        SELECT * FROM spec_data WHERE {filter}
                    """)
                except Exception as e:
                    console.print(f"[red]Filter error: {e}[/red]")
                    return 1
            
            result_path, stats = processor.process(
                dry_run=dry_run,
                continue_on_error=continue_on_error
            )
            
            # Print statistics
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            console.print(Panel(f"""
            [bold]{spec_type.upper()} Processing Complete[/bold]
            
            Total Rows: {stats['total']}
            ✓ Success: {stats['success']} [green]({success_rate:.1f}%)[/green]
            ✗ Failed: {stats['failed']} [red]
            ⚠ Validation Failed: {stats['validation_failed']} [yellow]
            ⚠ No Response: {stats['no_response']} [red]
            ⚠ Exception: {stats['exception']} [red]
            ⊘ Dry Run: {stats['dry_run']} [blue]
            ⊘ Skipped: {stats['skipped']} [yellow](already processed)[/yellow]
            
            Exit Codes:
            0 = Success
            >0 = Server Error (from API response)
            -1 = No response from server
            -2 = Validation error (client-side)
            -3 = Exception occurred
            -4 = Dry run (not executed)
            
            Result File: {result_path}
            """, title="Processing Summary", border_style="blue"))
            
            return 0 if stats['failed'] == 0 and stats['exception'] == 0 else 1
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1
    
    else:
        # Multiple files processing
        console.print(f"Processing {len(expanded_files)} files")
        
        manager = BatchManager(spec_type, expanded_files)
        results = manager.process_all(
            dry_run=dry_run,
            continue_on_error=continue_on_error,
            stop_on_file_error=stop_on_file_error
        )
        
        # Show result files
        console.print("\n[bold]Result Files:[/bold]")
        failed_files = 0
        for result in results:
            if result['status'] == 'completed':
                console.print(f"  ✓ [green]{result['result']}[/green]")
            else:
                console.print(f"  ✗ [red]{result['file']} - {result.get('error', 'Failed')}[/red]")
                failed_files += 1
        
        return 0 if failed_files == 0 else 1