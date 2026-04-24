from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import mysql.connector
import uuid
import random
import string
import hashlib
import secrets
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import re
import smtplib
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# -------------------- APP INIT --------------------
app = Flask(__name__)
app.secret_key = secrets.token_hex(24)  
# Secure secret key for sessions
from dotenv import load_dotenv
load_dotenv()

import os

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")

import threading

def send_email_task(email, reset_link):
    try:
        send_password_reset_email(email, reset_link)
    except Exception as e:
        print("Email thread error:", e)
UPLOAD_FOLDER_PROFILE = "static/uploads/profile"
os.makedirs(UPLOAD_FOLDER_PROFILE, exist_ok=True)

# -------------------- DATABASE CONNECTION --------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="inmba"
)
cursor = db.cursor(dictionary=True)

# -------------------- HELPER FUNCTIONS --------------------
def generate_unique_referral_id():
    existing_chars = string.ascii_uppercase + string.digits
    while True:
        referral_id = ''.join(random.choices(existing_chars, k=8))
        cursor.execute(
            "SELECT id FROM kyc_members WHERE referral_id=%s",
            (referral_id,)
        )
        results = cursor.fetchall()
        if not results:
            return referral_id


from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_referral_email(recipient_email, referral_link, referral_code):

    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=recipient_email,
        subject="Your INMBA Referral Link",
        html_content=f"""
            <h3>Your Referral is Ready</h3>
            <p>Link: <a href="{referral_link}">{referral_link}</a></p>
            <p>Code: <b>{referral_code}</b></p>
        """
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print("STATUS CODE:", response.status_code)

        if response.status_code in [200, 202]:
            return True, "Email sent via SendGrid"
        else:
            return False, f"SendGrid failed: {response.status_code}"

    except Exception as e:
        print("SENDGRID ERROR:", e)
        return False, str(e)
def generate_otp():
    return str(random.randint(100000, 999999))


def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return bool(re.match(pattern, email))


def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

def send_password_reset_email(recipient_email, reset_link):

    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=recipient_email,
        subject="INMBA Password Reset Request",
        html_content=f"""
        <div style="font-family:Arial;padding:20px;">
            <h2 style="color:#2d6a4f;">Password Reset Request</h2>

            <p>We received a request to reset your password.</p>

            <p>
                Click the button below to reset your password:
            </p>

            <a href="{reset_link}" 
               style="background:#2d6a4f;color:white;padding:10px 20px;
               text-decoration:none;border-radius:5px;display:inline-block;">
               Reset Password
            </a>

            <p style="margin-top:20px;color:red;">
                This link will expire in 30 minutes.
            </p>

            <hr>
            <p style="font-size:12px;color:gray;">
                If you did not request this, ignore this email.
            </p>
        </div>
        """
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print("STATUS CODE:", response.status_code)

        return response.status_code in [200, 202], "Reset email sent successfully"

    except Exception as e:
        print("SENDGRID ERROR:", e)
        return False, str(e)
