"""
IngestFile: Production-ready data ingestion pipeline for FinVox.

Handles CSV and Excel file uploads with automatic:
- File validation (size, format, encoding)
- Column name standardization
- Currency symbol detection and cleaning
- Date parsing (Sri Lankan DD/MM/YYYY format)
- Null analysis, rejection, and smart filling
- JSON conversion for downstream LLM consumption
"""

import json
import pandas as pd
import numpy as np
import io
import re
import os
import sys
import chardet
from pathlib import Path
from typing import Tuple, Optional, Union, Dict, Any

# Ensure project root is in sys.path for standalone execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.log import log
import pymupdf4llm

# Pre-compiled regex patterns (module-level for performance)
_DATE_PATTERN = re.compile(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}')
_CURRENCY_PATTERN = re.compile(r'\bRs\.?|\bLKR\b|\$', re.IGNORECASE)
_DIGIT_PATTERN = re.compile(r'\d')
_CLEAN_CURRENCY_PATTERN = re.compile(r'\bRs\.?|\bLKR\b|[$,\s]', re.IGNORECASE)

# Supported file extensions
_EXCEL_EXTENSIONS = {'.xlsx', '.xls'}
_CSV_EXTENSIONS = {'.csv'}
_PDF_EXTENSIONS = {'.pdf'}
_ALL_SUPPORTED = _CSV_EXTENSIONS | _EXCEL_EXTENSIONS | _PDF_EXTENSIONS


