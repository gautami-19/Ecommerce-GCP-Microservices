import os
import time
import pymysql
import requests

from flask import Flask, request

app = Flask(__name__)

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "order_db"),
    "user": os.getenv("DB_USER", "order_app"),
    "password": os.getenv("DB_PASSWORD", "order_pass"),
}

PRODUCT = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:5002")
USER = os.getenv("USER_SERVICE_URL", "http://localhost:5001")


def db():
    return pymysql.connect(
        host=DB["host"],
        port=DB["port"],
        database=DB["database"],
        user=DB["user"],
        password=DB["password"],
        cursorclass=pymysql.cursors.DictCursor
    )


def init():
    for _ in range(30):
        try:
            c = db()
            x = c.cursor()

            x.execute("""
                CREATE TABLE IF NOT EXISTS cart(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            x.execute("""
                CREATE TABLE IF NOT EXISTS orders(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    total DECIMAL(10,2) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'PLACED',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            x.execute("""
                CREATE TABLE IF NOT EXISTS order_items(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL,
                    price DECIMAL(10,2) NOT NULL
                )
            """)

            c.commit()
            x.close()
            c.close()
            return

        except Exception:
            time.sleep(2)


def product(i):
    try:
        r = requests.get(
            f"{PRODUCT}/products/{i}",
            timeout=5
        )

        if r.ok:
            return r.json()

        return None

    except requests.RequestException:
        return None


@app.get("/health")
def health():
    return {
        "service": "cart-order-service",
        "status": "running"
    }


@app.get("/cart/<int:u>")
def cart(u):
    c = db()
    x = c.cursor()

    x.execute(
        "SELECT id, product_id, quantity FROM cart WHERE user_id=%s",
        (u,)
    )

    rows = x.fetchall()

    x.close()
    c.close()

    out = []

    for z in rows:
        p = product(z["product_id"])

        if p:
            out.append({
                "id": z["id"],
                "product_id": z["product_id"],
                "name": p["name"],
                "price": float(p["price"]),
                "quantity": z["quantity"]
            })

    return out


@app.post("/cart")
def add():
    d = request.get_json() or {}

    u = d.get("user_id")
    p = d.get("product_id")
    q = int(d.get("quantity", 1))

    try:
        response = requests.get(
            f"{USER}/users/{u}",
            timeout=5
        )

        if not response.ok:
            return {"message": "User does not exist"}, 400

    except requests.RequestException:
        return {"message": "User service unavailable"}, 503

    if not product(p):
        return {"message": "Product not found"}, 404

    c = db()
    x = c.cursor()

    x.execute(
        "SELECT id FROM cart WHERE user_id=%s AND product_id=%s",
        (u, p)
    )

    existing = x.fetchone()

    if existing:
        x.execute(
            "UPDATE cart SET quantity=quantity+%s WHERE id=%s",
            (q, existing["id"])
        )
    else:
        x.execute(
            """
            INSERT INTO cart(user_id, product_id, quantity)
            VALUES(%s, %s, %s)
            """,
            (u, p, q)
        )

    c.commit()

    x.close()
    c.close()

    return {"message": "Added to cart"}


@app.post("/cart/remove/<int:i>")
def remove(i):
    c = db()
    x = c.cursor()

    x.execute(
        "DELETE FROM cart WHERE id=%s",
        (i,)
    )

    c.commit()

    x.close()
    c.close()

    return {"message": "Removed"}


@app.post("/checkout")
def checkout():
    u = (request.get_json() or {}).get("user_id")

    c = db()
    x = c.cursor()

    x.execute(
        "SELECT product_id, quantity FROM cart WHERE user_id=%s",
        (u,)
    )

    items = x.fetchall()

    if not items:
        x.close()
        c.close()
        return {"message": "Cart is empty"}, 400

    total = 0
    details = []

    for z in items:
        p = product(z["product_id"])

        if not p:
            x.close()
            c.close()
            return {"message": "A product is unavailable"}, 400

        price = float(p["price"])

        total += price * z["quantity"]

        details.append(
            (
                z["product_id"],
                z["quantity"],
                price
            )
        )

    x.execute(
        """
        INSERT INTO orders(user_id, total, status)
        VALUES(%s, %s, %s)
        """,
        (u, total, "PLACED")
    )

    order_id = x.lastrowid

    for p, q, price in details:
        x.execute(
            """
            INSERT INTO order_items(
                order_id,
                product_id,
                quantity,
                price
            )
            VALUES(%s, %s, %s, %s)
            """,
            (order_id, p, q, price)
        )

    x.execute(
        "DELETE FROM cart WHERE user_id=%s",
        (u,)
    )

    c.commit()

    x.close()
    c.close()

    return {
        "message": "Order placed",
        "order_id": order_id,
        "total": total
    }, 201


@app.get("/orders/<int:user_id>")
def orders(user_id):
    c = db()
    x = c.cursor()

    x.execute(
        "SELECT id,total,status,created_at FROM orders WHERE user_id=%s ORDER BY id DESC",
        (user_id,)
    )

    r = x.fetchall()

    for order in r:
        order["total"] = float(order["total"])

    x.close()
    c.close()

    return r


if __name__ == "__main__":
    init()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5003))
    )