# -------------------- ROUTES --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/membership')
def membership():
    referral_token = request.args.get('ref')
    return render_template('membership.html', referral_token=referral_token)

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

    def generate_unique_login_id():
        while True:
            login_id = str(random.randint(1000000, 9999999))
            cursor.execute("SELECT id FROM kyc_members WHERE login_id=%s", (login_id,))
            if not cursor.fetchall():
                return login_id

    login_id = generate_unique_login_id()
    token = str(uuid.uuid4())

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
    referred_by = request.form.get('referral') or None   # ← renamed
    aadhar = request.form.get('aadhar')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not is_valid_email(email):
        flash("Please enter a valid email address.")
        return render_template("membership.html", error="Invalid email format.", referral_token=referred_by)

    password_ok, password_message = is_strong_password(password)
    if not password_ok:
        flash(password_message)
        return render_template("membership.html", error=password_message, referral_token=referred_by)

    if password != confirm_password:
        message = "Password and Confirm Password do not match."
        flash(message)
        return render_template("membership.html", error=message, referral_token=referred_by)

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if phone or email:
        cursor.execute("SELECT id FROM kyc_members WHERE phone=%s OR email=%s LIMIT 1", (phone, email))
        if cursor.fetchall():
            flash("This mobile number or email is already registered. Please login.")
            return redirect(url_for("login"))

    if aadhar:
        cursor.execute("SELECT id FROM kyc_members WHERE aadhar=%s LIMIT 1", (aadhar,))
        if cursor.fetchall():
            flash("Aadhar already registered. Please login.")
            return redirect(url_for("login"))

    sql = """
    INSERT INTO kyc_members (
        first_name, last_name, dob, email, phone,
        state, district, city, pincode,
        gender, marital_status, nationality,
        occupation, education, membership_type,
        referred_by, aadhar, token, login_id, password, created_at
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """

    values = (
        first_name, last_name, dob, email, phone,
        state, district, city, pincode,
        gender, marital_status, nationality,
        occupation, education, membership_type,
        referred_by,   # ← stored in referred_by column
        aadhar, token, login_id, hashed_password
    )

    cursor.execute(sql, values)
    db.commit()

    # -------- Network strength update --------
    if referred_by:
        cursor.execute(
            "SELECT id, referred_by FROM kyc_members WHERE referral_id=%s",
            (referred_by,)
        )
        results = cursor.fetchall()
        referrer = results[0] if results else None

        if referrer:
            # Direct +1 for referrer
            cursor.execute(
                "UPDATE kyc_members SET direct_network = COALESCE(direct_network, 0) + 1 WHERE id=%s",
                (referrer['id'],)
            )
            db.commit()

            # Indirect +1 for grandparent (person who referred the referrer)
            if referrer['referred_by']:
                cursor.execute(
                    "SELECT id FROM kyc_members WHERE referral_id=%s",
                    (referrer['referred_by'],)
                )
                results = cursor.fetchall()
                grand_referrer = results[0] if results else None
                if grand_referrer:
                    cursor.execute(
                        "UPDATE kyc_members SET indirect_network = COALESCE(indirect_network, 0) + 1 WHERE id=%s",
                        (grand_referrer['id'],)
                    )
                    db.commit()

    link = url_for('login', _external=True)
    return render_template("kyc_submitted.html", login_id=login_id, login_link=link)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        if not login_id or not password:
            return render_template("login.html", error="Please provide both Login ID and password.")

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT * FROM kyc_members WHERE login_id=%s AND password=%s",
            (login_id, hashed_password)
        )
        results = cursor.fetchall()
        user = results[0] if results else None

        if not user:
            return render_template("login.html", error="Invalid login ID or password.")

        session.clear()   # ← ADD THIS: wipes any previous user's session
        user.pop("password", None)
        session["user"] = user
        session["user_token"] = user.get("token")
        return redirect(url_for("dashboard"))

    return render_template("login.html")
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":

        # 1. ALWAYS define first
        email = request.form.get("email")

        if not email:
            return render_template("forgot_password.html", error="Email required")

        if not is_valid_email(email):
            return render_template("forgot_password.html", error="Invalid email")

        # 2. check user
        cursor.execute("SELECT id FROM kyc_members WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            return render_template("forgot_password.html", error="No account found")

        # 3. generate reset token
        reset_token = uuid.uuid4().hex
        expires_at = datetime.now() + timedelta(minutes=30)

        cursor.execute("""
            UPDATE kyc_members 
            SET password_reset_token=%s, password_reset_expires=%s 
            WHERE id=%s
        """, (reset_token, expires_at, user["id"]))
        db.commit()

        reset_link = url_for("reset_password", token=reset_token, _external=True)

        # 4. THREADING (safe place)
        threading.Thread(
            target=send_email_task,
            args=(email, reset_link)
        ).start()

        flash("Reset link sent to your email!")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    cursor.execute("SELECT * FROM kyc_members WHERE password_reset_token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None
    if not user or not user.get("password_reset_expires") or user["password_reset_expires"] < datetime.now():
        flash("Password reset link is invalid or has expired.")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        password_ok, password_message = is_strong_password(password)
        if not password_ok:
            return render_template("reset_password.html", error=password_message, token=token)

        if password != confirm_password:
            error = "Password and Confirm Password do not match."
            return render_template("reset_password.html", error=error, token=token)

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "UPDATE kyc_members SET password=%s, password_reset_token=NULL, password_reset_expires=NULL WHERE id=%s",
            (hashed_password, user["id"])
        )
        db.commit()

        flash("Password updated successfully. You can now login.")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)

# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_session = session['user']
    cursor.execute("SELECT * FROM kyc_members WHERE id=%s", (user_session.get('id'),))
    results = cursor.fetchall()
    user = results[0] if results else None
    if not user:
        session.pop('user', None)
        return redirect(url_for('login'))

    if user.get('referral_id'):
        user['referral_link'] = url_for('membership', _external=True) + f"?ref={user.get('referral_id')}"

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
    session.clear()   # ← clear ALL session data, not just 'user'
    return redirect(url_for('login'))
# -------------------- VIEW ALL MEMBERS --------------------


@app.route("/members")
def members():
    cursor.execute("SELECT * FROM kyc_members")
    data = cursor.fetchall()
    return render_template("members.html", members=data)
@app.route('/payment')
def payment():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('payment.html')
@app.route("/pan/<token>")
def pan_page(token):
    return render_template("pancard.html", token=token)

@app.route('/payment_submit', methods=['POST'])
def payment_submit():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']

    transaction_id = request.form.get('transaction_id')
    subscription_year = request.form.get('subscription_year')
    payment_method = request.form.get('payment_method')

    payment_file = request.files.get("payment_proof")

    filename = None
    if payment_file and payment_file.filename:
        filename = secrets.token_hex(8) + "_" + secure_filename(payment_file.filename)
        payment_file.save("static/uploads/" + filename)
    # update payment details
    cursor.execute("""
        UPDATE kyc_members
        SET transaction_id=%s,
            subscription_year=%s,
            payment_method=%s,
            payment_proof=%s
        WHERE id=%s
    """, (transaction_id, subscription_year, payment_method, filename, user['id']))

    db.commit()

    token = session.get('user_token')
    return redirect(url_for('bank_form', token=token))
# -------------------- BANK FORM --------------------
@app.route("/bank_form/<token>")
def bank_form(token):
    # Check if token exists in DB
    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None
    if not user:
        return "❌ Invalid token!"
    return render_template("bank.html", token=token)

