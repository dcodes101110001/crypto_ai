#!/usr/bin/env python3
"""
CoinMarketCap Data Download Script

This script downloads cryptocurrency data from CoinMarketCap API and saves it to the crypto_data directory.
It requires a COINMARKETCAP_API_KEY environment variable to be set for authentication.

Usage:
    export COINMARKETCAP_API_KEY='your-api-key-here'
    python scripts/download_coinmarketcap_data.py

The script downloads:
- Top 50 cryptocurrencies by market capitalization
- Latest market data including price, volume, market cap, etc.
"""

import os
import sys
import logging
import time
import json
import csv
from pathlib import Path
from datetime import datetime

# Try to import requests, but don't fail if it's not installed yet
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

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
    """Verify that the COINMARKETCAP_API_KEY environment variable is set."""
    api_key = os.getenv('COINMARKETCAP_API_KEY')
    if not api_key:
        logger.error("COINMARKETCAP_API_KEY environment variable is not set!")
        logger.error("Please set it with: export COINMARKETCAP_API_KEY='your-api-key-here'")
        sys.exit(1)
    logger.info("✓ COINMARKETCAP_API_KEY found")
    return api_key


def verify_directory(data_dir):
    """Verify and create the crypto_data directory if it doesn't exist."""
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.info(f"Creating directory: {data_dir}")
        data_path.mkdir(parents=True, exist_ok=True)
    else:
        logger.info(f"✓ Directory exists: {data_dir}")
    return str(data_path.absolute())


def download_with_retry(api_key, url, params, max_retries=5, initial_delay=2, max_delay=300):
    """
    Download data with exponential backoff retry logic for rate limiting.
    
    Args:
        api_key: CoinMarketCap API key for authentication
        url: API endpoint URL
        params: Query parameters for the API request
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        
    Returns:
        Response data as dictionary
        
    Raises:
        Exception: If all retries are exhausted or non-retryable error occurs
    """
    delay = initial_delay
    last_exception = None
    
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Requesting data from CoinMarketCap API... (attempt {attempt + 1}/{max_retries + 1})")
            response = requests.get(url, headers=headers, params=params)
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Successfully retrieved data")
                return data
            
            # Handle specific HTTP errors
            elif response.status_code == 429:
                # Rate limit exceeded
                logger.warning(f"⚠ Rate limit exceeded (HTTP 429)")
                if attempt < max_retries:
                    logger.info(f"Retrying in {delay} seconds... (attempt {attempt + 2}/{max_retries + 1})")
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
                    continue
                else:
                    raise Exception(f"Rate limit exceeded after {max_retries} retries")
            
            elif response.status_code == 401:
                # Unauthorized - invalid API key
                logger.error(f"✗ Authentication failed (HTTP 401): Invalid API key")
                raise Exception("Invalid COINMARKETCAP_API_KEY. Please check your API key.")
            
            elif response.status_code >= 500:
                # Server error - retry
                logger.warning(f"⚠ Server error (HTTP {response.status_code})")
                if attempt < max_retries:
                    logger.info(f"Retrying in {delay} seconds... (attempt {attempt + 2}/{max_retries + 1})")
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
                    continue
                else:
                    raise Exception(f"Server error after {max_retries} retries")
            
            else:
                # Other HTTP errors
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"⚠ Request failed: {str(e)}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {delay} seconds... (attempt {attempt + 2}/{max_retries + 1})")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            else:
                logger.error(f"✗ Max retries ({max_retries}) exhausted")
                raise
    
    # Should not reach here, but raise the last exception if we do
    raise last_exception


def create_csv_row(crypto, idx):
    """
    Create a CSV row dictionary from cryptocurrency data.
    
    Args:
        crypto: Cryptocurrency data dictionary from API response
        idx: Rank/index of the cryptocurrency
        
    Returns:
        Dictionary with formatted CSV row data
    """
    quote_usd = crypto.get('quote', {}).get('USD', {})
    
    return {
        'rank': idx,
        'id': crypto.get('id'),
        'name': crypto.get('name'),
        'symbol': crypto.get('symbol'),
        'slug': crypto.get('slug'),
        'num_market_pairs': crypto.get('num_market_pairs'),
        'date_added': crypto.get('date_added'),
        'max_supply': crypto.get('max_supply'),
        'circulating_supply': crypto.get('circulating_supply'),
        'total_supply': crypto.get('total_supply'),
        'cmc_rank': crypto.get('cmc_rank'),
        'last_updated': crypto.get('last_updated'),
        'price_usd': quote_usd.get('price'),
        'volume_24h_usd': quote_usd.get('volume_24h'),
        'volume_change_24h': quote_usd.get('volume_change_24h'),
        'percent_change_1h': quote_usd.get('percent_change_1h'),
        'percent_change_24h': quote_usd.get('percent_change_24h'),
        'percent_change_7d': quote_usd.get('percent_change_7d'),
        'percent_change_30d': quote_usd.get('percent_change_30d'),
        'percent_change_60d': quote_usd.get('percent_change_60d'),
        'percent_change_90d': quote_usd.get('percent_change_90d'),
        'market_cap_usd': quote_usd.get('market_cap'),
        'market_cap_dominance': quote_usd.get('market_cap_dominance'),
        'fully_diluted_market_cap': quote_usd.get('fully_diluted_market_cap'),
    }


