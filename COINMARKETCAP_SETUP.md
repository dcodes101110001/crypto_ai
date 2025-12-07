# CoinMarketCap Workflow Setup

This document describes how to set up and use the CoinMarketCap data download workflow.

## Overview

The workflow automatically downloads data for the top 50 cryptocurrencies by market capitalization from CoinMarketCap API daily at 2 AM UTC.

## Prerequisites

You need a CoinMarketCap API key. Get one for free at: https://coinmarketcap.com/api/

## Setup

1. **Add CoinMarketCap API Key as a Secret**
   - Go to your repository on GitHub
   - Navigate to: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `COINMARKETCAP_API_KEY`
   - Value: Your CoinMarketCap API key
   - Click "Add secret"

2. **Optional: Add Git PAT for Authentication** (only if needed for public forks)
   - Create a Personal Access Token at: https://github.com/settings/tokens
   - Select scopes: `repo` and `workflow`
   - Add as repository secret named `GIT_PAT`

## Data Output

The workflow downloads and saves:
- **Top 50 cryptocurrencies** ranked by market capitalization
- Data includes: price, volume, market cap, percentage changes, and more
- Two CSV files are created:
  - `top50_cryptocurrencies_YYYY-MM-DD_HH-MM-SS.csv` - Timestamped version
  - `latest_top50_cryptocurrencies.csv` - Always contains the latest data

Data is saved to the `crypto_data/` directory.

## CSV Columns

The downloaded CSV files contain the following information:
- `rank` - Current ranking
- `id`, `name`, `symbol`, `slug` - Cryptocurrency identifiers
- `price_usd` - Current price in USD
- `volume_24h_usd` - 24-hour trading volume
- `market_cap_usd` - Market capitalization
- `percent_change_1h`, `percent_change_24h`, `percent_change_7d`, etc. - Price changes
- And more (see script for complete list)

## Manual Trigger

To manually trigger the workflow:
1. Go to: Actions → Download CoinMarketCap Data
2. Click "Run workflow"
3. Select the branch and click "Run workflow"

## Troubleshooting

### No data downloaded
- Check that `COINMARKETCAP_API_KEY` secret is set correctly
- Verify your API key is valid at CoinMarketCap
- Check if you've exceeded API rate limits

### Push failed
- Add `GIT_PAT` secret with proper permissions
- Or configure SSH authentication (see workflow comments)

## Local Testing

To test the download script locally:

```bash
# Install dependencies
pip install requests

# Set your API key
export COINMARKETCAP_API_KEY='your-api-key-here'

# Run the script
python scripts/download_coinmarketcap_data.py
```

## Files Modified

- `.github/workflows/data-coinmarket-cap.yml` - GitHub Actions workflow
- `scripts/download_coinmarketcap_data.py` - Python script to fetch data
- `.gitignore` - Excludes Python cache files
