"""
Data loader and DuckDB session manager for OMOP tables.
Provides centralized access to DuckDB connection with pre-registered Parquet tables.
Uses native DuckDB execution to ensure pure DuckDB/Parquet performance.
"""

import os
import duckdb
from typing import Optional, Dict, List, Any
from src.data.lzo_util import ensure_parquet_tables


class OMOPDataLoader:
    def __init__(
        self,
        source_dir: str = "synthea100k",
        parquet_dir: str = "data/parquet",
        db_path: str = ":memory:"
    ):
        self.source_dir = source_dir
        self.parquet_dir = parquet_dir
        self.db_path = db_path
        self.con: Optional[duckdb.DuckDBPyConnection] = None
        self.table_paths: Dict[str, str] = {}
        
    def initialize(self, force_reconvert: bool = False) -> duckdb.DuckDBPyConnection:
        """
        Ensures Parquet files exist and connects DuckDB, registering views for all tables.
        """
        self.table_paths = ensure_parquet_tables(
            source_dir=self.source_dir,
            parquet_dir=self.parquet_dir
        )
        
        self.con = duckdb.connect(self.db_path)
        
        # Register views for each table
        for table_name, parquet_path in self.table_paths.items():
            clean_path = parquet_path.replace("\\", "/")
            self.con.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{clean_path}');")
            
        return self.con

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        if self.con is None:
            return self.initialize()
        return self.con

    def query(self, sql: str, params: Optional[list] = None):
        """Executes a SQL query and returns the DuckDB result relation."""
        con = self.get_connection()
        if params:
            return con.execute(sql, params)
        return con.execute(sql)

    def query_dicts(self, sql: str, params: Optional[list] = None) -> List[Dict[str, Any]]:
        """Executes SQL and returns a list of dictionaries (column_name -> value)."""
        rel = self.query(sql, params)
        cols = [desc[0] for desc in rel.description]
        rows = rel.fetchall()
        return [dict(zip(cols, row)) for row in rows]

    def query_one(self, sql: str, params: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """Executes SQL and returns a single dictionary result."""
        results = self.query_dicts(sql, params)
        return results[0] if results else None

    def close(self):
        if self.con is not None:
            self.con.close()
            self.con = None


# Default shared singleton instance
_default_loader: Optional[OMOPDataLoader] = None

def get_db(source_dir: str = "synthea100k", parquet_dir: str = "data/parquet") -> duckdb.DuckDBPyConnection:
    global _default_loader
    if _default_loader is None:
        _default_loader = OMOPDataLoader(source_dir=source_dir, parquet_dir=parquet_dir)
        _default_loader.initialize()
    return _default_loader.get_connection()
