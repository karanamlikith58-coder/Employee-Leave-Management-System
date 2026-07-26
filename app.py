from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "employee_secret_key"


# ---------------- DATABASE ---------------- #

def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Employee Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        department TEXT,
        password TEXT
    )
    """)

    # Leave Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leaves(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_name TEXT,
        leave_type TEXT,
        from_date TEXT,
        to_date TEXT,
        reason TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    conn.close()


create_database()


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        department = request.form["department"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Check duplicate email
        cursor.execute(
            "SELECT * FROM employees WHERE email=?",
            (email,)
        )

        existing = cursor.fetchone()

        if existing:
            conn.close()
            return render_template(
                "register.html",
                error="Email already exists"
            )

        cursor.execute(
            "INSERT INTO employees(name,email,department,password) VALUES(?,?,?,?)",
            (name, email, department, password)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM employees WHERE email=?",
            (email,)
        )

        employee = cursor.fetchone()

        conn.close()

        if employee and check_password_hash(employee[4], password):
            session["employee"] = employee[1]
            return redirect(url_for("dashboard"))
        else:
            return render_template(
                "login.html",
                error="Invalid Email or Password"
            )

    return render_template("login.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "employee" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM leaves WHERE employee_name=?",
        (session["employee"],)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM leaves WHERE employee_name=? AND status='Pending'",
        (session["employee"],)
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM leaves WHERE employee_name=? AND status='Approved'",
        (session["employee"],)
    )
    approved = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM leaves WHERE employee_name=? AND status='Rejected'",
        (session["employee"],)
    )
    rejected = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        name=session["employee"],
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected
    )

    # ---------------- PROFILE ---------------- #

# ---------------- PROFILE ---------------- #

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "employee" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        department = request.form["department"]

        cursor.execute(
            """
            UPDATE employees
            SET name=?, email=?, department=?
            WHERE name=?
            """,
            (name, email, department, session["employee"])
        )

        conn.commit()

        # Update session if name changes
        session["employee"] = name

    cursor.execute(
        "SELECT name, email, department FROM employees WHERE name=?",
        (session["employee"],)
    )

    employee = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        employee=employee
    )


# ---------------- APPLY LEAVE ---------------- #

@app.route("/apply_leave", methods=["GET", "POST"])
def apply_leave():

    if "employee" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        leave_type = request.form["leave_type"]
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        reason = request.form["reason"]
        if from_date > to_date:
            return render_template(
                "apply_leave.html",
                error="From Date cannot be later than To Date."
            )   

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO leaves
            (employee_name, leave_type, from_date, to_date, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["employee"],
                leave_type,
                from_date,
                to_date,
                reason
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("apply_leave.html")


# ---------------- LEAVE HISTORY ---------------- #

@app.route("/leave_history")
def leave_history():

    if "employee" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM leaves WHERE employee_name=?",
        (session["employee"],)
    )

    leaves = cursor.fetchall()

    conn.close()

    return render_template(
        "leave_history.html",
        leaves=leaves
    )

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = "Admin"
            return redirect(url_for("admin"))

        return render_template(
            "admin_login.html",
            error="Invalid Username or Password"
        )

    return render_template("admin_login.html")


# ---------------- ADMIN LOGOUT ---------------- #

@app.route("/admin_logout")
def admin_logout():

    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# ---------------- ADMIN PANEL ---------------- #

# ---------------- ADMIN PANEL ---------------- #

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "")
    status = request.args.get("status", "All")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Dashboard Statistics
    cursor.execute("SELECT COUNT(*) FROM leaves")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leaves WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leaves WHERE status='Approved'")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leaves WHERE status='Rejected'")
    rejected = cursor.fetchone()[0]

    # Search & Filter
    query = "SELECT * FROM leaves WHERE employee_name LIKE ?"
    params = [f"%{search}%"]

    if status != "All":
        query += " AND status=?"
        params.append(status)

    cursor.execute(query, params)
    leaves = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        leaves=leaves,
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected,
        search=search,
        status=status
    )

# ---------------- APPROVE LEAVE ---------------- #

@app.route("/approve/<int:id>")
def approve(id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE leaves SET status='Approved' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ---------------- REJECT LEAVE ---------------- #

@app.route("/reject/<int:id>")
def reject(id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE leaves SET status='Rejected' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))

# ---------------- CANCEL LEAVE ---------------- #

@app.route("/cancel_leave/<int:id>")
def cancel_leave(id):

    if "employee" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM leaves
        WHERE id=? AND status='Pending'
        """,
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("leave_history"))

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)