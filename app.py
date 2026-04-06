
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
import os, uuid, json
from datetime import datetime

# ── TEST DATABASE CONNECTION ────────────────────────────────────────────────
try:
    db = get_db()
    cur = db.cursor()
    cur.execute("SHOW TABLES;")
    print("Tables in database:", cur.fetchall())
except Exception as e:
    print("Database connection failed:", e)

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass 

from utils.tfidf import parse_resume, match_resume_to_job
from utils.db import get_db, init_app as init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "careerswipe-secret-2026")
init_db(app)

# ── Mail config (Used for job applications and status updates) ───────────────
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "your@gmail.com")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "your_app_password")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME", "your@gmail.com")
mail = Mail(app)

UPLOAD_FOLDER = os.path.join("static", "uploads")
RESUME_FOLDER = os.path.join(UPLOAD_FOLDER, "resumes")
LOGO_FOLDER   = os.path.join(UPLOAD_FOLDER, "logos")
ALLOWED_RESUME = {"pdf", "doc", "docx"}
ALLOWED_LOGO   = {"png", "jpg", "jpeg"}

os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(LOGO_FOLDER, exist_ok=True)

def allowed_file(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

# ── Email Helpers ────────────────────────────────────────────────────────────
def send_application_emails(seeker_email, seeker_name, company_email, company_name, job_title, resume_path):
    # To Company
    msg1 = Message(f"New applicant for {job_title}", recipients=[company_email])
    msg1.html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#00c896">CareerSwipe</h2>
      <p><b>{seeker_name}</b> has applied for <b>{job_title}</b>.</p>
      <p>Resume is attached.</p>
    </div>"""
    if resume_path and os.path.exists(resume_path):
        with app.open_resource(resume_path) as fp:
            msg1.attach(os.path.basename(resume_path), "application/octet-stream", fp.read())
    mail.send(msg1)

    # To Seeker
    msg2 = Message(f"Application sent to {company_name}", recipients=[seeker_email])
    msg2.html = f"<h2>CareerSwipe</h2><p>Your application for <b>{job_title}</b> was sent!</p>"
    mail.send(msg2)

# ════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register/seeker", methods=["GET", "POST"])
def register_seeker():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        email = request.form["email"].strip().lower()
        
        cur.execute("SELECT id FROM seekers WHERE email=%s", (email,))
        if cur.fetchone():
            flash("Email already registered.", "error")
            return redirect(url_for("register_seeker"))

        resume_file = request.files.get("resume")
        resume_path = ""
        if resume_file and allowed_file(resume_file.filename, ALLOWED_RESUME):
            fname = secure_filename(f"{uuid.uuid4()}_{resume_file.filename}")
            resume_path = os.path.join(RESUME_FOLDER, fname)
            resume_file.save(resume_path)

        cur.execute("""
            INSERT INTO seekers
              (first_name, last_name, email, password_hash, phone, education, experience, skills, resume_path, is_verified, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1,NOW())
        """, (
            request.form["first_name"], request.form["last_name"], email,
            generate_password_hash(request.form["password"]),
            request.form.get("phone",""), request.form.get("education",""),
            request.form.get("experience",""), request.form.get("skills", ""), resume_path
        ))
        db.commit()
        flash("Account created! You can log in now.", "success")
        return redirect(url_for("login_seeker"))
    return render_template("register_seeker.html")

@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        email = request.form["email"].strip().lower()

        cur.execute("SELECT id FROM companies WHERE email=%s", (email,))
        if cur.fetchone():
            flash("Email already registered.", "error")
            return redirect(url_for("register_company"))

        logo_file = request.files.get("logo")
        logo_path = ""
        if logo_file and allowed_file(logo_file.filename, ALLOWED_LOGO):
            fname = secure_filename(f"{uuid.uuid4()}_{logo_file.filename}")
            logo_path = os.path.join(LOGO_FOLDER, fname)
            logo_file.save(logo_path)

        cur.execute("""
            INSERT INTO companies
              (company_name, email, password_hash, description, industry, website, logo_path, is_verified, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,1,NOW())
        """, (
            request.form["company_name"], email,
            generate_password_hash(request.form["password"]),
            request.form.get("description",""), request.form.get("industry",""),
            request.form.get("website",""), logo_path
        ))
        db.commit()
        flash("Company registered!", "success")
        return redirect(url_for("login_company"))
    return render_template("register_company.html")

@app.route("/login/seeker", methods=["GET", "POST"])
def login_seeker():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM seekers WHERE email=%s", (request.form["email"].strip().lower(),))
        user = cur.fetchone()
        if user and check_password_hash(user["password_hash"], request.form["password"]):
            session["seeker_id"] = user["id"]
            session["seeker_name"] = user["first_name"]
            return redirect(url_for("seeker_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login_seeker.html")

@app.route("/login/company", methods=["GET", "POST"])
def login_company():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM companies WHERE email=%s", (request.form["email"].strip().lower(),))
        co = cur.fetchone()
        if co and check_password_hash(co["password_hash"], request.form["password"]):
            session["company_id"] = co["id"]
            session["company_name"] = co["company_name"]
            return redirect(url_for("company_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login_company.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ════════════════════════════════════════════════════════════════════════════
#  SEEKER FEATURES
# ════════════════════════════════════════════════════════════════════════════
@app.route("/dashboard/seeker")
def seeker_dashboard():
    if "seeker_id" not in session:
        return redirect(url_for("login_seeker"))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM seekers WHERE id=%s", (session["seeker_id"],))
    seeker = cur.fetchone()

    cur.execute("""
        SELECT j.*, c.company_name, c.logo_path
        FROM job_listings j
        JOIN companies c ON j.company_id = c.id
        WHERE j.id NOT IN (SELECT job_id FROM job_swipes WHERE seeker_id=%s)
        ORDER BY j.created_at DESC LIMIT 20
    """, (session["seeker_id"],))
    jobs = cur.fetchall()

    resume_text = parse_resume(seeker["resume_path"]) if seeker["resume_path"] and os.path.exists(seeker["resume_path"]) else ""
    for job in jobs:
        job["match_score"] = match_resume_to_job(resume_text, f"{job['description']} {job['required_skills']}") if resume_text else 0

    jobs.sort(key=lambda x: x["match_score"], reverse=True)

    cur.execute("""
        SELECT j.title, c.company_name, s.created_at, s.status
        FROM job_swipes s
        JOIN job_listings j ON s.job_id = j.id
        JOIN companies c ON j.company_id = c.id
        WHERE s.seeker_id=%s AND s.direction='right'
        ORDER BY s.created_at DESC
    """, (session["seeker_id"],))
    applications = cur.fetchall()

    return render_template("seeker_dashboard.html", seeker=seeker, jobs=jobs, applications=applications)

@app.route("/swipe", methods=["POST"])
def swipe():
    if "seeker_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    job_id, direction = data.get("job_id"), data.get("direction")

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id FROM job_swipes WHERE seeker_id=%s AND job_id=%s", (session["seeker_id"], job_id))
    if cur.fetchone():
        return jsonify({"status": "already_swiped"})

    cur.execute("INSERT INTO job_swipes (seeker_id, job_id, direction, status, created_at) VALUES (%s,%s,%s,'pending',NOW())",
                (session["seeker_id"], job_id, direction))
    db.commit()

    if direction == "right":
        cur.execute("SELECT * FROM seekers WHERE id=%s", (session["seeker_id"],))
        seeker = cur.fetchone()
        cur.execute("SELECT j.*, c.email AS company_email, c.company_name FROM job_listings j JOIN companies c ON j.company_id=c.id WHERE j.id=%s", (job_id,))
        job = cur.fetchone()
        try:
            send_application_emails(seeker["email"], f"{seeker['first_name']} {seeker['last_name']}", job["company_email"], job["company_name"], job["title"], seeker["resume_path"])
        except: pass

    return jsonify({"status": "ok", "direction": direction})

@app.route("/profile/seeker", methods=["GET", "POST"])
def edit_seeker_profile():
    if "seeker_id" not in session:
        return redirect(url_for("login_seeker"))
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        resume_file = request.files.get("resume")
        resume_path = request.form.get("existing_resume", "")
        if resume_file and allowed_file(resume_file.filename, ALLOWED_RESUME):
            fname = secure_filename(f"{uuid.uuid4()}_{resume_file.filename}")
            resume_path = os.path.join(RESUME_FOLDER, fname)
            resume_file.save(resume_path)

        cur.execute("""
            UPDATE seekers SET first_name=%s, last_name=%s, phone=%s, education=%s, experience=%s, skills=%s, resume_path=%s
            WHERE id=%s
        """, (request.form["first_name"], request.form["last_name"], request.form.get("phone",""),
              request.form.get("education",""), request.form.get("experience",""), request.form.get("skills",""),
              resume_path, session["seeker_id"]))
        db.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("seeker_dashboard"))

    cur.execute("SELECT * FROM seekers WHERE id=%s", (session["seeker_id"],))
    seeker = cur.fetchone()
    return render_template("edit_seeker_profile.html", seeker=seeker)

# ════════════════════════════════════════════════════════════════════════════
#  COMPANY FEATURES
# ════════════════════════════════════════════════════════════════════════════
@app.route("/dashboard/company")
def company_dashboard():
    if "company_id" not in session:
        return redirect(url_for("login_company"))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM companies WHERE id=%s", (session["company_id"],))
    company = cur.fetchone()
    cur.execute("SELECT * FROM job_listings WHERE company_id=%s ORDER BY created_at DESC", (session["company_id"],))
    jobs = cur.fetchall()
    cur.execute("""
        SELECT s.id AS seeker_id, s.first_name, s.last_name, s.email, s.skills, s.resume_path, 
               j.title AS job_title, sw.created_at AS applied_at, sw.status, sw.id AS swipe_id
        FROM job_swipes sw
        JOIN seekers s ON sw.seeker_id = s.id
        JOIN job_listings j ON sw.job_id = j.id
        WHERE j.company_id=%s AND sw.direction='right'
        ORDER BY sw.created_at DESC
    """, (session["company_id"],))
    applicants = cur.fetchall()
    return render_template("company_dashboard.html", company=company, jobs=jobs, applicants=applicants)

@app.route("/jobs/post", methods=["GET", "POST"])
def post_job():
    if "company_id" not in session:
        return redirect(url_for("login_company"))
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO job_listings (company_id, title, description, required_skills, location, job_type, salary, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())",
                    (session["company_id"], request.form["title"], request.form["description"], request.form.get("required_skills",""),
                     request.form.get("location",""), request.form.get("job_type","Full-time"), request.form.get("salary","")))
        db.commit()
        flash("Job posted successfully!", "success")
        return redirect(url_for("company_dashboard"))
    return render_template("post_job.html")

@app.route("/applicant/<int:swipe_id>/<action>")
def update_applicant(swipe_id, action):
    if "company_id" not in session:
        return redirect(url_for("login_company"))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("UPDATE job_swipes SET status=%s WHERE id=%s", (action + "ed", swipe_id))
    db.commit()
    
    cur.execute("SELECT s.email, s.first_name, j.title FROM job_swipes sw JOIN seekers s ON sw.seeker_id=s.id JOIN job_listings j ON sw.job_id=j.id WHERE sw.id=%s", (swipe_id,))
    row = cur.fetchone()
    if row:
        msg = Message(f"Application Update: {row['title']}", recipients=[row["email"]])
        msg.html = f"<p>Hi {row['first_name']}, your application for {row['title']} was {action}ed.</p>"
        try: mail.send(msg)
        except: pass
    flash(f"Applicant {action}ed.", "success")
    return redirect(url_for("company_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
