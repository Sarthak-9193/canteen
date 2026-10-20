"""server.py: canteen API server (port 5000).

Owns the menu, prices, orders and order status. The website only displays things
and sends requests here.

Run:  python server.py
Test: http://localhost:5000/api/menu
"""
from datetime import datetime
from threading import Lock

from flask import Flask, jsonify, request

app = Flask(__name__)

CONFIG = {
    "name": "Campus Bites",
    "location": "Main Academic Block",
    "opening_hour": 8,
    "closing_hour": 20,
    "currency": "₹",
    "cancel_window_seconds": 120,   # an order can be cancelled for this long
    "preparing_after_seconds": 30,  # "received" turns into "preparing" after this
    "base_wait_minutes": 2,
    "wait_per_active_order": 2,
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def dish(i, name, price, category, desc, veg=True, prep=5, popular=False):
    return {"id": i, "name": name, "price": price, "category": category,
            "description": desc, "veg": veg, "prep_time_minutes": prep,
            "popular": popular, "available": True}


MENU = {
    "Monday": [
        dish(101, "Upma", 25, "Breakfast", "Semolina cooked with curry leaves, mustard and vegetables", prep=4),
        dish(102, "Bread Omelette", 35, "Breakfast", "Two-egg omelette between toasted bread slices", veg=False, prep=6, popular=True),
        dish(103, "Dal Khichdi", 60, "Lunch", "Comforting rice and lentil bowl with ghee and pickle", prep=9, popular=True),
        dish(104, "Veg Frankie", 45, "Snacks", "Spiced vegetable roll with tangy mint sauce", prep=6),
        dish(105, "Filter Coffee", 20, "Beverages", "Strong South Indian style coffee with frothy milk", prep=3, popular=True),
        dish(106, "Kheer", 30, "Dessert", "Slow-cooked rice pudding with cardamom", prep=2),
    ],
    "Tuesday": [
        dish(201, "Medu Vada", 30, "Breakfast", "Crisp lentil doughnuts served with coconut chutney", prep=5, popular=True),
        dish(202, "Rava Idli", 35, "Breakfast", "Soft semolina idlis with sambar", prep=5),
        dish(203, "Kadhi Chawal", 65, "Lunch", "Tangy yogurt curry with fritters over steamed rice", prep=9),
        dish(204, "Corn Chaat", 40, "Snacks", "Sweet corn tossed with lemon, chilli and herbs", prep=4, popular=True),
        dish(205, "Jaljeera", 20, "Beverages", "Cooling cumin and mint drink", prep=2),
        dish(206, "Sooji Halwa", 25, "Dessert", "Warm semolina sweet with dry fruits", prep=3),
    ],
    "Wednesday": [
        dish(301, "Sabudana Khichdi", 40, "Breakfast", "Tapioca pearls with peanuts and potato", prep=6),
        dish(302, "Paratha Combo", 70, "Lunch", "Two mixed-veg parathas with curd and pickle", prep=9, popular=True),
        dish(303, "Egg Curry Rice", 80, "Lunch", "Egg curry in onion-tomato gravy with rice", veg=False, prep=11),
        dish(304, "Bhel Puri", 30, "Snacks", "Puffed rice, sev and chutneys", prep=3, popular=True),
        dish(305, "Buttermilk", 15, "Beverages", "Spiced chilled chaas", prep=2),
        dish(306, "Jalebi", 30, "Dessert", "Crisp syrup-soaked spirals", prep=2),
    ],
    "Thursday": [
        dish(401, "Besan Chilla", 35, "Breakfast", "Gram flour pancake with onions and herbs", prep=5),
        dish(402, "Pav Bhaji", 60, "Lunch", "Mashed vegetable curry with buttered pav", prep=8, popular=True),
        dish(403, "Veg Pulao Bowl", 65, "Lunch", "Light pulao with raita", prep=8),
        dish(404, "Aloo Tikki", 35, "Snacks", "Crisp potato patties with chutney", prep=5, popular=True),
        dish(405, "Lemon Iced Tea", 30, "Beverages", "Chilled black tea with lemon", prep=2),
        dish(406, "Choco Lava Cup", 45, "Dessert", "Warm chocolate sponge with molten centre", prep=4),
    ],
    "Friday": [
        dish(501, "Poha Jalebi", 40, "Breakfast", "Indori style poha with a jalebi on the side", prep=5, popular=True),
        dish(502, "Chicken Biryani", 110, "Lunch", "Layered dum biryani with raita", veg=False, prep=12, popular=True),
        dish(503, "Paneer Biryani", 95, "Lunch", "Fragrant rice with marinated paneer", prep=11),
        dish(504, "Masala Fries", 45, "Snacks", "Fries tossed in chaat masala", prep=5),
        dish(505, "Mango Shake", 50, "Beverages", "Thick chilled mango milkshake", prep=3),
        dish(506, "Ras Malai", 45, "Dessert", "Soft paneer discs in saffron milk", prep=2),
    ],
    "Saturday": [
        dish(601, "Chole Kulcha", 55, "Breakfast", "Spiced chickpeas with soft kulcha", prep=7, popular=True),
        dish(602, "Veg Fried Rice", 70, "Lunch", "Wok-tossed rice with vegetables", prep=8),
        dish(603, "Schezwan Noodles", 75, "Lunch", "Fiery stir-fried noodles", prep=8, popular=True),
        dish(604, "Mixed Pakora", 40, "Snacks", "Assorted vegetable fritters", prep=5),
        dish(605, "Cutting Chai", 10, "Beverages", "Small, strong, sweet tea", prep=2, popular=True),
        dish(606, "Gulab Jamun", 25, "Dessert", "Warm milk dumplings in syrup", prep=2),
    ],
}

ORDERS = {}
NEXT_ID = 1001
LOCK = Lock()


# ---------------------------------------------------------------- helpers
def today():
    return datetime.now().strftime("%A")


def find_dish(item_id, day=None):
    for d in MENU.get(day or today(), []):
        if d["id"] == item_id:
            return d
    return None


def is_open():
    return CONFIG["opening_hour"] <= datetime.now().hour < CONFIG["closing_hour"]


def refresh(order):
    """Move an order through received -> preparing -> ready based on elapsed time."""
    if order["status"] in ("cancelled", "picked_up"):
        return order
    placed = datetime.fromisoformat(order["placed_at"])
    elapsed = (datetime.now() - placed).total_seconds()
    ready_after = order["eta_minutes"] * 60
    if elapsed >= ready_after:
        order["status"] = "ready"
    elif elapsed >= CONFIG["preparing_after_seconds"]:
        order["status"] = "preparing"
    order["minutes_left"] = max(0, round((ready_after - elapsed) / 60))
    return order


@app.after_request
def add_cors(resp):
    origin = request.headers.get("Origin", "")
    if origin in ("http://localhost:8000", "http://127.0.0.1:8000"):
        resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


# ---------------------------------------------------------------- routes
@app.get("/api/status")
def status():
    return jsonify(name=CONFIG["name"], location=CONFIG["location"], open=is_open(),
                   opening_hour=CONFIG["opening_hour"], closing_hour=CONFIG["closing_hour"],
                   currency=CONFIG["currency"], today=today())


@app.get("/api/menu")
def menu():
    day = request.args.get("day", today())
    if day not in MENU:
        return jsonify(error=f"'{day}' is not a valid day"), 400
    return jsonify(day=day, items=MENU[day])


@app.get("/api/combos")
def combos():
    """Meal ideas: up to 3 dishes from today's menu that fit a budget."""
    try:
        budget = int(request.args.get("budget", 100))
    except ValueError:
        return jsonify(error="budget must be a number"), 400
    items = sorted(MENU[today()], key=lambda d: (not d["popular"], d["price"]))
    found = []
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            pair = [items[a], items[b]]
            if sum(x["price"] for x in pair) <= budget:
                found.append(pair)
            for c in range(b + 1, len(items)):
                trio = pair + [items[c]]
                if sum(x["price"] for x in trio) <= budget:
                    found.append(trio)
    found.sort(key=lambda g: (-len(g), -sum(x["price"] for x in g)))
    out = [{"items": [{"id": x["id"], "name": x["name"], "price": x["price"]} for x in g],
            "total": sum(x["price"] for x in g)} for g in found[:6]]
    return jsonify(budget=budget, combos=out)


@app.post("/api/orders")
def place_order():
    global NEXT_ID
    data = request.get_json(silent=True) or {}
    lines, total = [], 0
    for row in data.get("items", []):
        d = find_dish(row.get("item_id"))
        qty = row.get("quantity", 1)
        if d is None or not d["available"]:
            return jsonify(error=f"Item {row.get('item_id')} is not on today's menu"), 400
        if not isinstance(qty, int) or not 1 <= qty <= 20:
            return jsonify(error="Quantity must be between 1 and 20"), 400
        lines.append({"item_id": d["id"], "name": d["name"], "price": d["price"],
                      "quantity": qty, "line_total": d["price"] * qty})
        total += d["price"] * qty
    if not lines:
        return jsonify(error="Your order has no items"), 400

    with LOCK:
        active = sum(1 for o in ORDERS.values() if refresh(o)["status"] in ("received", "preparing"))
        slowest = max(find_dish(l["item_id"])["prep_time_minutes"] for l in lines)
        order = {
            "id": NEXT_ID, "items": lines, "total": total,
            "note": str(data.get("note", ""))[:200],
            "status": "received", "placed_at": datetime.now().isoformat(),
            "eta_minutes": CONFIG["base_wait_minutes"] + slowest + active * CONFIG["wait_per_active_order"],
        }
        ORDERS[NEXT_ID] = order
        NEXT_ID += 1
    return jsonify(refresh(order)), 201


@app.get("/api/orders/<int:order_id>")
def get_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify(error=f"Order #{order_id} not found"), 404
    return jsonify(refresh(order))


@app.post("/api/orders/<int:order_id>/cancel")
def cancel_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify(error=f"Order #{order_id} not found"), 404
    refresh(order)
    age = (datetime.now() - datetime.fromisoformat(order["placed_at"])).total_seconds()
    if order["status"] != "received" or age > CONFIG["cancel_window_seconds"]:
        return jsonify(error="This order is already being prepared and can't be cancelled"), 409
    order["status"] = "cancelled"
    return jsonify(order)


@app.post("/api/orders/<int:order_id>/pickup")
def pickup_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify(error=f"Order #{order_id} not found"), 404
    if refresh(order)["status"] != "ready":
        return jsonify(error="Order is not ready yet"), 409
    order["status"] = "picked_up"
    return jsonify(order)


@app.get("/api/summary")
def summary():
    """Small admin view: orders and revenue so far."""
    done = [o for o in ORDERS.values() if o["status"] != "cancelled"]
    return jsonify(orders=len(ORDERS), cancelled=len(ORDERS) - len(done),
                   revenue=sum(o["total"] for o in done))


if __name__ == "__main__":
    print(f"{CONFIG['name']} API running at http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
