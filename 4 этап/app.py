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

    # опросы
    cur.execute("""
    CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        user_id INTEGER
    )
    """)

    # варианты ответов
    cur.execute("""
    CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER,
        option_text TEXT
    )
    """)

    # голоса
    cur.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        poll_id INTEGER,
        option_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

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

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM polls WHERE user_id=?",
                (session["user_id"],))
    polls = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", polls=polls)

@app.route("/create_poll", methods=["GET", "POST"])
def create_poll():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        options = request.form.getlist("options")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("INSERT INTO polls (title, user_id) VALUES (?, ?)",
                    (title, session["user_id"]))
        poll_id = cur.lastrowid

        for opt in options:
            if opt.strip():
                cur.execute("INSERT INTO options (poll_id, option_text) VALUES (?, ?)",
                            (poll_id, opt))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("create_poll.html")

@app.route("/poll/<int:poll_id>")
def poll(poll_id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM polls WHERE id=?", (poll_id,))
    poll = cur.fetchone()

    cur.execute("SELECT * FROM options WHERE poll_id=?", (poll_id,))
    options = cur.fetchall()

    conn.close()

    return render_template("poll.html", poll=poll, options=options)

@app.route("/vote/<int:option_id>/<int:poll_id>")
def vote(option_id, poll_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # проверка: голосовал ли уже
    cur.execute("""
        SELECT * FROM votes 
        WHERE user_id=? AND poll_id=?
    """, (session["user_id"], poll_id))

    already_voted = cur.fetchone()

    if not already_voted:
        cur.execute("""
            INSERT INTO votes (user_id, poll_id, option_id)
            VALUES (?, ?, ?)
        """, (session["user_id"], poll_id, option_id))

        conn.commit()

    conn.close()

    return redirect(url_for("results", poll_id=poll_id))

@app.route("/results/<int:poll_id>")
def results(poll_id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT title FROM polls WHERE id=?", (poll_id,))
    poll = cur.fetchone()

    cur.execute("""
        SELECT options.option_text, COUNT(votes.id)
        FROM options
        LEFT JOIN votes ON options.id = votes.option_id
        WHERE options.poll_id=?
        GROUP BY options.id
    """, (poll_id,))

    data = cur.fetchall()
    conn.close()

    labels = [row[0] for row in data]
    values = [row[1] for row in data]

    return render_template("results.html",
                           poll=poll,
                           labels=labels,
                           values=values)

# ---------------------------
# ЗАПУСК
# ---------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)