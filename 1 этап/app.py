from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key_123"  # нужен для сессий

# ---------------------------
# БАЗА ДАННЫХ
# ---------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # пользователи
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------------------
# ГЛАВНАЯ СТРАНИЦА
# ---------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return render_template("index.html", user=session["username"])
    return redirect(url_for("login"))

# ---------------------------
# РЕГИСТРАЦИЯ
# ---------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                        (username, password))
            conn.commit()
        except:
            return "Такой пользователь уже существует"

        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------------------
# ВХОД
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                    (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("index"))
        else:
            return "Неверный логин или пароль"

    return render_template("login.html")

# ---------------------------
# ВЫХОД
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------------
# ЗАПУСК
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)