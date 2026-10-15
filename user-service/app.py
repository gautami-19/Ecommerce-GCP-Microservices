import os
import time
import pymysql

from flask import Flask, request

app = Flask(__name__)

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "user_db"),
    "user": os.getenv("DB_USER", "user_app"),
    "password": os.getenv("DB_PASSWORD", "user_pass")
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
                CREATE TABLE IF NOT EXISTS users(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(150) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            c.commit()
            x.close()
            c.close()
            return

        except Exception:
            time.sleep(2)


@app.get("/health")
def health():
    return {
        "service": "user-service",
        "status": "running"
    }


@app.post("/register")
def register():
    d = request.get_json() or {}

    if not all(d.get(k) for k in ["name", "email", "password"]):
        return {"message": "All fields are required"}, 400

    try:
        c = db()
        x = c.cursor()

        x.execute(
            """
            INSERT INTO users(name, email, password)
            VALUES(%s, %s, %s)
            """,
            (d["name"], d["email"], d["password"])
        )

        c.commit()

        i = x.lastrowid

        x.close()
        c.close()

        return {
            "id": i,
            "name": d["name"],
            "email": d["email"]
        }, 201

    except Exception:
        return {
            "message": "Email already exists or database error"
        }, 400


@app.post("/login")
def login():
    d = request.get_json() or {}

    c = db()
    x = c.cursor()

    x.execute(
        "SELECT id, name, email, password FROM users WHERE email=%s",
        (d.get("email"),)
    )

    u = x.fetchone()

    x.close()
    c.close()

    if not u or u["password"] != d.get("password"):
        return {
            "message": "Invalid email or password"
        }, 401

    u.pop("password")

    return u


@app.get("/users/<int:i>")
def user(i):
    c = db()
    x = c.cursor()

    x.execute(
        "SELECT id, name, email FROM users WHERE id=%s",
        (i,)
    )

    u = x.fetchone()

    x.close()
    c.close()

    if u:
        return u

    return {
        "message": "User not found"
    }, 404


if __name__ == "__main__":
    init()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5001))
    )