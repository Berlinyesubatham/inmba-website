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
import requests
from datetime import datetime, timedelta

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
    host="localhost", user="root", password="root", database="inmba"
)
cursor = db.cursor(dictionary=True)


# -------------------- HELPER FUNCTIONS --------------------
def generate_unique_referral_id():
    existing_chars = string.ascii_uppercase + string.digits
    while True:
        referral_id = "".join(random.choices(existing_chars, k=8))
        cursor.execute(
            "SELECT id FROM kyc_members WHERE referral_id=%s", (referral_id,)
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
        """,
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


# def is_strong_password(password):
#     if len(password) < 8:
#         return False, "Password must be at least 8 characters long."
#     if not re.search(r"[A-Z]", password):
#         return False, "Password must contain at least one uppercase letter."
#     if not re.search(r"[a-z]", password):
#         return False, "Password must contain at least one lowercase letter."
#     if not re.search(r"[0-9]", password):
#         return False, "Password must contain at least one digit."
#     if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
#         return False, "Password must contain at least one special character."
#     return True, ""


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
        """,
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
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/membership")
def membership():
    referral_token = request.args.get("ref")
    return render_template("membership.html", referral_token=referral_token)


@app.route("/commercial")
def commercial():
    return render_template("commercial.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/events")
def events():
    return render_template("events.html")


@app.route("/programs")
def programs():
    return render_template("programs.html")


@app.route("/foundation")
def foundation():
    return render_template("foundation.html")


@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


@app.route("/organization")
def organization():
    return render_template("organization.html")


@app.route("/network")
def network():
    return render_template("network.html")


# -------------------- MEMBER REGISTRATION --------------------
@app.route("/register", methods=["POST"])
def register():

    # ---------- Generate Unique Login ID ----------
    def generate_unique_login_id():
        while True:
            login_id = str(random.randint(1000000, 9999999))
            cursor.execute("SELECT id FROM kyc_members WHERE login_id=%s", (login_id,))
            if not cursor.fetchone():
                return login_id

    login_id = generate_unique_login_id()
    token = str(uuid.uuid4())

    # ---------- Get Data (JSON + FORM SUPPORT) ----------
    data = request.get_json(silent=True) or request.form

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    father_name = data.get("father_name")
    dob = data.get("dob")
    email = data.get("email")
    phone = data.get("phone")
    pincode = data.get("pincode")
    gender = data.get("gender")
    marital_status = data.get("marital_status")
    nationality = data.get("nationality")
    occupation = data.get("occupation")
    education = data.get("education")
    membership_type = data.get("membership_type")
    referred_by = data.get("referral") or None
    aadhar = data.get("aadhar")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    # ---------- Validations ----------
    if not email:
        flash("Email is required")
        return render_template("membership.html")

    if not is_valid_email(email):
        flash("Please enter a valid email address.")
        return render_template(
            "membership.html", error="Invalid email format.", referral_token=referred_by
        )

    if password != confirm_password:
        flash("Password and Confirm Password do not match.")
        return render_template(
            "membership.html", error="Password mismatch", referral_token=referred_by
        )
    # ---------- LIMIT CHECK (MAX 3 REGISTRATIONS) ----------
    if email and phone:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM kyc_members WHERE email=%s AND phone=%s",
            (email, phone),
        )
        result = cursor.fetchone()
        count = result["total"] if result else 0

        if count >= 3:
            flash("Account limit expired. Please contact support.")
            return render_template(
                "membership.html",
                error="Account limit expired",
                referral_token=referred_by,
            )

    # ❗ IMPORTANT: Removed duplicate check block
    # (otherwise it blocks 2nd/3rd registration)

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    # ---------- Aadhar Check ----------
    if aadhar:
        cursor.execute("SELECT id FROM kyc_members WHERE aadhar=%s LIMIT 1", (aadhar,))
        if cursor.fetchone():
            flash("Aadhar already registered. Please login.")
            return redirect(url_for("login"))

    # ---------- INSERT QUERY ----------
    sql = """
    INSERT INTO kyc_members (
        first_name, last_name, father_name, dob, email, phone,
        pincode,
        gender, marital_status, nationality,
        occupation, education, membership_type,
        referred_by, aadhar, token, login_id, password, created_at
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """
    values = (
        first_name,
        last_name,
        father_name,
        dob,
        email,
        phone,
        pincode,
        gender,
        marital_status,
        nationality,
        occupation,
        education,
        membership_type,
        referred_by,
        aadhar,
        token,
        login_id,
        hashed_password,
    )

    # Debug check
    print("Placeholders:", sql.count("%s"))
    print("Values:", len(values))

    cursor.execute(sql, values)
    db.commit()

    # ---------- Network Update ----------
    if referred_by:
        cursor.execute(
            "SELECT id, referred_by FROM kyc_members WHERE referral_id=%s",
            (referred_by,),
        )
        referrer = cursor.fetchone()

        if referrer:
            cursor.execute(
                "UPDATE kyc_members SET direct_network = COALESCE(direct_network,0)+1 WHERE id=%s",
                (referrer["id"],),
            )
            db.commit()

            if referrer["referred_by"]:
                cursor.execute(
                    "SELECT id FROM kyc_members WHERE referral_id=%s",
                    (referrer["referred_by"],),
                )
                grand_referrer = cursor.fetchone()

                if grand_referrer:
                    cursor.execute(
                        "UPDATE kyc_members SET indirect_network = COALESCE(indirect_network,0)+1 WHERE id=%s",
                        (grand_referrer["id"],),
                    )
                    db.commit()

    # ---------- Success ----------
    session["new_login_id"] = login_id
    login_link = url_for("login", _external=True)

    return render_template(
        "kyc_submitted.html", login_id=login_id, login_link=login_link
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    # Pick up login_id from session if just registered
    prefill_id = session.pop("new_login_id", None)

    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        if not login_id or not password:
            return render_template(
                "login.html",
                error="Please provide both Login ID and password.",
                prefill_id=login_id,
            )

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT * FROM kyc_members WHERE login_id=%s AND password=%s",
            (login_id, hashed_password),
        )
        results = cursor.fetchall()
        user = results[0] if results else None

        if not user:
            return render_template(
                "login.html", error="Invalid login ID or password.", prefill_id=login_id
            )

        session.clear()
        user.pop("password", None)
        session["user"] = user
        session["user_token"] = user.get("token")
        return redirect(url_for("dashboard"))

    return render_template("login.html", prefill_id=prefill_id)


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email", "").strip()

        # 🔹 Validate input
        if not email:
            return render_template("forgot_password.html", error="Email is required")

        if not is_valid_email(email):
            return render_template(
                "forgot_password.html", error="Invalid email address"
            )

        db_conn = None
        cursor = None

        try:
            # 🔹 fresh connection usage (safe)
            db_conn = db
            cursor = db_conn.cursor(dictionary=True)

            # 🔹 check user
            cursor.execute("SELECT id FROM kyc_members WHERE email=%s", (email,))
            user = cursor.fetchone()

            if not user:
                return render_template(
                    "forgot_password.html", error="No account found with this email"
                )

            # 🔹 call mail server
            try:
                response = requests.post(
                    "http://localhost:3000/api/auth/forgot-password",
                    json={"email": email},
                    timeout=5,
                )

                print("MAIL STATUS:", response.status_code)
                print("MAIL RESPONSE:", response.text)

                data = response.json()

                if not data.get("success"):
                    return render_template(
                        "forgot_password.html", error="Failed to send OTP. Try again."
                    )

                otp = data.get("otp")

                if not otp:
                    return render_template(
                        "forgot_password.html", error="OTP not received. Try again."
                    )

            except requests.exceptions.RequestException as e:
                print("Mail server error:", e)
                return render_template(
                    "forgot_password.html", error="Mail server not reachable"
                )

            # 🔹 store OTP in DB
            expires_at = datetime.now() + timedelta(minutes=5)

            cursor.execute(
                """
                UPDATE kyc_members
                SET otp=%s,
                    otp_expires=%s
                WHERE id=%s
            """,
                (otp, expires_at, user["id"]),
            )

            db_conn.commit()

            # 🔹 session
            session["reset_email"] = email
            email = session.get("reset_email")
            print("Session reset_email set to:", email)
            return redirect(url_for("verify_otp"))

        except Exception as e:
            print("Unexpected error:", e)
            return render_template("forgot_password.html", error="Something went wrong")

        finally:
            # 🔥 FIX: always cleanup (prevents unread result error)
            if cursor:
                cursor.close()

    return render_template("forgot_password.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():

    email = session.get("reset_email")

    print("SESSION EMAIL:", email)  # 🔥 DEBUG

    # if not email:
    #     print("SESSION LOST → redirecting")
    #     return redirect(url_for("forgot_password"))

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()

        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT otp, otp_expires
                FROM kyc_members
                WHERE email=%s
            """,
                (email,),
            )

            user = cursor.fetchone()

            print("DB USER:", user)

            if not user:
                return render_template("verify_otp.html", error="User not found")

            if user["otp_expires"] is None or user["otp_expires"] < datetime.now():
                return render_template("verify_otp.html", error="OTP expired")

            if str(user["otp"]) != str(entered_otp):
                return render_template("verify_otp.html", error="Invalid OTP")

            return redirect(url_for("reset_password"))

        finally:
            cursor.close()

    return render_template("verify_otp.html")


import hashlib


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    email = session.get("reset_email")

    # 🔴 block direct access
    if not email:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # validation
        if not password or not confirm_password:
            return render_template("reset_password.html", error="All fields required")

        if password != confirm_password:
            return render_template(
                "reset_password.html", error="Passwords do not match"
            )

        try:
            cursor = db.cursor()

            # hash password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # update DB
            cursor.execute(
                """
                UPDATE kyc_members
                SET password=%s,
                    otp=NULL,
                    otp_expires=NULL
                WHERE email=%s
            """,
                (hashed_password, email),
            )

            db.commit()

            cursor.close()

            # clear session
            session.pop("reset_email", None)

            flash("Password updated successfully")

            return redirect(url_for("login"))

        except Exception as e:
            print("Reset error:", e)
            return render_template("reset_password.html", error="Something went wrong")

    return render_template("reset_password.html")


# -------------------- DASHBOARD --------------------
# @app.route("/dashboard")
# def dashboard():
#     if "user" not in session:
#         return redirect(url_for("login"))

#     user_session = session["user"]
#     cursor.execute("SELECT * FROM kyc_members WHERE id=%s", (user_session.get("id"),))
#     results = cursor.fetchall()
#     user = results[0] if results else None
#     if not user:
#         session.pop("user", None)
#         return redirect(url_for("login"))

#     if user.get("referral_id"):
#         user["referral_link"] = (
#             url_for("membership", _external=True) + f"?ref={user.get('referral_id')}"
#         )

#     return render_template("dashboard.html", user=user)


@app.route("/policy")
def policy():
    return render_template("policy.html")


@app.route("/accept_policy", methods=["POST"])
def accept_policy():
    session["policy_accepted"] = True
    return redirect(url_for("payment"))


@app.route("/logout")
def logout():
    session.clear()  # ← clear ALL session data, not just 'user'
    return redirect(url_for("login"))


# -------------------- VIEW ALL MEMBERS --------------------


@app.route("/members")
def members():
    cursor.execute("SELECT * FROM kyc_members")
    data = cursor.fetchall()
    return render_template("members.html", members=data)


@app.route("/payment")
def payment():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("payment.html")


@app.route("/pan/<token>")
def pan_page(token):
    return render_template("pancard.html", token=token)


# ─────────────────────────────────────────────────────────────
# REPLACE your existing payment_submit route with this
# ─────────────────────────────────────────────────────────────


@app.route("/payment_submit", methods=["POST"])
def payment_submit():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]

    # Required fields
    payment_method = request.form.get("payment_method")
    subscription_year = request.form.get("subscription_year")
    amount = request.form.get("amount")  # ← REQUIRED

    # Validate amount
    if not amount:
        flash("Amount is required.")
        return redirect(url_for("payment"))

    try:
        amount = float(amount)
        if amount <= 0:
            flash("Amount must be greater than 0.")
            return redirect(url_for("payment"))
    except ValueError:
        flash("Invalid amount entered.")
        return redirect(url_for("payment"))

    # Optional fields — store NULL if empty
    transaction_id = request.form.get("transaction_id") or None  # ← OPTIONAL
    payment_file = request.files.get("payment_proof")  # ← OPTIONAL

    filename = None
    if payment_file and payment_file.filename:
        filename = secrets.token_hex(8) + "_" + secure_filename(payment_file.filename)
        payment_file.save("static/uploads/" + filename)

    cursor.execute(
        """
        UPDATE kyc_members
        SET transaction_id=%s,
            subscription_year=%s,
            payment_method=%s,
            amount=%s,
            payment_proof=%s
        WHERE id=%s
    """,
        (
            transaction_id,
            subscription_year,
            payment_method,
            amount,
            filename,
            user["id"],
        ),
    )

    db.commit()

    token = session.get("user_token")
    return redirect(url_for("bank_form", token=token))


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
    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None
    if not user:
        return "❌ Invalid token"

    account_holder = request.form.get("account_holder")
    bank_name = request.form.get("bank_name")
    branch = request.form.get("branch_name")

    # Optional
    acc1 = request.form.get("account_number1") or None
    acc2 = request.form.get("account_number2") or None
    ifsc = request.form.get("ifsc") or None

    # Required fields only
    if not all([account_holder, bank_name, branch]):
        return "❌ Account holder, bank name and branch are required"

    # Only validate match if user entered account number
    if acc1 or acc2:
        if acc1 != acc2:
            return "❌ Account numbers do not match"

    bank_proof = request.files.get("bank_proof")
    filename = None
    if bank_proof and bank_proof.filename:
        filename = secrets.token_hex(8) + "_" + secure_filename(bank_proof.filename)
        bank_proof.save(os.path.join("static/uploads", filename))

    cursor.execute(
        """
        UPDATE kyc_members
        SET account_holder=%s,
            bank_name=%s,
            account_number=%s,
            ifsc=%s,
            branch=%s,
            bank_proof=%s
        WHERE token=%s
    """,
        (account_holder, bank_name, acc1, ifsc, branch, filename, token),
    )

    db.commit()
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
    return redirect(url_for("admin_payment"))  # better redirect


@app.route("/success")
def success():
    return render_template(
        "kyc_submitted.html", login_id="INMBA123", login_link="/login"
    )


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
        selfie_file = (
            secrets.token_hex(8) + "_" + secure_filename(aadhar_selfie.filename)
        )
        aadhar_selfie.save(os.path.join("static/uploads", selfie_file))

    # -------- DB UPDATE --------
    cursor.execute(
        """
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
    """,
        (
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
            token,
        ),
    )

    db.commit()

    return redirect(url_for("pan_page", token=token))


@app.route("/pan_submit/<token>", methods=["POST"])
def pan_submit(token):
    pan_number = request.form.get("pan_number", "").upper() or None  # optional
    pan_name = request.form.get("pan_name") or None  # optional

    # Only check duplicate if pan_number was provided
    if pan_number:
        cursor.execute(
            "SELECT id FROM kyc_members WHERE pan_number=%s AND token!=%s",
            (pan_number, token),
        )
        if cursor.fetchone():
            return "❌ This PAN is already registered!"

    # PAN front — optional
    pan_front = request.files.get("pan_front")
    front_filename = None
    if pan_front and pan_front.filename:
        front_filename = (
            secrets.token_hex(8) + "_" + secure_filename(pan_front.filename)
        )
        pan_front.save(os.path.join("static/uploads", front_filename))

    cursor.execute(
        """
        UPDATE kyc_members
        SET pan_number=%s,
            pan_name=%s,
            pan_front=%s
        WHERE token=%s
    """,
        (pan_number, pan_name, front_filename, token),
    )

    db.commit()
    return redirect(url_for("profile_picture", token=token))


def generate_pdf(user, filename):

    import os
    from datetime import datetime
    from reportlab.platypus import (
        SimpleDocTemplate,
        Image,
        Table,
        TableStyle,
        Spacer,
        Paragraph,
        HRFlowable,
    )
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    PAGE_W, PAGE_H = A4
    MARGIN = 0.5 * inch
    CONTENT_W = PAGE_W - 2 * MARGIN

    GREEN_DARK = colors.HexColor("#0f4d0f")
    GREEN_LIGHT = colors.HexColor("#e8f5e9")
    GREY_LINE = colors.HexColor("#cccccc")
    GREY_TEXT = colors.HexColor("#555555")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join("static/pdfs", filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    styles = getSampleStyleSheet()

    def add_style(name, **kwargs):
        styles.add(ParagraphStyle(name=name, **kwargs))

    add_style(
        "DocTitle",
        fontSize=16,
        textColor=colors.white,
        alignment=TA_LEFT,
        spaceAfter=0,
        leading=20,
    )
    add_style(
        "DocSub",
        fontSize=9,
        textColor=colors.HexColor("#c8e6c9"),
        alignment=TA_LEFT,
        spaceAfter=0,
    )
    add_style(
        "SectionHd",
        fontSize=10,
        textColor=GREEN_DARK,
        spaceBefore=10,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    add_style("CellLabel", fontSize=9, textColor=GREY_TEXT, fontName="Helvetica-Bold")
    add_style("CellValue", fontSize=9, textColor=colors.black)
    add_style("Footer", fontSize=7.5, textColor=GREY_TEXT, alignment=TA_CENTER)
    add_style("SignLabel", fontSize=9, textColor=GREY_TEXT, fontName="Helvetica-Bold")
    add_style(
        "DocLabel",
        fontSize=8,
        textColor=GREY_TEXT,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    elements = []

    # ── Helper: safe image ─────────────────────────────────────────────────────
    def get_image(path, w=2.2, h=1.6):
        if not path:
            return Paragraph("Not provided", styles["CellValue"])
        if not os.path.exists(path):
            return Paragraph("File missing", styles["CellValue"])
        try:
            return Image(path, width=w * inch, height=h * inch)
        except Exception:
            return Paragraph("Invalid file", styles["CellValue"])

    def full_path(folder, fname):
        """Build absolute path for a file."""
        if not fname:
            return ""
        return os.path.join(BASE_DIR, folder, fname)

    # 1. HEADER BANNER
    profile_img = (
        get_image(
            full_path("static/uploads/profile", user.get("profile_pic")), 1.1, 1.1
        )
        if user.get("profile_pic")
        else Paragraph("", styles["CellValue"])
    )

    header_table = Table(
        [
            [
                [
                    Paragraph("INMBA", styles["DocTitle"]),
                    Paragraph("KYC Verification Report", styles["DocSub"]),
                    Paragraph(
                        f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}",
                        styles["DocSub"],
                    ),
                ],
                profile_img,
            ]
        ],
        colWidths=[CONTENT_W - 1.3 * inch, 1.3 * inch],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GREEN_DARK),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 12),
                ("RIGHTPADDING", (1, 0), (1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # 2. MEMBER DETAILS
    elements.append(Paragraph("Member Details", styles["SectionHd"]))
    elements.append(
        HRFlowable(width=CONTENT_W, thickness=1, color=GREEN_DARK, spaceAfter=6)
    )

    MEMBER_FIELDS = [
        ("first_name", "First Name"),
        ("last_name", "Last Name"),
        ("father_name", "Father Name"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("dob", "Date of Birth"),
        ("gender", "Gender"),
        ("address", "Address"),
        ("city", "City"),
        ("state", "State"),
        ("pincode", "Pin Code"),
        ("country", "Country"),
        ("referral_id", "Referral ID"),
        ("joining_date", "Joining Date"),
    ]

    def kv_cell(label, value):
        return [
            Paragraph(label, styles["CellLabel"]),
            Paragraph(str(value) if value else "—", styles["CellValue"]),
        ]

    rows = []
    pairs = [(lbl, user.get(key, "")) for key, lbl in MEMBER_FIELDS if user.get(key)]

    COL_W = CONTENT_W / 2 - 6
    for i in range(0, len(pairs), 2):
        left_lbl, left_val = pairs[i]
        right_lbl, right_val = pairs[i + 1] if i + 1 < len(pairs) else ("", "")
        rows.append(
            [
                Table(
                    [kv_cell(left_lbl, left_val)],
                    colWidths=[1.4 * inch, COL_W - 1.4 * inch],
                ),
                Table(
                    [kv_cell(right_lbl, right_val)],
                    colWidths=[1.4 * inch, COL_W - 1.4 * inch],
                ),
            ]
        )

    if rows:
        grid = Table(rows, colWidths=[COL_W + 6, COL_W])
        grid.setStyle(
            TableStyle(
                [
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GREEN_LIGHT]),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, GREY_LINE),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(grid)

    elements.append(Spacer(1, 14))

    # 3. ADDITIONAL DETAILS
    EXCLUDE = {
        # private / sensitive
        "password",
        "token",
        "signature_image",
        # images — shown in document sections below
        "profile_pic",
        "pan_front",
        "pan_back",
        "payment_proof",
        "bank_proof",
        "entity_aadhar_front",
        "entity_aadhar_back",
        "entity_aadhar_selfie",
        # shown in member details
        "first_name",
        "last_name",
        "father_name",
        "email",
        "phone",
        "dob",
        "gender",
        "address",
        "city",
        "state",
        "pincode",
        "country",
        "referral_id",
        "joining_date",
    }

    def clean_label(key):
        label = key.replace("_", " ").title()
        label = label.replace("Nomini", "Nominee")
        label = label.replace("Nomine ", "Nominee ")
        label = label.replace("Nominne", "Nominee")
        label = label.replace(" Entity", "")
        label = label.replace("Entity ", "")
        return label.strip()

    extra = [(clean_label(k), v) for k, v in user.items() if k not in EXCLUDE and v]

    if extra:
        elements.append(Paragraph("Additional Information", styles["SectionHd"]))
        elements.append(
            HRFlowable(width=CONTENT_W, thickness=1, color=GREEN_DARK, spaceAfter=6)
        )

        extra_rows = []
        for i in range(0, len(extra), 2):
            lbl1, val1 = extra[i]
            lbl2, val2 = extra[i + 1] if i + 1 < len(extra) else ("", "")
            extra_rows.append(
                [
                    Table(
                        [kv_cell(lbl1, val1)],
                        colWidths=[1.6 * inch, COL_W - 1.6 * inch],
                    ),
                    Table(
                        [kv_cell(lbl2, val2)],
                        colWidths=[1.6 * inch, COL_W - 1.6 * inch],
                    ),
                ]
            )

        extra_grid = Table(extra_rows, colWidths=[COL_W + 6, COL_W])
        extra_grid.setStyle(
            TableStyle(
                [
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GREEN_LIGHT]),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, GREY_LINE),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(extra_grid)
        elements.append(Spacer(1, 14))

    IMG_W, IMG_H = 2.2, 1.6

    def img_cell(folder, fname):
        """Shortcut — builds path and returns image or 'Not uploaded'."""
        if not fname:
            return Paragraph("Not uploaded", styles["CellValue"])
        return get_image(full_path(folder, fname), IMG_W, IMG_H)

    # 4. UPLOADED DOCUMENTS (PAN / Payment / Bank)
    elements.append(Paragraph("Uploaded Documents", styles["SectionHd"]))
    elements.append(
        HRFlowable(width=CONTENT_W, thickness=1, color=GREEN_DARK, spaceAfter=6)
    )

    doc_rows = [
        [
            Paragraph("PAN Card (Front)", styles["DocLabel"]),
            Paragraph("Payment Proof", styles["DocLabel"]),
            Paragraph("Bank Proof", styles["DocLabel"]),
        ],
        [
            img_cell("static/uploads", user.get("pan_front")),
            img_cell("static/uploads", user.get("payment_proof")),
            img_cell("static/uploads", user.get("bank_proof")),
        ],
    ]

    doc_table = Table(doc_rows, colWidths=[CONTENT_W / 3] * 3)
    doc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN_LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, GREY_LINE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(doc_table)
    elements.append(Spacer(1, 18))

    # 4b. AADHAAR DOCUMENTS
    elements.append(Paragraph("Aadhaar Documents", styles["SectionHd"]))
    elements.append(
        HRFlowable(width=CONTENT_W, thickness=1, color=GREEN_DARK, spaceAfter=6)
    )

    aadhar_rows = [
        [
            Paragraph("Aadhaar Front", styles["DocLabel"]),
            Paragraph("Aadhaar Back", styles["DocLabel"]),
            Paragraph("Aadhaar Selfie", styles["DocLabel"]),
        ],
        [
            img_cell("static/uploads", user.get("entity_aadhar_front")),
            img_cell("static/uploads", user.get("entity_aadhar_back")),
            img_cell("static/uploads", user.get("entity_aadhar_selfie")),
        ],
    ]

    aadhar_table = Table(aadhar_rows, colWidths=[CONTENT_W / 3] * 3)
    aadhar_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN_LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, GREY_LINE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(aadhar_table)
    elements.append(Spacer(1, 18))

    # 5. DECLARATION & SIGNATURE
    elements.append(Paragraph("Declaration & Signature", styles["SectionHd"]))
    elements.append(
        HRFlowable(width=CONTENT_W, thickness=1, color=GREEN_DARK, spaceAfter=8)
    )

    declaration_text = (
        "I hereby declare that the information furnished above is true, complete "
        "and correct to the best of my knowledge and belief. I undertake to inform "
        "the company of any change therein."
    )
    elements.append(Paragraph(declaration_text, styles["CellValue"]))
    elements.append(Spacer(1, 24))

    LINE = "_" * 28

    sig_fields = Table(
        [
            [
                Paragraph(f"Date: {LINE}", styles["CellValue"]),
                Paragraph(f"Place: {LINE}", styles["CellValue"]),
                Paragraph(f"Signature: {LINE}", styles["CellValue"]),
            ]
        ],
        colWidths=[CONTENT_W / 3] * 3,
    )
    sig_fields.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(sig_fields)
    elements.append(Spacer(1, 24))

    # 6. FOOTER
    elements.append(
        HRFlowable(width=CONTENT_W, thickness=0.5, color=GREY_LINE, spaceAfter=4)
    )
    elements.append(
        Paragraph(
            "INMBA KYC Report  ·  Confidential Document  ·  "
            f"Generated on {datetime.now().strftime('%d %b %Y')}",
            styles["Footer"],
        )
    )

    doc.build(elements)
    return file_path


@app.route("/profile_picture/<token>", methods=["GET", "POST"])
def profile_picture(token):

    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None

    if not user:
        return "❌ Invalid token!"

    if request.method == "GET":
        return render_template("profile.html", token=token)

    if request.method == "POST":

        profile_pic = request.files.get("profile_pic")
        contact_number = request.form.get("contact_number")
        whatsapp_number = request.form.get("whatsapp_number")
        declaration = request.form.get("declaration")
        nomini_name = request.form.get("nomini_name")
        nomini_dob = request.form.get("nomini_dob")
        nomini_relationship = request.form.get("nomini_relationship")
        nomini_aadhar = request.form.get("nomini_aadhar")
        witness_name = request.form.get("witness_name")
        witness_phone = request.form.get("witness_phone")
        witness_inmba_id = request.form.get("witness_inmba_id")
        social_links_list = request.form.getlist("social_link[]")
        social_links = ", ".join([l for l in social_links_list if l.strip()])
        educational_qualification = request.form.get("educational_qualification")

        if not declaration:
            return "❌ Please accept declaration"

        filename = None
        if profile_pic and profile_pic.filename != "":
            filename = (
                secrets.token_hex(8) + "_" + secure_filename(profile_pic.filename)
            )
            profile_pic.save(os.path.join("static/uploads/profile", filename))

        cursor.execute(
            """
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
        """,
            (
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
                token,
            ),
        )

        db.commit()
        return redirect(url_for("acknowledgement", token=token))


@app.route("/acknowledgement/<token>")
def acknowledgement(token):

    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None

    return render_template("acknowledgement.html", user=user)


from flask import send_file


# ✅ FIXED — only ONE decorator
@app.route("/download_ack/<token>")
def download_ack(token):
    cursor.execute("SELECT * FROM kyc_members WHERE token=%s", (token,))
    results = cursor.fetchall()
    user = results[0] if results else None

    if not user:
        return "❌ User not found"

    if user.get("created_at"):
        user["joining_date"] = user["created_at"].strftime("%d %B %Y")
    else:
        user["joining_date"] = ""

    pdf_path = generate_pdf(user, f"{token}.pdf")

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{token}.pdf",
        mimetype="application/pdf",
    )


@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    status_filter = request.args.get("status", "all")

    if status_filter in ("approved", "pending", "rejected"):
        cursor.execute(
            "SELECT * FROM kyc_members WHERE payment_status=%s AND is_deleted=0 ORDER BY id DESC",
            (status_filter,),
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
        "pending": counts.get("pending", 0),
        "rejected": counts.get("rejected", 0),
        "all": sum(counts.values()),
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
            (status_filter,),
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
        "pending": counts.get("pending", 0),
        "rejected": counts.get("rejected", 0),
        "all": sum(counts.values()),
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
    return render_template(
        "admin_payment.html",
        users=users,
        status_counts=status_counts,
        selected_status=status_filter,
    )


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

    cursor.execute("SELECT email, phone FROM kyc_members WHERE id=%s", (id,))
    results = cursor.fetchall()
    user = results[0] if results else None

    if status == "approved" and not referral_id:
        referral_id = generate_unique_referral_id()

    cursor.execute(
        """
        UPDATE kyc_members
        SET payment_status=%s,
            referral_id=%s
        WHERE id=%s
    """,
        (status, referral_id, id),
    )

    db.commit()

    if status == "approved" and user:
        referral_link = url_for("membership", _external=True) + f"?ref={referral_id}"

        if send_method == "email" and user.get("email"):
            sent, message = send_referral_email(
                user["email"], referral_link, referral_id
            )
            flash(message)
        elif send_method == "otp" and user.get("phone"):
            otp_code = generate_otp()
            flash(
                f"OTP generated for {user['phone']}: {otp_code}. SMS gateway not configured."
            )
        else:
            flash("Referral created, but delivery method could not be completed.")

    return redirect(url_for("admin_payment"))


@app.route("/save_signature/<token>", methods=["POST"])
def save_signature(token):
    import base64, os, secrets

    signature_data = request.form.get("signature_data")

    if not signature_data:
        return "No signature"

    header, encoded = signature_data.split(",", 1)
    binary = base64.b64decode(encoded)

    filename = secrets.token_hex(8) + ".png"
    path = os.path.join("static/uploads/signature", filename)

    with open(path, "wb") as f:
        f.write(binary)

    # save to DB
    cursor.execute(
        """
        UPDATE kyc_members 
        SET signature_image=%s 
        WHERE token=%s
    """,
        (filename, token),
    )

    db.commit()

    # redirect to PDF
    return redirect(url_for("download_ack", token=token))


@app.route("/soft_delete/<int:user_id>", methods=["POST"])
def soft_delete(user_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))
    cursor.execute("UPDATE kyc_members SET is_deleted=1 WHERE id=%s", (user_id,))
    db.commit()
    flash("User temporarily deactivated. Can be restored later.", "warning")
    return redirect(url_for("admin"))


@app.route("/permanent_delete/<int:id>", methods=["POST"])
def permanent_delete(id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    # ✅ Permanently delete the user
    cursor.execute("DELETE FROM kyc_members WHERE id=%s", (id,))
    db.commit()

    # ✅ Reset auto-increment to current max id + 1
    cursor.execute("SELECT MAX(id) AS max_id FROM kyc_members")
    result = cursor.fetchone()
    max_id = result["max_id"] or 0
    cursor.execute(f"ALTER TABLE kyc_members AUTO_INCREMENT = {max_id + 1}")
    db.commit()

    flash("User permanently deleted and ID reset.", "danger")
    return redirect(url_for("admin"))
@app.route('/profile/<login_id>')
def public_profile(login_id):

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="inmba"
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM kyc_members WHERE login_id=%s", (login_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return "User not found"

    return render_template("public_profile.html", user=user)

import qrcode
import os

import qrcode
import os

@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]

    # Refresh user from DB
    cursor.execute("SELECT * FROM kyc_members WHERE id=%s", (user["id"],))
    user = cursor.fetchone()

    # ✅ Generate QR ONLY if user exists (registered)
    qr_filename = None

    if user and user.get("login_id"):
        qr_data = url_for("public_profile", login_id=user["login_id"], _external=True)

        qr_filename = f"{user['login_id']}.png"
        qr_path = os.path.join("static/qr", qr_filename)

        os.makedirs("static/qr", exist_ok=True)

        if not os.path.exists(qr_path):  # avoid regenerating
            qr = qrcode.make(qr_data)
            qr.save(qr_path)

    # ✅ Get direct members
    cursor.execute("""
        SELECT first_name, last_name, login_id, email
        FROM kyc_members
        WHERE referred_by = %s
    """, (user["referral_id"],))

    direct_members = cursor.fetchall()

    return render_template(
    "dashboard.html",
    user=user,
    direct_members=direct_members,
    qr="qr/" + qr_filename   # ✅ FIXED
)

# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(debug=True)
