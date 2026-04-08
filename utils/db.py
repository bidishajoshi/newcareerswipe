import mysql.connector
from flask import g, current_app
import os

def get_db():
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host=os.environ.get("DB_HOST", "localhost"),
                  port= int(os.environ.get("DB_PORT", 3306)),
                user=os.environ.get("DB_USER", "root"),
                password=os.environ.get("DB_PASSWORD", ""),
                database=os.environ.get("DB_NAME", "careerswipe")
            )
            print("✅ Database connected successfully")
        except Exception as e:
            print("❌ DB connection error:", e)
            raise
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        print("🔌 Database connection closed")

def init_app(app):
    app.teardown_appcontext(close_db)