@app.route("/bank_submit/<token>", methods=["POST"])
def bank_submit(token):

    from werkzeug.utils import secure_filename

    # 🔍 Check user
    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None

    if not user:
        return "❌ Invalid token"

    # 📥 Form data
    account_holder = request.form.get("account_holder")
    bank_name = request.form.get("bank_name")
    acc1 = request.form.get("account_number1")
    acc2 = request.form.get("account_number2")
    ifsc = request.form.get("ifsc")
    branch = request.form.get("branch_name")

    # ❌ Validation
    if not all([account_holder, bank_name, acc1, acc2, ifsc, branch]):
        return "❌ All fields are required"

    if acc1 != acc2:
        return "❌ Account numbers do not match"

    # 📁 File upload
    bank_proof = request.files.get("bank_proof")

    filename = None

    if bank_proof and bank_proof.filename:
        # Use consistent naming and path
        filename = secrets.token_hex(8) + "_" + secure_filename(bank_proof.filename)
        # Save to static/uploads folder
        bank_proof.save(os.path.join("static/uploads", filename))
        print(f"✅ Bank proof saved: {filename}")  # Debug log

    # 💾 DB UPDATE
    cursor.execute("""
        UPDATE kyc_members
        SET account_holder=%s,
            bank_name=%s,
            account_number=%s,
            ifsc=%s,
            branch=%s,
            bank_proof=%s
        WHERE token=%s
    """, (
        account_holder,
        bank_name,
        acc1,
        ifsc,
        branch,
        filename,  # This should save the filename correctly
        token
    ))

    db.commit()
    
    # Verify it was saved
    cursor.execute("SELECT bank_proof FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    check = results[0] if results else None
    print(f"🔍 Bank proof in DB: {check}")  # Debug log

    return redirect(url_for("legal_entity_form", token=token))

@app.route("/legal_entity/<token>")
def legal_entity_form(token):
    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None
    if not user:
        return "❌ Invalid token!"
    return render_template("legalentity.html", token=token)
# -------------------- RUN APP --------------------

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    cursor.execute("UPDATE kyc_members SET is_deleted=1 WHERE id=%s", (id,))
    db.commit()
    return redirect(url_for('admin_payment'))  # better redirect

@app.route("/success")
def success():
    return render_template("kyc_submitted.html", login_id="INMBA123", login_link="/login")
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/legal_entity_submit/<token>", methods=["POST"])
def legal_entity_submit(token):

    aadhar_number = request.form.get("entity_aadhar_number")
    house_no = request.form.get("entity_house_no")
    street = request.form.get("entity_street")
    area = request.form.get("entity_area")
    city = request.form.get("entity_city")
    district = request.form.get("entity_district")
    state = request.form.get("entity_state")
    pincode = request.form.get("entity_pincode")

    from werkzeug.utils import secure_filename

    # -------- Aadhaar file upload --------
    aadhar_front = request.files.get("entity_aadhar_front")
    aadhar_back = request.files.get("entity_aadhar_back")
    aadhar_selfie = request.files.get("entity_aadhar_selfie")

    front_file = None
    back_file = None
    selfie_file = None

    if aadhar_front and aadhar_front.filename != "":
        front_file = secrets.token_hex(8) + "_" + secure_filename(aadhar_front.filename)
        aadhar_front.save(os.path.join("static/uploads", front_file))

    if aadhar_back and aadhar_back.filename != "":
        back_file = secrets.token_hex(8) + "_" + secure_filename(aadhar_back.filename)
        aadhar_back.save(os.path.join("static/uploads", back_file))

    if aadhar_selfie and aadhar_selfie.filename != "":
        selfie_file = secrets.token_hex(8) + "_" + secure_filename(aadhar_selfie.filename)
        aadhar_selfie.save(os.path.join("static/uploads", selfie_file))

    # -------- DB UPDATE --------
    cursor.execute("""
        UPDATE kyc_members
        SET entity_aadhar_number=%s,
            entity_house_no=%s,
            entity_street=%s,
            entity_area=%s,
            entity_city=%s,
            entity_district=%s,
            entity_state=%s,
            entity_pincode=%s,
            entity_aadhar_front=%s,
            entity_aadhar_back=%s,
            entity_aadhar_selfie=%s
        WHERE token=%s
    """, (
        aadhar_number,
        house_no,
        street,
        area,
        city,
        district,
        state,
        pincode,
        front_file,
        back_file,
        selfie_file,
        token
    ))

    db.commit()

    return redirect(url_for("pan_page", token=token))
@app.route('/pan_submit/<token>', methods=['POST'])
def pan_submit(token):

    pan_number = request.form['pan_number'].upper()
    pan_name = request.form['pan_name']

    # ✅ CHECK PAN EXISTS
    cursor.execute(
        "SELECT id FROM kyc_members WHERE pan_number=%s AND token!=%s",
        (pan_number, token)
    )
    results = cursor.fetchall()
    existing = results[0] if results else None

    if existing:
        return "❌ This PAN is already registered!"

    from werkzeug.utils import secure_filename

    pan_front = request.files.get('pan_front')
    pan_back = request.files.get('pan_back')

    front_filename = None
    back_filename = None

    # -------- SAVE PAN FRONT --------
    if pan_front and pan_front.filename != "":
        front_filename = secrets.token_hex(8) + "_" + secure_filename(pan_front.filename)
        pan_front.save(os.path.join("static/uploads", front_filename))

    # -------- SAVE PAN BACK --------
    if pan_back and pan_back.filename != "":
        back_filename = secrets.token_hex(8) + "_" + secure_filename(pan_back.filename)
        pan_back.save(os.path.join("static/uploads", back_filename))

    # -------- DB UPDATE --------
    cursor.execute("""
        UPDATE kyc_members
        SET pan_number=%s,
            pan_name=%s,
            pan_front=%s,
            pan_back=%s
        WHERE token=%s
    """, (
        pan_number,
        pan_name,
        front_filename,
        back_filename,
        token
    ))

    db.commit()

    return redirect(url_for("profile_picture", token=token))

def generate_pdf(user, filename):

    from reportlab.platypus import SimpleDocTemplate, Image, Table, TableStyle, Spacer, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    file_path = os.path.join("static/pdfs", filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=12,
        spaceBefore=6,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#0f4d0f"),
        spaceBefore=14,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Label",
        fontSize=10,
        leading=14,
        textColor=colors.black,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="Value",
        fontSize=10,
        leading=14,
        textColor=colors.darkgray,
        spaceAfter=8,
    ))

    elements = []
    elements.append(Paragraph("INMBA KYC REPORT", styles["ReportTitle"]))
    elements.append(Paragraph(
        "Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        styles["Normal"],
    ))
    elements.append(Spacer(1, 18))

    ignore = [
        "password", "token", "pan_front", "pan_back",
        "profile_pic", "entity_aadhar_front",
        "entity_aadhar_back", "entity_aadhar_selfie",
        "payment_proof", "bank_proof",
    ]

    visible_order = [
        "first_name", "last_name", "login_id", "email", "phone",
        "membership_type", "nationality", "occupation",
        "dob", "gender", "marital_status", "state",
        "district", "city", "pincode", "aadhar",
        "payment_status", "transaction_id", "subscription_year",
        "payment_method", "referral_id",
    ]

    details = []
    for key in visible_order:
        value = user.get(key)
        if value:
            details.append([
                Paragraph(f"<b>{key.replace('_', ' ').title()}</b>", styles["Label"]),
                Paragraph(str(value), styles["Value"]),
            ])

    for key, value in user.items():
        if key in ignore or key in visible_order or not value:
            continue
        details.append([
            Paragraph(f"<b>{key.replace('_', ' ').title()}</b>", styles["Label"]),
            Paragraph(str(value), styles["Value"]),
        ])

    if details:
        elements.append(Paragraph("Member Details", styles["SectionHeading"]))
        details_table = Table(details, colWidths=[2.2 * inch, 3.8 * inch], hAlign="LEFT")
        details_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 18))

    def get_image(folder, filename):
        if not filename:
            return Paragraph("Not provided", styles["Value"])

        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            return Paragraph("File missing", styles["Value"])

        try:
            image = Image(path, width=2.2 * inch, height=1.5 * inch)
            image.hAlign = "CENTER"
            return image
        except Exception:
            return Paragraph("Invalid image", styles["Value"])

    document_rows = [
        [
            get_image("static/uploads/profile", user.get("profile_pic")),
            get_image("static/uploads", user.get("pan_front")),
            get_image("static/uploads", user.get("pan_back")),
        ],
        [
            get_image("static/uploads", user.get("entity_aadhar_front")),
            get_image("static/uploads", user.get("entity_aadhar_back")),
            get_image("static/uploads", user.get("entity_aadhar_selfie")),
        ],
    ]

    elements.append(Paragraph("Uploaded Documents", styles["SectionHeading"]))
    uploaded_table = Table(document_rows, colWidths=[2.2 * inch] * 3, hAlign="CENTER")
    uploaded_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(uploaded_table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph("Financial Documents", styles["SectionHeading"]))
    financial_rows = [[
        get_image("static/uploads", user.get("payment_proof")),
        get_image("static/uploads", user.get("bank_proof")),
    ]]
    financial_table = Table(financial_rows, colWidths=[3.0 * inch, 3.0 * inch], hAlign="CENTER")
    financial_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 24))

    footer = Paragraph(
        "INMBA KYC Report generated by INMBA Foundation. All information is confidential.",
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
        ),
    )
    elements.append(footer)

    doc.build(elements)
    return file_path
