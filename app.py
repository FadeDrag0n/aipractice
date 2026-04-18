from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from db import init_db, get_user_id, show_catalog, view_cart, clear_cart
from chat import process_message, new_session

# ── Startup / shutdown ────────────────────────────────────────────────────────

USER_ID: int = 0
_sessions: dict[int, list] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global USER_ID
    init_db()
    USER_ID = get_user_id()
    yield


app = FastAPI(title="Apple Shop API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_session(user_id: int) -> list:
    if user_id not in _sessions:
        _sessions[user_id] = new_session()
    return _sessions[user_id]


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/catalog")
def api_catalog():
    rows = show_catalog()
    return [{"id": r[0], "name": r[1], "price": r[2], "category": r[3]} for r in rows]


@app.get("/api/cart")
def api_cart():
    rows = view_cart(USER_ID)
    items = [{"id": r[0], "name": r[1], "qty": r[2], "price": r[3]} for r in rows]
    total = sum(r["qty"] * r["price"] for r in items)
    return {"items": items, "total": total}


@app.delete("/api/cart")
def api_clear_cart():
    clear_cart(USER_ID)
    return {"ok": True}


@app.post("/api/chat")
async def api_chat(body: ChatRequest):
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty message")
    messages = get_session(USER_ID)
    reply = await process_message(messages, text, USER_ID)
    return {"reply": reply}


@app.post("/api/chat/reset")
def api_reset():
    _sessions.pop(USER_ID, None)
    return {"ok": True}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)