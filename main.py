import asyncio
import sqlite3
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

CURRENT_USER = "vasyl"
DB_PATH = "shop.db"

client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = "llama-3.3-70b-versatile"

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

    products = [
        ("p001","iPhone 15 Pro",42999,"Смартфони"),
        ("p002","MacBook Air M3",54999,"Ноутбуки"),
        ("p003","AirPods Pro 2",8999,"Навушники"),
        ("p004","iPad mini 7",19999,"Планшети"),
        ("p005","Apple Watch Series 10",14999,"Годинники"),
    ]

    cur.executemany(
        "INSERT OR IGNORE INTO products VALUES (?,?,?,?)",
        products
    )

    cur.execute("INSERT OR IGNORE INTO users (name) VALUES (?)", (CURRENT_USER,))
    conn.commit()
    conn.close()

def get_user_id():
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE name=?", (CURRENT_USER,)).fetchone()
    conn.close()
    return row[0]

USER_ID = None

def show_catalog():
    conn = get_conn()
    rows = conn.execute("SELECT id,name,price FROM products").fetchall()
    conn.close()
    return "\n".join([f"{i} — {n} ({p} грн)" for i,n,p in rows])

def search_catalog(query):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,name,price FROM products WHERE name LIKE ?",
        (f"%{query}%",)
    ).fetchall()
    conn.close()
    if not rows:
        return "Нічого не знайдено"
    return "\n".join([f"{i} — {n} ({p} грн)" for i,n,p in rows])

def add_to_cart(product_id, quantity=1):
    conn = get_conn()
    product = conn.execute("SELECT name,price FROM products WHERE id=?", (product_id,)).fetchone()

    if not product:
        return "Товар не знайдено"

    conn.execute(
        "INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,?) "
        "ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + ?",
        (USER_ID, product_id, quantity, quantity)
    )
    conn.commit()
    conn.close()
    return f"{product[0]} додано ({quantity} шт.)"

def view_cart():
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.name, c.quantity, p.price
        FROM cart c JOIN products p ON c.product_id=p.id
        WHERE c.user_id=?
    """, (USER_ID,)).fetchall()
    conn.close()

    if not rows:
        return "Кошик порожній"

    total = 0
    lines = []
    for n,q,p in rows:
        total += q*p
        lines.append(f"{n} — {q} × {p} = {q*p}")

    lines.append(f"Разом: {total}")
    return "\n".join(lines)

tools = [
    {
        "type": "function",
        "function": {
            "name": "show_catalog",
            "description": "Показати каталог",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Пошук товару",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Додати товар",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "quantity": {"type": "integer"}
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "Показати кошик",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def call_tool(name, args):
    if name == "show_catalog":
        return show_catalog()
    if name == "search_catalog":
        return search_catalog(**args)
    if name == "add_to_cart":
        return add_to_cart(**args)
    if name == "view_cart":
        return view_cart()
    return "Помилка tool"

async def chat():
    global USER_ID

    init_db()
    USER_ID = get_user_id()

    messages = [
        {
            "role": "system",
            "content": "Ти асистент інтернет-магазину. Відповідай коротко."
        }
    ]

    while True:
        user = input("\n> ")

        if user in ("exit","/exit"):
            break

        messages.append({"role": "user", "content": user})

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            for call in msg.tool_calls:
                name = call.function.name
                args = json.loads(call.function.arguments)

                result = call_tool(name, args)

                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })

            response = await client.chat.completions.create(
                model=MODEL,
                messages=messages
            )

            msg = response.choices[0].message

        print("\n🤖", msg.content)
        messages.append({"role": "assistant", "content": msg.content})


if __name__ == "__main__":
    asyncio.run(chat())