@app.route("/profile_picture/<token>", methods=['GET','POST'])
def profile_picture(token):

    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None

    if not user:
        return "❌ Invalid token!"

    if request.method == "GET":
        return render_template("profile.html", token=token)

    if request.method == "POST":

        profile_pic           = request.files.get('profile_pic')
        contact_number        = request.form.get('contact_number')
        whatsapp_number       = request.form.get('whatsapp_number')
        declaration           = request.form.get("declaration")
        nomini_name           = request.form.get('nomini_name')
        nomini_dob            = request.form.get('nomini_dob')
        nomini_relationship   = request.form.get('nomini_relationship')
        nomini_aadhar         = request.form.get('nomini_aadhar')
        witness_name          = request.form.get('witness_name')
        witness_phone         = request.form.get('witness_phone')
        witness_inmba_id      = request.form.get('witness_inmba_id')
        social_links_list = request.form.getlist('social_link[]')
        social_links = ', '.join([l for l in social_links_list if l.strip()])
        educational_qualification = request.form.get('educational_qualification')

        if not declaration:
            return "❌ Please accept declaration"

        filename = None
        if profile_pic and profile_pic.filename != "":
            filename = secrets.token_hex(8) + "_" + secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join("static/uploads/profile", filename))

        cursor.execute("""
            UPDATE kyc_members
            SET profile_pic=%s,
                contact_number=%s,
                whatsapp_number=%s,
                nomini_name=%s,
                nomini_dob=%s,
                nomini_relationship=%s,
                nomini_aadhar=%s,
                witness_name=%s,
                witness_phone=%s,
                witness_inmba_id=%s,
                social_links=%s,
                educational_qualification=%s,
                payment_status='pending'
            WHERE token=%s
        """, (
            filename,
            contact_number,
            whatsapp_number,
            nomini_name,
            nomini_dob,
            nomini_relationship,
            nomini_aadhar,
            witness_name,
            witness_phone,
            witness_inmba_id,
            social_links,
            educational_qualification,
            token
        ))

        db.commit()
        return redirect(url_for("acknowledgement", token=token))
