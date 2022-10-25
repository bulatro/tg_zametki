import os
from dotenv import load_dotenv


load_dotenv()

token = os.environ.get("TOKEN")

db_host = os.environ.get("DB_SETTINGS_HOST")
db_port = os.environ.get("DB_SETTINGS_PORT")
db_database = os.environ.get("DB_SETTINGS_DATABASE")
db_user = os.environ.get("DB_SETTINGS_USER")
db_password = os.environ.get("DB_SETTINGS_PASSWORD")