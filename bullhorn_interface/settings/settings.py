import os

from mylittlehelpers import InterfaceSettings

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))

# InterfaceSettings(SETTINGS_DIR, CONF_NAME)
InterfaceSettings(SETTINGS_DIR, "bullhorn_conf.conf")

secrets, conf = InterfaceSettings.load_secrets(), InterfaceSettings.load_conf()

USE_FLAT_FILES = conf["USE_FLAT_FILES"]
CLIENT_ID = secrets["CLIENT_ID"]
CLIENT_SECRET = secrets["CLIENT_SECRET"]
EMAIL_ADDRESS = secrets["EMAIL_ADDRESS"]
EMAIL_PASSWORD = secrets["EMAIL_PASSWORD"]
DB_USER = secrets["DB_USER"]
DB_PASSWORD = secrets["DB_PASSWORD"]