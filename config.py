import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")  # À définir sur Render
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
