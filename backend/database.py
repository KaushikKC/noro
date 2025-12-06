"""
Simple SQLite database for storing market data
Used for fast retrieval while NeoFS provides permanent storage
"""
import sqlite3
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

DB_PATH = os.getenv("MARKET_DB_PATH", "markets.db")

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn

def init_database():
    """Initialize the database with markets table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id TEXT UNIQUE NOT NULL,
            question TEXT NOT NULL,
            description TEXT,
            category TEXT,
            resolve_date TEXT,
            resolve_timestamp INTEGER,
            oracle_url TEXT,
            creator TEXT,
            created_at TEXT,
            created_timestamp INTEGER,
            is_resolved INTEGER DEFAULT 0,
            outcome TEXT,
            yes_shares INTEGER DEFAULT 0,
            no_shares INTEGER DEFAULT 0,
            probability REAL DEFAULT 50.0,
            neofs_object_id TEXT,
            neofs_container_id TEXT,
            neofs_url TEXT,
            status TEXT DEFAULT 'active',
            source TEXT,
            updated_at TEXT,
            UNIQUE(market_id)
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_market_id ON markets(market_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON markets(status)
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

def insert_market(market_data: Dict[str, Any]) -> bool:
    """
    Insert or update a market in the database
    
    Args:
        market_data: Market data dictionary
        
    Returns:
        True if successful
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prepare data
        now = datetime.now().isoformat()
        now_timestamp = int(datetime.now().timestamp())
        
        cursor.execute("""
            INSERT OR REPLACE INTO markets (
                market_id, question, description, category,
                resolve_date, resolve_timestamp, oracle_url,
                creator, created_at, created_timestamp,
                is_resolved, outcome, yes_shares, no_shares,
                probability, neofs_object_id, neofs_container_id,
                neofs_url, status, source, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            market_data.get("market_id"),
            market_data.get("question"),
            market_data.get("description"),
            market_data.get("category"),
            market_data.get("resolve_date"),
            market_data.get("resolve_timestamp"),
            market_data.get("oracle_url"),
            market_data.get("creator"),
            market_data.get("created_at", now),
            market_data.get("created_timestamp", now_timestamp),
            1 if market_data.get("is_resolved") or market_data.get("resolved") else 0,
            market_data.get("outcome"),
            market_data.get("yes_shares", 0),
            market_data.get("no_shares", 0),
            market_data.get("probability", 50.0),
            market_data.get("neofs_object_id"),
            market_data.get("neofs_container_id"),
            market_data.get("neofs_url"),
            market_data.get("status", "active"),
            market_data.get("source", "frontend"),
            now
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error inserting market: {e}")
        return False

def get_market(market_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a market by market_id
    
    Args:
        market_id: Market ID
        
    Returns:
        Market data dictionary or None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM markets WHERE market_id = ?", (market_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"❌ Error getting market: {e}")
        return None

def list_markets(status: str = "active", limit: int = 100) -> List[Dict[str, Any]]:
    """
    List all markets
    
    Args:
        status: Filter by status (default: "active")
        limit: Maximum number of markets to return
        
    Returns:
        List of market data dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM markets 
            WHERE status = ? 
            ORDER BY created_timestamp DESC 
            LIMIT ?
        """, (status, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ Error listing markets: {e}")
        return []

def update_market_onchain_data(market_id: str, onchain_data: Dict[str, Any]) -> bool:
    """
    Update market with on-chain data (shares, resolved status, etc.)
    
    Args:
        market_id: Market ID
        onchain_data: On-chain data dictionary
        
    Returns:
        True if successful
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if "yes_shares" in onchain_data:
            updates.append("yes_shares = ?")
            values.append(onchain_data["yes_shares"])
        
        if "no_shares" in onchain_data:
            updates.append("no_shares = ?")
            values.append(onchain_data["no_shares"])
        
        if "is_resolved" in onchain_data or "resolved" in onchain_data:
            updates.append("is_resolved = ?")
            values.append(1 if onchain_data.get("is_resolved") or onchain_data.get("resolved") else 0)
        
        if "outcome" in onchain_data:
            updates.append("outcome = ?")
            values.append(onchain_data["outcome"])
        
        if "probability" in onchain_data:
            updates.append("probability = ?")
            values.append(onchain_data["probability"])
        
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(market_id)
            
            cursor.execute(f"""
                UPDATE markets 
                SET {', '.join(updates)}
                WHERE market_id = ?
            """, values)
            
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error updating market: {e}")
        return False

# Initialize database on import
init_database()

