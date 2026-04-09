from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import mysql.connector
import uuid
import random
import hashlib
import secrets

# -------------------- APP INIT --------------------
app = Flask(__name__)
app.secret_key = secrets.token_hex(24)  # Secure secret key for sessions

# -------------------- DATABASE CONNECTION --------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="inmba"
)
cursor = db.cursor(dictionary=True)

# -------------------- ROUTES --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/membership')
def membership():
    return render_template('membership.html')

@app.route('/commercial')
def commercial():
    return render_template('commercial.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/programs')
def programs():
    return render_template('programs.html')

@app.route('/foundation')
def foundation():
    return render_template('foundation.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/organization')
def organization():
    return render_template('organization.html')

@app.route('/network')
def network():
    return render_template('network.html')

# -------------------- MEMBER REGISTRATION --------------------
@app.route("/register", methods=["POST"])
def register():
    # Generate unique login ID
    def generate_unique_login_id():
        while True:
            login_id = str(random.randint(1000000, 9999999))
            cursor.execute("SELECT id FROM kyc_members WHERE login_id=%s", (login_id,))
            if not cursor.fetchone():
                return login_id

    login_id = generate_unique_login_id()
    token = str(uuid.uuid4())

    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    dob = request.form.get('dob')
    email = request.form.get('email')
    phone = request.form.get('phone')
    state = request.form.get('state')
    district = request.form.get('district')
    city = request.form.get('city')
    pincode = request.form.get('pincode')
    gender = request.form.get('gender')
    marital_status = request.form.get('marital_status')
    nationality = request.form.get('nationality')
    occupation = request.form.get('occupation')
    education = request.form.get('education')
    membership_type = request.form.get('membership_type')
    aadhar = request.form.get('aadhar')
    password = request.form.get('password')

    # Hash password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Check Aadhar uniqueness within 14 days
    if aadhar:
        cursor.execute(
            "SELECT created_at FROM kyc_members WHERE aadhar=%s ORDER BY created_at DESC LIMIT 1",
            (aadhar,)
        )
        result = cursor.fetchone()
        if result:
            last_used = result["created_at"]
            if datetime.now() - last_used < timedelta(days=14):
                return "❌ This Aadhar was registered recently. Try after 14 days."

    # Check phone usage limit
    cursor.execute("SELECT COUNT(*) AS count FROM kyc_members WHERE phone=%s", (phone,))
    phone_count = cursor.fetchone()['count']
    if phone_count >= 3:
        return "❌ This phone number is already used 3 times. You cannot register more."

    # Insert into DB
    sql = """
    INSERT INTO kyc_members
    (first_name, last_name, dob, email, phone, state, district, city, pincode,
     gender, marital_status, nationality, occupation, education, membership_type,
     aadhar, token, login_id, password, created_at)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW())
    """
    values = (
        first_name, last_name, dob, email, phone, state, district, city, pincode,
        gender, marital_status, nationality, occupation, education,
        membership_type, aadhar, token, login_id, hashed_password
    )
    cursor.execute(sql, values)
    db.commit()

    link = url_for('login', _external=True)
    return f"✅ KYC Submitted! Your Login ID: <b>{login_id}</b> <br>Go to <a href='{link}'>Login</a>"

# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get('login_id')
        password = request.form.get('password')
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute(
            "SELECT * FROM kyc_members WHERE login_id=%s AND password=%s",
            (login_id, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            session['user'] = user
            return redirect(url_for('dashboard'))  # ✅ direct dashboard
        else:
            return "❌ Invalid Login ID or Password"

    return render_template("login.html")

# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    return render_template("dashboard.html", user=user)
@app.route("/policy")
def policy():
    return render_template("policy.html")

@app.route('/accept_policy', methods=['POST'])
def accept_policy():
    session['policy_accepted'] = True
    return redirect(url_for('payment'))

@app.route('/logout')
def logout():
    session.pop('user', None)   # remove user from session
    return redirect(url_for('login'))  # go back to login page
# -------------------- VIEW ALL MEMBERS --------------------
@app.route('/payment_submit', methods=['POST'])
def payment_submit():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Get data from the payment form
    transaction_id = request.form.get('transaction_id')
    subscription_year = request.form.get('subscription_year')
    payment_method = request.form.get('payment_method')

    if not transaction_id or not subscription_year or not payment_method:
        return "❌ All fields are required!"

    user = session['user']

    # Save payment info in DB
    cursor.execute("""
        UPDATE kyc_members
        SET transaction_id=%s, subscription_year=%s, payment_method=%s
        WHERE id=%s
    """, (transaction_id, subscription_year, payment_method, user['id']))
    db.commit()

    # Redirect to bank details page using user's token
    token = user['token']
    return redirect(url_for('bank_form', token=token))
@app.route("/members")
def members():
    cursor.execute("SELECT * FROM kyc_members")
    data = cursor.fetchall()
    return render_template("members.html", members=data)
@app.route('/payment')
def payment():
    return render_template('payment.html')
# -------------------- BANK DETAILS --------------------
@app.route("/bank/<token>")
def bank_form(token):
    # Get user info from token
    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    user = cursor.fetchone()
    if not user:
        return "❌ Invalid token!"

    return render_template("bank.html", token=token)

@app.route("/bank_submit/<token>", methods=["POST"])
def bank_submit(token):
    bank_name = request.form.get('bank_name')
    account_holder = request.form.get('account_holder')
    account_number = request.form.get('account_number1')

    if not bank_name or not account_holder or not account_number:
        return "❌ All fields are required!"

    # Update bank info in DB
    cursor.execute("""
        UPDATE kyc_members
        SET bank_name=%s, account_holder=%s, account_number=%s
        WHERE token=%s
    """, (bank_name, account_holder, account_number, token))
    db.commit()

    # Redirect to next page (e.g., legal entity or dashboard)
    return redirect(url_for('dashboard'))

# -------------------- ADMIN --------------------
@app.route("/admin")
def admin():
    cursor.execute("SELECT * FROM kyc_members ORDER BY id DESC")
    users = cursor.fetchall()
    return render_template("admin.html", users=users)

@app.route("/delete/<int:id>")
def delete(id):
    cursor.execute("DELETE FROM kyc_members WHERE id=%s", (id,))
    db.commit()
    return redirect(url_for('admin'))
@app.route('/bank-details', methods=['GET', 'POST'])
def bank_details():
    if request.method == 'POST':
        bank_name = request.form['bank_name']
        account_holder = request.form['account_holder']
        account_number = request.form['account_number1']
        # Save in DB
        db.cursor().execute("""
            UPDATE kyc_members SET bank_name=%s, account_holder=%s, account_number=%s
            WHERE transaction_id=(SELECT MAX(transaction_id) FROM kyc_members)
        """, (bank_name, account_holder, account_number))
        db.commit()
        return "Bank details submitted! Admin will verify."
    return render_template('bank_details.html')

# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(debug=True)