import json
import os

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SETTINGS_DIR)

with open(os.path.join(SETTINGS_DIR, 'secrets.json')) as secrets_file:
    secrets = json.load(secrets_file)

USE_FLAT_FILES = False
CLIENT_ID = secrets.get("CLIENT_ID")
CLIENT_SECRET = secrets.get("CLIENT_SECRET")
EMAIL_ADDRESS = secrets.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = secrets.get("EMAIL_PASSWORD")
DB_USER = secrets.get("DB_USER")
DB_PASSWORD = secrets.get("DB_PASSWORD")