@app.route("/acknowledgement/<token>")
def acknowledgement(token):

    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None

    return render_template("acknowledgement.html", user=user)
from flask import send_file

@app.route("/download_ack/<token>")
def download_ack(token):

    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None

    if not user:
        return "❌ User not found"

    pdf_path = generate_pdf(user, f"{token}.pdf")

    return send_file(
    pdf_path,
    as_attachment=True,
    download_name=f"{token}.pdf",
    mimetype="application/pdf"
)
@app.route("/admin")
def admin():
    if "admin" not in session:          # ← ADD THIS
        return redirect(url_for("admin_login"))

    status_filter = request.args.get("status", "all")

    if status_filter in ("approved", "pending", "rejected"):
        cursor.execute(
            "SELECT * FROM kyc_members WHERE payment_status=%s AND is_deleted=0 ORDER BY id DESC",
            (status_filter,)
        )
    else:
        cursor.execute("SELECT * FROM kyc_members WHERE is_deleted=0 ORDER BY id DESC")

    users = cursor.fetchall()

    cursor.execute(
        "SELECT payment_status, COUNT(*) AS count FROM kyc_members WHERE is_deleted=0 GROUP BY payment_status"
    )
    counts = {row["payment_status"]: row["count"] for row in cursor.fetchall()}

    status_counts = {
        "approved": counts.get("approved", 0),
        "pending":  counts.get("pending",  0),
        "rejected": counts.get("rejected", 0),
        "all":      sum(counts.values())
    }

    return render_template(
        "admin.html",
        users=users,
        status_counts=status_counts,
        selected_status=status_filter,
    )

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # simple hardcoded login (you can improve later)
        if username == "admin" and password == "inmba@2026":
            session["admin"] = True
            return redirect(url_for("admin_payment"))

        return "❌ Invalid Credentials"

    return render_template("admin_login.html")
