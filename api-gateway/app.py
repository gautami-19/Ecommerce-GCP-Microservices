import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

USER_SERVICE = os.getenv("USER_SERVICE_URL", "http://localhost:5001")
PRODUCT_SERVICE = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:5002")
CART_ORDER_SERVICE = os.getenv("CART_ORDER_SERVICE_URL", "http://localhost:5003")

def get(url):
    try:
        return requests.get(url, timeout=5)
    except requests.RequestException:
        return None

def post(url, data=None):
    try:
        return requests.post(url, json=data, timeout=5)
    except requests.RequestException:
        return None

@app.route("/")
def index():
    r = get(f"{PRODUCT_SERVICE}/products")
    products = r.json() if r and r.ok else []
    return render_template("index.html", products=products)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        r = post(f"{USER_SERVICE}/register", {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"]
        })
        if r and r.ok:
            flash("Registration successful. Please login.")
            return redirect(url_for("login"))
        flash(r.json().get("message", "Registration failed") if r else "User service unavailable")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        r = post(f"{USER_SERVICE}/login", {
            "email": request.form["email"],
            "password": request.form["password"]
        })
        if r and r.ok:
            user = r.json()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("index"))
        flash(r.json().get("message", "Invalid login") if r else "User service unavailable")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))
    r = get(f"{CART_ORDER_SERVICE}/cart/{session['user_id']}")
    items = r.json() if r and r.ok else []
    total = sum(float(x["price"]) * int(x["quantity"]) for x in items)
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_cart(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    post(f"{CART_ORDER_SERVICE}/cart", {
        "user_id": session["user_id"],
        "product_id": product_id,
        "quantity": 1
    })
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove_cart(item_id):
    post(f"{CART_ORDER_SERVICE}/cart/remove/{item_id}")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["POST"])
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))
    r = post(f"{CART_ORDER_SERVICE}/checkout", {"user_id": session["user_id"]})
    flash(r.json().get("message", "Checkout failed") if r else "Order service unavailable")
    return redirect(url_for("orders"))

@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))
    r = get(f"{CART_ORDER_SERVICE}/orders/{session['user_id']}")
    orders = r.json() if r and r.ok else []
    return render_template("orders.html", orders=orders)

@app.route("/health")
def health():
    return {"service": "api-gateway", "status": "running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
