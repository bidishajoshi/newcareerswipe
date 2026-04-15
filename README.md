# CareerSwipe 🃏

A full-stack job-matching web app powered by **Python Flask**, **MySQL**, and a **Tinder-style swipe UI**. Resumes are parsed and matched to jobs using **TF-IDF + Cosine Similarity**.

---

## Project Structure

```
careerswipe/
├── app.py                        # Main Flask application
├── schema.sql                    # MySQL database schema
├── requirements.txt
├── .env.example                  # Copy to .env and fill in values
├── utils/
│   ├── db.py                     # MySQL connection helper
│   └── tfidf.py                  # Resume parsing + TF-IDF matching
├── templates/
│   ├── base.html                 # Shared navbar/footer layout
│   ├── index.html                # Landing page
│   ├── register_seeker.html      # /seekers folder — job seeker registration
│   ├── register_company.html     # /companies folder — company registration
│   ├── login_seeker.html
│   ├── login_company.html
│   ├── seeker_dashboard.html     # Swipe UI + applications list
│   ├── company_dashboard.html    # Job listings + applicants manager
│   ├── post_job.html
│   └── edit_seeker_profile.html
└── static/
    ├── css/
    │   ├── main.css              # Global styles
    │   └── swipe.css             # Swipe card styles & animations
    ├── js/
    │   ├── main.js               # Flash message auto-dismiss
    │   └── swipe.js              # Drag / touch / keyboard swipe logic
    └── uploads/
        ├── resumes/              # Uploaded seeker resumes
        └── logos/                # Uploaded company logos
```

---

## Quick Setup

### 1. Clone / unzip the project

```bash
cd careerswipe
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up MySQL

```bash
mysql -u root -p < schema.sql
```

This creates the `careerswipe` database and all required tables.

### 5. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your MySQL credentials and Gmail App Password
```

Then load them before running (or use python-dotenv):

```bash
export $(cat .env | xargs)      # Linux/Mac
# Windows PowerShell:
# Get-Content .env | ForEach-Object { $name,$value = $_ -split '=',2; Set-Item "env:$name" $value }
```

Or install python-dotenv and add to the top of `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### 6. Run the app

```bash
python app.py
```

Visit: **http://localhost:5000**

---

## Gmail Email Setup

CareerSwipe sends emails for:
- Email verification on registration
- Resume delivery to company when a seeker swipes right
- Application status updates (accept/reject)

To enable emails:
1. Go to your Google Account → Security → **2-Step Verification** (enable it)
2. Go to **App Passwords** → Generate a password for "Mail"
3. Use that 16-character password as `MAIL_PASSWORD` in your `.env`

> If you just want to test locally without email, the app still works — registration just won't require email verification.

---

## Features

| Feature | Details |
|---|---|
| Dual registration | Separate `/seekers` and `/companies` folders with distinct UI |
| Email verification | Token-based verification before account activation |
| Resume upload | PDF / DOC / DOCX supported |
| TF-IDF matching | Resume keywords matched to job descriptions via Cosine Similarity |
| Swipe UI | Drag, touch, keyboard (←/→ arrow keys) or button swipe |
| Auto email on apply | Resume emailed to company + confirmation to seeker |
| Company dashboard | View all applicants with timestamps, accept/reject candidates |
| Match score badge | Each job card shows % compatibility with seeker's resume |

---

## Tech Stack

- **Backend**: Python 3.11+, Flask 3.0, Flask-Mail
- **Database**: MySQL 8.x
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Resume parsing**: pdfplumber (PDF), python-docx (DOCX)
- **Matching algorithm**: TF-IDF + Cosine Similarity (pure Python, no ML libraries)
- **Email**: Gmail SMTP via Flask-Mail

---

## URL Reference

| URL | Method | Description |
|---|---|---|
| `/` | GET | Landing page |
| `/register/seeker` | GET/POST | Seeker registration |
| `/register/company` | GET/POST | Company registration |
| `/verify/<role>/<token>` | GET | Email verification |
| `/login/seeker` | GET/POST | Seeker login |
| `/login/company` | GET/POST | Company login |
| `/logout` | GET | Logout |
| `/dashboard/seeker` | GET | Seeker dashboard + swipe UI |
| `/dashboard/company` | GET | Company dashboard |
| `/swipe` | POST (JSON) | Record a swipe, send emails |
| `/profile/seeker` | GET/POST | Edit seeker profile |
| `/jobs/post` | GET/POST | Post a new job |
| `/applicant/<id>/<action>` | GET | Accept or reject applicant |


---

## Customisation Tips

- **Add more industries**: Edit the `<select name="industry">` in `register_company.html`
- **Change match threshold colours**: Edit `.match-high / .match-mid / .match-low` in `swipe.css`
- **Pagination for jobs**: Add `LIMIT` and `OFFSET` to the seeker dashboard query in `app.py`
- **Production deployment**: Use `gunicorn app:app` and set `debug=False`
