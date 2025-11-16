"""CSV export for database ingestion.

This module exports mapped data to CSV files for PostgreSQL ingestion.
"""

import os
import json
import pandas as pd
import logging
from typing import Dict, List
from pathlib import Path
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports mapped data to CSV files."""
    
    def __init__(self, output_dir: str = 'output'):
        """Initialize CSV exporter.
        
        Args:
            output_dir: Directory for output CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.exported_files = []
    
    def export_table(self, df: pd.DataFrame, table_name: str) -> str:
        """Export DataFrame to CSV file.
        
        Args:
            df: DataFrame to export
            table_name: Name of the database table
            
        Returns:
            Path to exported CSV file
        """
        if df.empty:
            logger.info(f"Table {table_name} is empty, creating empty CSV with headers")
        
        # Serialize JSONB columns
        df = self._serialize_jsonb_columns(df)
        
        # Generate filename
        filename = f"{table_name.lower()}.csv"
        filepath = self.output_dir / filename
        
        # Export to CSV
        df.to_csv(
            filepath,
            index=False,
            encoding='utf-8',
            na_rep='',  # NULL values as empty strings
            escapechar='\\',
            doublequote=True
        )
        
        logger.info(f"Exported {len(df)} rows to {filepath}")
        self.exported_files.append({
            'table': table_name,
            'file': filename,
            'row_count': len(df)
        })
        
        return str(filepath)
    
    def _serialize_jsonb_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Serialize JSONB fields as JSON strings.
        
        Args:
            df: DataFrame with potential JSONB columns
            
        Returns:
            DataFrame with serialized JSONB columns
        """
        df = df.copy()
        
        # Identify JSONB columns (typically dict or list types)
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains dicts or lists
                sample = df[col].dropna().head(1)
                if not sample.empty:
                    value = sample.iloc[0]
                    if isinstance(value, (dict, list)):
                        # Serialize to JSON string
                        df[col] = df[col].apply(
                            lambda x: json.dumps(x) if pd.notna(x) and x else ''
                        )
        
        return df
    
    def export_all(self, mapped_data: Dict[str, pd.DataFrame]) -> List[str]:
        """Export all tables and return file paths.
        
        Args:
            mapped_data: Dictionary mapping table names to DataFrames
            
        Returns:
            List of exported file paths
        """
        file_paths = []
        
        for table_name, df in mapped_data.items():
            filepath = self.export_table(df, table_name)
            file_paths.append(filepath)
        
        logger.info(f"Exported {len(file_paths)} CSV files to {self.output_dir}")
        return file_paths
    
    def create_manifest(self, consultation_session_id: str, 
                       total_entities: int, processing_time: float) -> str:
        """Create manifest file listing all outputs.
        
        Args:
            consultation_session_id: UUID of consultation session
            total_entities: Total number of entities extracted
            processing_time: Processing time in seconds
            
        Returns:
            Path to manifest file
        """
        manifest = {
            'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
            'consultation_session_id': consultation_session_id,
            'files': self.exported_files,
            'total_entities_extracted': total_entities,
            'processing_time_seconds': round(processing_time, 2)
        }
        
        manifest_path = self.output_dir / 'manifest.json'
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created manifest file: {manifest_path}")
        return str(manifest_path)
