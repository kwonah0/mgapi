"""File management utilities for batch processing."""

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

console = Console()


class ResultFileManager:
    """Manage result files for batch processing."""
    
    def __init__(self, original_csv: Path):
        """Initialize file manager.
        
        Args:
            original_csv: Path to original CSV file
        """
        self.original_csv = Path(original_csv)
        self.result_csv = self.get_result_path()
        
    def get_result_path(self) -> Path:
        """Get result file path.
        
        Returns:
            Path to .result.csv file
        """
        stem = self.original_csv.stem
        parent = self.original_csv.parent
        return parent / f"{stem}.result.csv"
    
    def backup_existing_result(self) -> Path:
        """Backup existing result file if it exists.
        
        Returns:
            Path to backup file or None if no backup was created
        """
        if self.result_csv.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(f"{self.result_csv}.backup.{timestamp}")
            
            shutil.copy2(self.result_csv, backup_path)
            console.print(f"[yellow]Backed up existing result to: {backup_path}[/yellow]")
            
            return backup_path
        return None
    
    def save_results(self, df: pd.DataFrame) -> Path:
        """Save results to file after backing up existing.
        
        Args:
            df: DataFrame containing results
            
        Returns:
            Path to saved result file
        """
        # Backup existing file
        self.backup_existing_result()
        
        # Save new results
        df.to_csv(self.result_csv, index=False)
        console.print(f"[green]Results saved to: {self.result_csv}[/green]")
        
        return self.result_csv
    
    def load_for_resume(self) -> pd.DataFrame:
        """Load existing result file for resume processing.
        
        Returns:
            DataFrame with existing results or None if file doesn't exist
        """
        if self.result_csv.exists():
            try:
                return pd.read_csv(self.result_csv)
            except Exception as e:
                console.print(f"[red]Error loading result file: {e}[/red]")
                return None
        return None