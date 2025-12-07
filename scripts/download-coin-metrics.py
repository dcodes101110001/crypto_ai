#!/usr/bin/env python3
"""
SimFin Data Download Script

This script downloads financial data from SimFin API and saves it to the stock_data directory.
It requires a SIMFIN_API_KEY environment variable to be set for authentication.

Usage:
    export SIMFIN_API_KEY='your-api-key-here'
    python scripts/download_simfin_data.py

The script downloads:
- US Income Statements (annual)
- US Balance Sheets (annual)
- US Cash Flow Statements (annual)
- US Daily Share Prices
"""

import os
import sys
import logging
import time
from pathlib import Path

# Try to import simfin, but don't fail if it's not installed yet
try:
    import simfin as sf
    SIMFIN_AVAILABLE = True
except ImportError:
    SIMFIN_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def verify_api_key():
    """Verify that the SIMFIN_API_KEY environment variable is set."""
    api_key = os.getenv('SIMFIN_API_KEY')
    if not api_key:
        logger.error("SIMFIN_API_KEY environment variable is not set!")
        logger.error("Please set it with: export SIMFIN_API_KEY='your-api-key-here'")
        sys.exit(1)
    logger.info("✓ SIMFIN_API_KEY found")
    return api_key


def verify_directory(data_dir):
    """Verify and create the stock_data directory if it doesn't exist."""
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.info(f"Creating directory: {data_dir}")
        data_path.mkdir(parents=True, exist_ok=True)
    else:
        logger.info(f"✓ Directory exists: {data_dir}")
    return str(data_path.absolute())


def download_with_retry(load_func, dataset_name, max_retries=5, initial_delay=2, max_delay=300):
    """
    Download data with exponential backoff retry logic for rate limiting.
    
    Args:
        load_func: Function to call for loading data
        dataset_name: Name of the dataset for logging
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        
    Returns:
        Downloaded dataframe
        
    Raises:
        Exception: If all retries are exhausted or non-retryable error occurs
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Downloading {dataset_name}... (attempt {attempt + 1}/{max_retries + 1})")
            df = load_func()
            logger.info(f"✓ {dataset_name}: {len(df)} rows downloaded")
            return df
            
        except Exception as e:
            last_exception = e
            error_str = str(e)
            
            # Check if this is a rate limit error (429)
            is_rate_limit = ('429' in error_str or 
                           'rate limit' in error_str.lower() or
                           'too many requests' in error_str.lower())
            
            # Check if this is a server error (5xx) that might be transient
            is_server_error = any(code in error_str for code in ['500', '502', '503', '504'])
            
            # Determine if we should retry
            should_retry = is_rate_limit or is_server_error
            
            if should_retry and attempt < max_retries:
                logger.warning(f"⚠ {dataset_name} download failed with error: {error_str}")
                logger.info(f"Retrying in {delay} seconds... (attempt {attempt + 2}/{max_retries + 1})")
                time.sleep(delay)
                
                # Exponential backoff
                delay = min(delay * 2, max_delay)
            else:
                # Non-retryable error or max retries exhausted
                if attempt >= max_retries:
                    logger.error(f"✗ Max retries ({max_retries}) exhausted for {dataset_name}")
                else:
                    logger.error(f"✗ Non-retryable error for {dataset_name}: {error_str}")
                raise
    
    # Should not reach here, but raise the last exception if we do
    raise last_exception


def download_simfin_data(api_key, data_dir):
    """
    Download SimFin data using the SimFin Python API with retry logic.
    
    Args:
        api_key: SimFin API key for authentication
        data_dir: Directory path to save the data
    """
    # Check if simfin is available
    if not SIMFIN_AVAILABLE:
        logger.error("simfin library is not installed!")
        logger.error("Please install it with: pip install simfin")
        sys.exit(1)
    
    try:
        logger.info("✓ simfin library imported successfully")
        
        # Set API key and data directory
        logger.info("Configuring SimFin API...")
        sf.set_api_key(api_key)
        sf.set_data_dir(data_dir)
        logger.info(f"✓ SimFin configured with data directory: {data_dir}")
        
        # Download datasets with retry logic
        datasets = [
            ('US Income Statements (Annual)', lambda: sf.load_income(variant='annual', market='us')),
            ('US Balance Sheets (Annual)', lambda: sf.load_balance(variant='annual', market='us')),
            ('US Cash Flow Statements (Annual)', lambda: sf.load_cashflow(variant='annual', market='us')),
            ('US Daily Share Prices', lambda: sf.load_shareprices(variant='daily', market='us')),
        ]
        
        for dataset_name, load_func in datasets:
            try:
                download_with_retry(load_func, dataset_name)
            except Exception as e:
                logger.error(f"✗ Failed to download {dataset_name} after all retries: {str(e)}")
                raise
        
        logger.info("=" * 60)
        logger.info("All datasets downloaded successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        logger.error("Download failed! Please check your API key and network connection.")
        sys.exit(1)


def main():
    """Main function to orchestrate the data download process."""
    logger.info("=" * 60)
    logger.info("SimFin Data Download Script")
    logger.info("=" * 60)
    
    # Get repository root (assuming script is in scripts/ subdirectory)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    data_dir = repo_root / 'stock_data'
    
    logger.info(f"Repository root: {repo_root}")
    logger.info(f"Data directory: {data_dir}")
    
    # Step 1: Verify API key
    logger.info("\nStep 1: Verifying API key...")
    api_key = verify_api_key()
    
    # Step 2: Verify/create directory
    logger.info("\nStep 2: Verifying data directory...")
    data_dir_path = verify_directory(str(data_dir))
    
    # Step 3: Download data
    logger.info("\nStep 3: Downloading SimFin data...")
    download_simfin_data(api_key, data_dir_path)
    
    logger.info("\n✓ Script completed successfully!")


if __name__ == '__main__':
    main()
