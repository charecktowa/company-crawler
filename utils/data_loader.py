"""
Data loader utilities for loading company data from Excel files.
"""

import logging
from typing import List, Tuple, Any

import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


def load_company_data(xlsx_path: str) -> List[Tuple[str, str, str, str]]:
    """
    Load company data from an Excel file.

    Args:
        xlsx_path: Path to the Excel file

    Returns:
        List[Tuple[str, str, str, str]]: List of tuples with company data
                                         (ric, company_name, industry_type, web_link)
    """
    try:
        logger.info(f"Loading company data from {xlsx_path}")
        df = pd.read_excel(xlsx_path)

        # Log column names for debugging
        logger.debug(f"Columns in Excel file: {df.columns.tolist()}")

        # Map the specific columns from your file to the expected names
        column_mapping = {
            "Identifier (RIC)": "ric",
            "Company Name": "company_name",
            "GICS Industry Name": "industry_type",
            "Web Link to Home Page": "web_link",
        }

        # Rename columns based on mapping
        df = df.rename(columns=column_mapping)

        # Ensure required columns exist
        required_columns = ["ric", "company_name", "industry_type", "web_link"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Clean data - remove rows with missing values in required columns
        df = df.dropna(subset=required_columns)

        # Clean URLs (remove trailing slashes, ensure http/https)
        df["web_link"] = df["web_link"].apply(lambda url: clean_url(url))

        # Convert DataFrame to list of tuples
        company_data = list(df[required_columns].itertuples(index=False, name=None))

        logger.info(f"Loaded {len(company_data)} companies from {xlsx_path}")
        return company_data

    except Exception as e:
        logger.error(f"Error loading company data: {e}")
        raise


def clean_url(url: str) -> str:
    """
    Clean a URL by ensuring it has http/https prefix and no trailing slash.

    Args:
        url: URL to clean

    Returns:
        str: Cleaned URL
    """
    if not url:
        return ""

    url = str(url).strip()

    # Add http if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Remove trailing slash
    url = url.rstrip("/")

    return url
