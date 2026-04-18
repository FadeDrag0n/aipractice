import json
from db import show_catalog, search_catalog, add_to_cart, view_cart

# ── Tool schemas ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "show_catalog",
            "description": "Показати весь каталог товарів",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Пошук товару за назвою",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Додати товар до кошика",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "Показати кошик",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ── Dispatcher ────────────────────────────────────────────────────────────────

def call_tool(name: str, args: dict, user_id: int) -> str:
    if name == "show_catalog":
        rows = show_catalog()
        if not rows:
            return "Каталог порожній"
        return "\n".join(f"{r[0]} — {r[1]} ({r[2]} грн)" for r in rows)

    if name == "search_catalog":
        rows = search_catalog(args.get("query", ""))
        if not rows:
            return "Нічого не знайдено"
        return "\n".join(f"{r[0]} — {r[1]} ({r[2]} грн)" for r in rows)

    if name == "add_to_cart":
        product_name, qty = add_to_cart(
            user_id,
            args["product_id"],
            args.get("quantity", 1),
        )
        if product_name is None:
            return qty  # error message
        return f"{product_name} додано ({qty} шт.)"

    if name == "view_cart":
        rows = view_cart(user_id)
        if not rows:
            return "Кошик порожній"
        total = 0
        lines = []
        for _, n, q, p in rows:
            total += q * p
            lines.append(f"{n} — {q} × {p} = {q * p} грн")
        lines.append(f"Разом: {total} грн")
        return "\n".join(lines)

    return "Невідомий інструмент"
