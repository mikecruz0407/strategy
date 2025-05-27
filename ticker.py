import yfinance as yf

# Simple logo-mapped sample dataset
sample_data = {
    "AAPL": ("Apple Inc.", "https://logo.clearbit.com/apple.com"),
    "AMZN": ("Amazon.com, Inc.", "https://logo.clearbit.com/amazon.com"),
    "GOOGL": ("Alphabet Inc.", "https://logo.clearbit.com/google.com"),
    "MSFT": ("Microsoft Corporation", "https://logo.clearbit.com/microsoft.com"),
    "TSLA": ("Tesla, Inc.", "https://logo.clearbit.com/tesla.com"),
}


def search_tickers_by_name(query):
    query = query.lower().strip()
    results = []
    for ticker, (name, logo) in sample_data.items():
        if query in ticker.lower() or query in name.lower():
            results.append((ticker, name, logo))
    return results


def get_ticker_from_name(name):
    name = name.lower().strip()

    # Make sure keys are clean and lowercase only
    company_to_ticker = {
        'amazon': 'AMZN',
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'alphabet': 'GOOGL',
        'facebook': 'META',
        'meta': 'META',
        'tesla': 'TSLA',
        'netflix': 'NFLX',
        'nvidia': 'NVDA',
        'intel': 'INTC',
        'ibm': 'IBM',
        'oracle': 'ORCL',
        'adobe': 'ADBE',
        'paypal': 'PYPL',
        'salesforce': 'CRM',
        'shopify': 'SHOP',
        'spotify': 'SPOT',
        'zoom': 'ZM',
        'snapchat': 'SNAP',
        'pinterest': 'PINS',
        'twitter': 'TWTR',
        'uber': 'UBER',
        'lyft': 'LYFT',
        'airbnb': 'ABNB',
        'coinbase': 'COIN',
        'palantir': 'PLTR',
        'snowflake': 'SNOW',
        'datadog': 'DDOG',
        'cloudflare': 'NET',
        'crowdstrike': 'CRWD',
        'okta': 'OKTA',
        'zendesk': 'ZEN',
        'atlassian': 'TEAM',
        'dropbox': 'DBX',
        'slack': 'WORK',
        'roku': 'ROKU',
        'etsy': 'ETSY',
        'sofi': 'SOFI',
        'nio': 'NIO',
        'xpeng': 'XPEV',
        'lucid': 'LCID',
        'rivian': 'RIVN',
        'plug power': 'PLUG',
        'enphase': 'ENPH',
        'first solar': 'FSLR',
        'sunpower': 'SPWR',
        'ford': 'F',
        'gm': 'GM',
        'toyota': 'TM',
        'honda': 'HMC',
        'sony': 'SONY',
        'samsung': 'SSNLF',
        'qualcomm': 'QCOM',
        'amd': 'AMD',
        'arm': 'ARM',
        'broadcom': 'AVGO',
        'dell': 'DELL',
        'hp': 'HPQ',
        'logitech': 'LOGI',
        'vmware': 'VMW',
        'intuit': 'INTU',
        'servicenow': 'NOW',
        'zscaler': 'ZS',
        'splunk': 'SPLK',
        'mongodb': 'MDB',
        'autodesk': 'ADSK'
        # Add more clean, lowercase keys and values here as needed
    }

    return company_to_ticker.get(name, name.upper())  # fallback to user input as-is
