import os
import time
import pymysql

from flask import Flask

app = Flask(__name__)

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "product_db"),
    "user": os.getenv("DB_USER", "product_app"),
    "password": os.getenv("DB_PASSWORD", "product_pass")
}


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
                CREATE TABLE IF NOT EXISTS products(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    stock INT NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            x.execute("SELECT COUNT(*) AS count FROM products")

            if x.fetchone()["count"] == 0:
                x.executemany(
                    """
                    INSERT INTO products(
                        name,
                        description,
                        price,
                        stock
                    )
                    VALUES(%s, %s, %s, %s)
                    """,
                    [
                        (
                            "Laptop",
                            "Student laptop",
                            55000,
                            10
                        ),
                        (
                            "Wireless Mouse",
                            "Comfortable wireless mouse",
                            799,
                            25
                        ),
                        (
                            "Keyboard",
                            "USB mechanical keyboard",
                            1999,
                            15
                        ),
                        (
                            "Headphones",
                            "Wireless headphones",
                            2499,
                            20
                        )
                    ]
                )

            c.commit()

            x.close()
            c.close()

            return

        except Exception:
            time.sleep(2)


@app.get("/health")
def health():
    return {
        "service": "product-service",
        "status": "running"
    }


@app.get("/products")
def products():
    c = db()
    x = c.cursor()
    x.execute("SELECT id,name,description,price,stock FROM products ORDER BY id")
    r = x.fetchall()

    for product in r:
        product["price"] = float(product["price"])

    x.close()
    c.close()
    return r


@app.get("/products/<int:i>")
def product(i):
    c = db()
    x = c.cursor()
    x.execute(
        "SELECT id,name,description,price,stock FROM products WHERE id=%s",
        (i,)
    )
    r = x.fetchone()

    if r:
        r["price"] = float(r["price"])

    x.close()
    c.close()

    return r if r else {"message": "Product not found"}, (200 if r else 404)

if __name__ == "__main__":
    init()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5002))
    )