def save_to_csv(data, data_dir):
    """
    Save cryptocurrency data to CSV file.
    
    Args:
        data: Response data from CoinMarketCap API
        data_dir: Directory to save the CSV file
    """
    timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"top50_cryptocurrencies_{timestamp}.csv"
    filepath = Path(data_dir) / filename
    
    # Extract cryptocurrency data
    crypto_list = data.get('data', [])
    
    if not crypto_list:
        logger.warning("⚠ No cryptocurrency data found in response")
        return
    
    logger.info(f"Saving {len(crypto_list)} cryptocurrencies to {filename}...")
    
    # Define CSV columns
    fieldnames = [
        'rank',
        'id',
        'name',
        'symbol',
        'slug',
        'num_market_pairs',
        'date_added',
        'max_supply',
        'circulating_supply',
        'total_supply',
        'cmc_rank',
        'last_updated',
        'price_usd',
        'volume_24h_usd',
        'volume_change_24h',
        'percent_change_1h',
        'percent_change_24h',
        'percent_change_7d',
        'percent_change_30d',
        'percent_change_60d',
        'percent_change_90d',
        'market_cap_usd',
        'market_cap_dominance',
        'fully_diluted_market_cap',
    ]
    
    # Write to CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, crypto in enumerate(crypto_list, 1):
            row = create_csv_row(crypto, idx)
            writer.writerow(row)
    
    logger.info(f"✓ Data saved to {filepath}")
    
    # Also save the latest data with a fixed filename for easy access
    latest_filepath = Path(data_dir) / "latest_top50_cryptocurrencies.csv"
    with open(latest_filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, crypto in enumerate(crypto_list, 1):
            row = create_csv_row(crypto, idx)
            writer.writerow(row)
    
    logger.info(f"✓ Latest data also saved to {latest_filepath}")


def download_coinmarketcap_data(api_key, data_dir):
    """
    Download CoinMarketCap data using the CoinMarketCap API with retry logic.
    
    Args:
        api_key: CoinMarketCap API key for authentication
        data_dir: Directory path to save the data
    """
    # Check if requests is available
    if not REQUESTS_AVAILABLE:
        logger.error("requests library is not installed!")
        logger.error("Please install it with: pip install requests")
        sys.exit(1)
    
    try:
        logger.info("✓ requests library imported successfully")
        
        # CoinMarketCap API endpoint for latest cryptocurrency listings
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        
        # Parameters for the API request
        params = {
            'start': '1',
            'limit': '50',  # Top 50 cryptocurrencies
            'convert': 'USD',
            'sort': 'market_cap',
            'sort_dir': 'desc',
        }
        
        logger.info("Fetching top 50 cryptocurrencies by market capitalization...")
        
        # Download data with retry logic
        data = download_with_retry(api_key, url, params)
        
        # Save data to CSV
        save_to_csv(data, data_dir)
        
        logger.info("=" * 60)
        logger.info("Cryptocurrency data downloaded successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        logger.error("Download failed! Please check your API key and network connection.")
        sys.exit(1)


def main():
    """Main function to orchestrate the data download process."""
    logger.info("=" * 60)
    logger.info("CoinMarketCap Data Download Script")
    logger.info("=" * 60)
    
    # Get repository root (assuming script is in scripts/ subdirectory)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    data_dir = repo_root / 'crypto_data'
    
    logger.info(f"Repository root: {repo_root}")
    logger.info(f"Data directory: {data_dir}")
    
    # Step 1: Verify API key
    logger.info("\nStep 1: Verifying API key...")
    api_key = verify_api_key()
    
    # Step 2: Verify/create directory
    logger.info("\nStep 2: Verifying data directory...")
    data_dir_path = verify_directory(str(data_dir))
    
    # Step 3: Download data
    logger.info("\nStep 3: Downloading CoinMarketCap data...")
    download_coinmarketcap_data(api_key, data_dir_path)
    
    logger.info("\n✓ Script completed successfully!")


if __name__ == '__main__':
    main()
