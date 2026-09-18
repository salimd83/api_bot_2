from pathlib import Path
import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

# Load the variables from the .env file
load_dotenv(override=True)

# 1. Fetch the raw string from your .env file
raw_db_path = os.getenv("DB_PATH", "trading.db")

# 2. Check if the path is absolute (starts with '/' like /trading_bot)
if os.path.isabs(raw_db_path):
    DB_PATH = Path(raw_db_path) # Use the exact path on the server
else:
    # Use the relative path for your local PC setup
    DB_PATH = Path(__file__).resolve().parent / raw_db_path

app = FastAPI()

# Enable CORS so your React frontend can query the backend across different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, change to your exact React URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Dict formatting
    return conn
  
@app.get("/api/dashboard/metrics")
def get_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate performance indicators (KPIs)
    cursor.execute("SELECT COUNT(*) FROM positions WHERE status != 'OPEN'")
    total_trades = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(pnl) FROM positions")
    total_pnl = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(COALESCE(amount, 0) * COALESCE(entry_price, 0)) FROM positions")
    total_size = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT COUNT(*) FROM positions WHERE pnl > 0 and status != 'OPEN'")
    win_trades = cursor.fetchone()[0] or 0
    
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    conn.close()
    return {
        "total_pnl": round(total_pnl, 2),
        "total_trades": total_trades,
        "win_rate": f"{round(win_rate, 2)}%",
        "total_size": f"{round(total_size, 2)}"
    }

@app.get("/api/dashboard/positions")
def get_positions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM positions ORDER BY opened_at DESC")
    positions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return positions