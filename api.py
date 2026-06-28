from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("finpulse.db")
    conn.row_factory = sqlite3.Row
    return conn

# Endpoint 1 - Get all stocks
@app.route("/stocks", methods=["GET"])
def get_stocks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stocks")
    stocks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(stocks)

# Endpoint 2 - Get single stock by ticker
@app.route("/stocks/<ticker>", methods=["GET"])
def get_stock(ticker):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stocks WHERE ticker = ?", (ticker,))
    stock = cursor.fetchone()
    conn.close()
    if stock:
        return jsonify(dict(stock))
    return jsonify({"error": "Stock not found"}), 404

# Endpoint 3 - Get market summary
@app.route("/market-summary", methods=["GET"])
def market_summary():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_stocks,
            AVG(pe_ratio) as avg_pe,
            SUM(market_cap) as total_market_cap,
            MAX(price) as highest_price,
            MIN(price) as lowest_price
        FROM stocks
        WHERE price > 0
    """)
    summary = dict(cursor.fetchone())
    conn.close()
    return jsonify(summary)

# Endpoint 4 - Get historical prices for a stock
@app.route("/stocks/<ticker>/history", methods=["GET"])
def get_history(ticker):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM historical_prices 
        WHERE ticker = ? 
        ORDER BY date ASC
    """, (ticker,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(history)

if __name__ == "__main__":
    app.run(debug=True, port=5000)