from flask import Flask, render_template, request, redirect, session
from database import get_connection

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- HOME / LOGIN PAGE ----------------
@app.route('/')
def home():
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        # Backend validation
        if not username or not password or not role:
            return "All fields are required"

        con = get_connection()
        cur = con.cursor()

        # Check if username already exists
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            con.close()
            return "Username already exists"

        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, password, role)
        )
        con.commit()
        con.close()

        return redirect('/')

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return "Username and Password required"

    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cur.fetchone()
    con.close()

    if user:
        session.clear()  # clear old session
        session['user_id'] = user['id']
        session['role'] = user['role']

        if user['role'] == 'admin':
            return redirect('/admin')
        else:
            return redirect('/user')
    else:
        return "Invalid Username or Password"

# ---------------- USER DASHBOARD ----------------
@app.route('/user')
def user_dashboard():
    if 'role' in session and session['role'] == 'user':
        return render_template("user_dashboard.html")
    return redirect('/')

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT incidents.id, users.username, title, category, priority, status, created_at
        FROM incidents
        JOIN users ON incidents.user_id = users.id
        ORDER BY incidents.id DESC
    """)
    incidents = cur.fetchall()
    con.close()

    return render_template("admin_dashboard.html", incidents=incidents)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/raise_incident', methods=['GET', 'POST'])
def raise_incident():
    if 'role' not in session or session['role'] != 'user':
        return redirect('/')

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        priority = request.form.get('priority')

        if not title or not description or not category or not priority:
            return "All fields required"

        con = get_connection()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO incidents (user_id, title, description, category, priority, status) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (session['user_id'], title, description, category, priority, "Open")
        )
        con.commit()
        con.close()

        return redirect('/user')

    return render_template("raise_incident.html")

@app.route('/update_status/<int:incident_id>', methods=['POST'])
def update_status(incident_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    new_status = request.form.get('status')

    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "UPDATE incidents SET status=%s WHERE id=%s",
        (new_status, incident_id)
    )
    con.commit()
    con.close()

    return redirect('/admin')

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)