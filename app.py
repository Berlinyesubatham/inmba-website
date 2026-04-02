from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import uuid
import os

app = Flask(__name__)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="inmba"
)

cursor = db.cursor()

# ---------- ROUTES ----------
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

# ---------- MEMBER REGISTRATION ----------
@app.route("/register", methods=["POST"])
def register():

    token = str(uuid.uuid4())   # ✅ unique token

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

    sql = """
    INSERT INTO kyc_members
    (first_name,last_name,dob,email,phone,state,district,city,pincode,
    gender,marital_status,nationality,occupation,education,membership_type,token)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        first_name, last_name, dob, email, phone,
        state, district, city, pincode,
        gender, marital_status, nationality, occupation, education,
        membership_type, token
    )

    cursor.execute(sql, values)
    db.commit()

    # 🔗 Generate link
    link = url_for('bank_form', token=token, _external=True)

    return f"""
    KYC Submitted ✅ <br><br>
    Click here to add bank details: <br>
    <a href='{link}'>{link}</a>
    """

# ---------- VIEW ALL MEMBERS ----------
@app.route("/members")
def members():
    cursor.execute("SELECT * FROM members")
    data = cursor.fetchall()
    return render_template("members.html", members=data)
@app.route("/bank/<token>")
def bank_form(token):
    return render_template("bank.html", token=token)

@app.route("/bank_submit/<token>", methods=["POST"])
def bank_submit(token):

    bank_name = request.form.get('bank_name')
    account_number = request.form.get('account_number')
    ifsc = request.form.get('ifsc')

    cursor.execute("""
    UPDATE kyc_members 
    SET bank_name=%s, account_number=%s, ifsc=%s
    WHERE token=%s
    """, (bank_name, account_number, ifsc, token))

    db.commit()

    return "Bank Details Saved Successfully ✅"

@app.route("/admin")
def admin():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="inmba"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM kyc_members ORDER BY id DESC")
    users = cursor.fetchall()

    return render_template("admin.html", users=users)
@app.route("/delete/<int:id>")
def delete(id):
    cursor.execute("DELETE FROM kyc_members WHERE id=%s", (id,))
    db.commit()
    return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)