@app.route("/admin_payment")
def admin_payment():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    status_filter = request.args.get("status", "all")

    if status_filter in ("approved", "pending", "rejected"):
        cursor.execute(
            "SELECT id, login_id, first_name, email, phone, payment_status, profile_pic FROM kyc_members WHERE payment_status=%s AND is_deleted=0 ORDER BY id DESC",
            (status_filter,)
        )
    else:
        cursor.execute(
            "SELECT id, login_id, first_name, email, phone, payment_status, profile_pic FROM kyc_members WHERE is_deleted=0 ORDER BY id DESC"
        )

    users = cursor.fetchall()

    cursor.execute(
        "SELECT payment_status, COUNT(*) AS count FROM kyc_members WHERE is_deleted=0 GROUP BY payment_status"
    )
    counts = {row["payment_status"]: row["count"] for row in cursor.fetchall()}

    status_counts = {
        "approved": counts.get("approved", 0),
        "pending":  counts.get("pending",  0),
        "rejected": counts.get("rejected", 0),
        "all":      sum(counts.values())
    }

    cursor.execute(
        "SELECT COUNT(*) AS count FROM kyc_members WHERE is_deleted=0 AND transaction_id IS NOT NULL AND transaction_id != ''"
    )
    payment_done = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT COUNT(*) AS count FROM kyc_members WHERE is_deleted=0 AND (transaction_id IS NULL OR transaction_id = '')"
    )
    payment_not_done = cursor.fetchone()["count"]

    return render_template(
        "admin_payment.html",
        users=users,
        status_counts=status_counts,
        selected_status=status_filter,
        payment_done=payment_done,
        payment_not_done=payment_not_done,
    )   
    return render_template("admin_payment.html", users=users, status_counts=status_counts, selected_status=status_filter)
@app.route("/admin/user/<int:id>")
def admin_user_details(id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute("SELECT * FROM kyc_members WHERE id=%s", (id,))
    results = cursor.fetchall()
    user = results[0] if results else None

    return render_template("admin_user_details.html", user=user)

@app.route("/admin_verify/<int:id>", methods=["POST"])
def admin_verify(id):

    status = request.form.get("status")
    referral_id = request.form.get("referral_id")
    send_method = request.form.get("send_method", "email")

    cursor.execute(
        "SELECT email, phone FROM kyc_members WHERE id=%s",
        (id,)
    )
    results = cursor.fetchall()
    user = results[0] if results else None

    if status == "approved" and not referral_id:
        referral_id = generate_unique_referral_id()

    cursor.execute("""
        UPDATE kyc_members
        SET payment_status=%s,
            referral_id=%s
        WHERE id=%s
    """, (status, referral_id, id))

    db.commit()

    if status == "approved" and user:
        referral_link = url_for('membership', _external=True) + f"?ref={referral_id}"

        if send_method == "email" and user.get('email'):
            sent, message = send_referral_email(user['email'], referral_link, referral_id)
            flash(message)
        elif send_method == "otp" and user.get('phone'):
            otp_code = generate_otp()
            flash(f"OTP generated for {user['phone']}: {otp_code}. SMS gateway not configured.")
        else:
            flash("Referral created, but delivery method could not be completed.")

    return redirect(url_for("admin_payment"))


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(debug=True)