class IngestFile:
    """Production-ready file ingestion and cleaning pipeline."""

    def __init__(
        self,
        null_threshold: float = None,
        max_file_size_mb: int = None,
        supported_formats: list = None,
    ):
        from src.infrastructure.config import (
            INGESTION_NULL_THRESHOLD,
            INGESTION_MAX_FILE_SIZE_MB,
            INGESTION_SUPPORTED_FORMATS,
        )
        self.null_threshold = null_threshold or INGESTION_NULL_THRESHOLD
        self.max_file_size_mb = max_file_size_mb or INGESTION_MAX_FILE_SIZE_MB
        self.supported_formats = supported_formats or INGESTION_SUPPORTED_FORMATS

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_text_col(series: pd.Series) -> bool:
        """Check if a column holds text (works with Pandas 2 and 3)."""
        return pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)

    @staticmethod
    def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to snake_case."""
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(r'[^a-zA-Z0-9]+', '_', regex=True)
            .str.strip('_')
        )
        return df

    @staticmethod
    def _detect_encoding(file_path: str) -> str:
        """Auto-detect file encoding using chardet."""
        with open(file_path, 'rb') as f:
            raw = f.read(10_000)
        result = chardet.detect(raw)
        encoding = result.get('encoding', 'utf-8') or 'utf-8'
        log.info(f"Detected file encoding: {encoding} (confidence: {result.get('confidence', 0):.0%})")
        return encoding

    def _clean_currency_strings(self, series: pd.Series) -> Tuple[pd.Series, Optional[str]]:
        """Remove currency symbols, commas, and whitespace; convert to float; identify currency."""
        sample_vals = series.dropna().astype(str)
        detected_currency = None

        if sample_vals.str.contains('$', regex=False).any():
            detected_currency = "usd"
        elif sample_vals.str.contains('Rs', case=False, regex=False).any() or \
             sample_vals.str.contains('LKR', case=False, regex=False).any():
            detected_currency = "lkr"

        cleaned = series.astype(str).apply(lambda x: _CLEAN_CURRENCY_PATTERN.sub('', str(x)))
        cleaned = cleaned.replace('', np.nan)
        return pd.to_numeric(cleaned, errors='coerce'), detected_currency

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate file existence, size, and format before processing."""
        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        # Check file extension
        ext = path.suffix.lower().lstrip('.')
        if ext not in self.supported_formats:
            return False, f"Unsupported format '.{ext}'. Supported: {self.supported_formats}"

        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            return False, f"File too large ({size_mb:.1f} MB). Maximum allowed: {self.max_file_size_mb} MB"

        if size_mb == 0:
            return False, "File is empty (0 bytes)."

        log.info(f"File validated: {path.name} ({size_mb:.2f} MB)")
        return True, "OK"

    # ------------------------------------------------------------------
    # Core: Load
    # ------------------------------------------------------------------

    def _load_file(self, file_path_or_buffer: Union[str, io.BytesIO]) -> pd.DataFrame:
        """Load CSV or Excel into a DataFrame with encoding detection."""
        if isinstance(file_path_or_buffer, (str, Path)):
            ext = Path(file_path_or_buffer).suffix.lower()
            if ext in _EXCEL_EXTENSIONS:
                return pd.read_excel(file_path_or_buffer)
            else:
                encoding = self._detect_encoding(str(file_path_or_buffer))
                return pd.read_csv(file_path_or_buffer, encoding=encoding)
        else:
            # BytesIO buffer (from API upload) - try CSV first, then Excel
            try:
                file_path_or_buffer.seek(0)
                return pd.read_csv(file_path_or_buffer)
            except Exception:
                file_path_or_buffer.seek(0)
                return pd.read_excel(file_path_or_buffer)

    # ------------------------------------------------------------------
    # Core: Clean
    # ------------------------------------------------------------------

    def data_cleaning(self, file_path_or_buffer: Union[str, io.BytesIO]) -> Tuple[bool, Optional[pd.DataFrame], str]:
        """
        Full data cleaning pipeline.

        Returns:
            Tuple of (success: bool, cleaned_df: DataFrame | None, message: str)
        """
        try:
            log.info("Starting data cleaning pipeline...")

            # 1. Load
            df = self._load_file(file_path_or_buffer)
            initial_rows, initial_cols = df.shape
            log.info(f"Loaded dataset: {initial_rows} rows x {initial_cols} columns.")

            # 2. Drop completely empty rows and columns
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)

            # 3. Early null-percentage gate
            total_cells = df.size
            total_nulls = df.isnull().sum().sum()
            null_pct = total_nulls / total_cells if total_cells > 0 else 0

            if null_pct > self.null_threshold:
                msg = (f"Dataset rejected: {null_pct * 100:.1f}% null values "
                       f"(threshold: {self.null_threshold * 100:.0f}%). "
                       f"Please fill in the missing data and re-upload.")
                log.error(msg)
                return False, None, msg

            log.info(f"Null check passed ({null_pct * 100:.1f}%). Proceeding...")

            # 4. Standardize column names
            df = self._clean_column_names(df)

            # 5. Remove duplicates
            df = df.drop_duplicates()
            removed = initial_rows - len(df)
            if removed > 0:
                log.info(f"Removed {removed} duplicate/empty rows.")

            # 6. Type parsing (3-pass approach)
            text_cols = [c for c in df.columns if self._is_text_col(df[c])]

            # Pass 1: Strip whitespace, normalize NaN
            for col in text_cols:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', np.nan)

            # Pass 2: Date detection
            for col in text_cols:
                if not self._is_text_col(df[col]):
                    continue
                sample = df[col].dropna().head(10).astype(str)
                if sample.empty:
                    continue
                if sample.apply(lambda x: bool(_DATE_PATTERN.match(str(x)))).any():
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                        log.info(f"Parsed date column: '{col}'")
                    except Exception:
                        pass

            # Pass 3: Currency detection and cleaning
            for col in text_cols:
                if not self._is_text_col(df[col]):
                    continue
                sample = df[col].dropna().head(10).astype(str)
                if sample.empty:
                    continue

                has_currency = sample.apply(lambda x: bool(_CURRENCY_PATTERN.search(str(x)))).any()
                has_digits = sample.apply(lambda x: bool(_DIGIT_PATTERN.search(str(x)))).any()

                if has_currency and has_digits:
                    log.info(f"Currency detected in '{col}'. Sample: {sample.head(3).tolist()}")
                    cleaned_series, currency_sym = self._clean_currency_strings(df[col])
                    df[col] = cleaned_series

                    # Append currency suffix only if the column name doesn't already contain it
                    if currency_sym and currency_sym not in col:
                        new_name = f"{col}_{currency_sym}"
                        df.rename(columns={col: new_name}, inplace=True)
                        log.info(f"Renamed '{col}' -> '{new_name}'")

            # 7. Smart null filling
            remaining_nulls = df.isnull().sum().sum()
            if remaining_nulls > 0:
                log.info(f"Filling {remaining_nulls} remaining null values...")
                for col in df.columns:
                    if not df[col].isnull().any():
                        continue
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df[col] = df[col].fillna(0)
                    elif pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].ffill()
                    else:
                        df[col] = df[col].replace('nan', np.nan).fillna("Unknown")

                log.info("Null filling complete (Numeric->0, Dates->ForwardFill, Text->'Unknown').")

            final_rows, final_cols = df.shape
            log.info(f"Cleaning complete: {final_rows} rows x {final_cols} columns.")
            return True, df, "Data cleaning successful."

        except Exception as e:
            error_msg = f"Data cleaning failed: {e}"
            log.error(error_msg)
            return False, None, error_msg

    # ------------------------------------------------------------------
    # Core: Convert
    # ------------------------------------------------------------------

    def convert_to_json(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert DataFrame to JSON dict with row numbers as keys."""
        df = df.reset_index(drop=True).copy()

        # Datetime -> ISO string for JSON compatibility
        for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d').replace('NaT', None)

        df = df.replace({np.nan: None})
        return {str(i): row.to_dict() for i, row in df.iterrows()}

    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract Markdown from a PDF using PyMuPDF4LLM."""
        log.info(f"Processing PDF file: {file_path}")
        try:
            # 1. Extract to markdown using PyMuPDF4LLM
            # PyMuPDF4LLM does an excellent job creating Markdown tables.
            # We must NOT pass these tables to Pandas for cleaning because Pandas
            # will drop the empty description columns in the summary rows (like Sub-Total).
            md_text = pymupdf4llm.to_markdown(file_path)
            
            result = {
                "text": md_text,
                "tables": [], # We leave tables inside md_text for the Markdown chunker to handle perfectly!
                "metadata": {"source": file_path}
            }
            log.info("PDF processed successfully. Kept tables inside Markdown to preserve layout.")
            return result
        except Exception as e:
            error_msg = f"Failed to process PDF: {str(e)}"
            log.error(error_msg)
            return {"error": error_msg}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point: validate -> clean -> convert to JSON or extract PDF text.

        Returns:
            dict with either the cleaned JSON data, extracted PDF content, or an error message.
        """
        # Validate
        valid, msg = self._validate_file(file_path)
        if not valid:
            log.error(msg)
            return {"error": msg}

        ext = Path(file_path).suffix.lower()
        if ext in _PDF_EXTENSIONS:
            return self._process_pdf(file_path)

        # Clean CSV/Excel
        success, df, msg = self.data_cleaning(file_path)
        if not success or df is None:
            return {"error": msg}

        # Convert
        return self.convert_to_json(df)