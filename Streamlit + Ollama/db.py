import streamlit as st
import sqlite3
from Bill import Bill
import pandas as pd
from Transaction import Transaction
from config import DB_PATH




def initialize_db():
    """Creates the database and table if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creditor TEXT NOT NULL, 
            date TEXT NOT NULL, 
            amount REAL NOT NULL,
            recurring INTEGER DEFAULT 0,
            bill_hash TEXT UNIQUE
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trans_date TEXT NOT NULL,
        creditor TEXT,
        amount REAL NOT NULL,
        balance REAL,
        category TEXT,
        trans_hash TEXT UNIQUE
    )
    """)
    conn.commit()
    conn.close()
    
def get_transactions():
    """Retrieves all transactions from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()

    transactions = []
    for row in rows:
        transaction = Transaction(
            trans_date=row[1],
            creditor=row[2],
            amount=row[3],
            balance=row[4],
            category=row[5]
        )
        transactions.append(transaction)
    conn.close()
    return transactions


    
def import_statement_xlsx(filepath):
    df = pd.read_excel(filepath, header=4)

    st.write("Columns in file:", df.columns.tolist())
    st.write("Preview of data:", df.head())

    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        trans_date = row.get("Dags")
        if pd.notnull(trans_date) and isinstance(trans_date, pd.Timestamp):
            trans_date = trans_date.strftime("%Y-%m-%d")
        creditor       = row.get("Texti")
        amount     = row.get("Upphæð", 0)
        balance    = row.get("Staða")
        category   = row.get("Textalykill")
        
        transaction = Transaction(trans_date, creditor, amount, balance, category)
        
        cursor.execute("""
            INSERT OR IGNORE INTO transactions (trans_date, creditor, amount, balance, category, trans_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            transaction.trans_date,
            transaction.creditor,
            transaction.amount,
            transaction.balance,
            transaction.category,
            transaction.trans_hash
        ))
    
    conn.commit()
    conn.close()

def save_bill(bill):
    """Saves a bill to the database, avoiding duplicates."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO bills (id, creditor, date, amount, recurring)
        VALUES (?, ?, ?, ?, ?)
    """, (bill.id, bill.creditor, bill.date, bill.amount, int(bill.recurring)))

    conn.commit()
    conn.close()
    
def get_bills():
    """Retrieves all bills from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bills")
    rows = cursor.fetchall()

    bills = []
    for row in rows:
        bill = Bill(
            creditor=row[1],
            date=row[2],
            amount=row[3],
            recurring=bool(row[4])
        )
        bills.append(bill)

    conn.close()
    return bills

def update_bill_recurring_status(bill_id, new_status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE bills SET recurring = ? WHERE id = ?", (new_status, bill_id))
    conn.commit()
    conn.close()
    
def delete_bill(bill_id):
    """Deletes a bill from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    conn.commit()
    conn.close()
    
