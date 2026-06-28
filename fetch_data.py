import yfinance as yf
import sqlite3
import pandas as pd
from datetime import datetime

STOCKS = {
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "Wipro": "WIPRO.NS",
    "HCL Tech": "HCLTECH.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Kotak Mahindra": "KOTAKBANK.NS",
    "Axis Bank": "AXISBANK.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Tata Communications": "TATACOMM.NS",
    "Indus Towers": "INDUSTOWER.NS",
    "Railtel": "RAILTEL.NS",
    "VA Tech Wabag": "WABAG.NS",
    "Ion Exchange": "IONEXCHANG.NS",
    "Thermax": "THERMAX.NS",
    "NTPC": "NTPC.NS",
    "Power Grid": "POWERGRID.NS",
    "Tata Power": "TATAPOWER.NS",
    "Maruti": "MARUTI.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
}

def create_database():
    conn = sqlite3.connect("finpulse.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ticker TEXT,
            price REAL,
            market_cap REAL,
            pe_ratio REAL,
            eps REAL,
            week_52_high REAL,
            week_52_low REAL,
            volume INTEGER,
            sector TEXT,
            last_updated TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database created successfully")

def fetch_and_store():
    conn = sqlite3.connect("finpulse.db")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM stocks")
    
    for name, ticker in STOCKS.items():
        try:
            print(f"Fetching {name}...")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            market_cap = info.get("marketCap", 0)
            pe_ratio = info.get("trailingPE", 0)
            eps = info.get("trailingEps", 0)
            week_52_high = info.get("fiftyTwoWeekHigh", 0)
            week_52_low = info.get("fiftyTwoWeekLow", 0)
            volume = info.get("volume", 0)
            sector = info.get("sector", "Unknown")
            
            cursor.execute("""
                INSERT INTO stocks 
                (name, ticker, price, market_cap, pe_ratio, eps, week_52_high, week_52_low, volume, sector, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, ticker, price, market_cap, pe_ratio, eps,
                  week_52_high, week_52_low, volume, sector,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            hist = stock.history(period="1y")
            
            cursor.execute("DELETE FROM historical_prices WHERE ticker = ?", (ticker,))
            
            for date, row in hist.iterrows():
                cursor.execute("""
                    INSERT INTO historical_prices (ticker, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ticker, str(date.date()), row["Open"], row["High"],
                      row["Low"], row["Close"], row["Volume"]))
            
            print(f"  {name}: ₹{price} | PE: {pe_ratio}")
            
        except Exception as e:
            print(f"  Error fetching {name}: {e}")
    
    conn.commit()
    conn.close()
    print("\nAll data fetched and stored successfully!")

if __name__ == "__main__":
    create_database()
    fetch_and_store()