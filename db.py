import sqlite3

DB_PATH = "shop.db"
CURRENT_USER = "vasyl"

PRODUCTS = [
    ("p001", "iPhone 15 Pro", 42999, "Смартфони"),
    ("p002", "MacBook Air M3", 54999, "Ноутбуки"),
    ("p003", "AirPods Pro 2", 8999, "Навушники"),
    ("p004", "iPad mini 7", 19999, "Планшети"),
    ("p005", "Apple Watch Series 10", 14999, "Годинники"),
]


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id TEXT,
            quantity INTEGER DEFAULT 1,
            UNIQUE(user_id, product_id)
        );
    """)
    cur.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?)", PRODUCTS)
    cur.execute("INSERT OR IGNORE INTO users (name) VALUES (?)", (CURRENT_USER,))
    conn.commit()
    conn.close()


def get_user_id():
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE name=?", (CURRENT_USER,)).fetchone()
    conn.close()
    return row[0]


# ── Catalog ──────────────────────────────────────────────────────────────────

def show_catalog():
    conn = get_conn()
    rows = conn.execute("SELECT id,name,price,category FROM products").fetchall()
    conn.close()
    return rows  # list of tuples


def search_catalog(query: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,name,price,category FROM products WHERE name LIKE ?",
        (f"%{query}%",),
    ).fetchall()
    conn.close()
    return rows


# ── Cart ─────────────────────────────────────────────────────────────────────

def add_to_cart(user_id: int, product_id: str, quantity: int = 1):
    conn = get_conn()
    product = conn.execute(
        "SELECT name,price FROM products WHERE id=?", (product_id,)
    ).fetchone()
    if not product:
        conn.close()
        return None, "Товар не знайдено"
    conn.execute(
        "INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,?) "
        "ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + ?",
        (user_id, product_id, quantity, quantity),
    )
    conn.commit()
    conn.close()
    return product[0], quantity


def view_cart(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT p.id, p.name, c.quantity, p.price
        FROM cart c JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return rows  # list of (id, name, qty, price)


def clear_cart(user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
