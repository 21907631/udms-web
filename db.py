import os
import mysql.connector

def get_conn():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        autocommit=True,
    )

def fetch_all(query, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        return cur.fetchall()
    finally:
        conn.close()

def fetch_one(query, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        return cur.fetchone()
    finally:
        conn.close()

def execute(query, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        return cur.rowcount
    finally:
        conn.close()
