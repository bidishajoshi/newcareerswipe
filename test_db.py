from flask import Flask
from utils.db import get_db, init_app

app = Flask(__name__)
init_app(app)

with app.app_context():
    db = get_db()
    cur = db.cursor()
    cur.execute("SHOW TABLES;")
    print("Tables:", cur.fetchall())