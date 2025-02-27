from dotenv import load_dotenv
import os

load_dotenv(override=True)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER") 
PROJECT_ID = os.getenv("PROJECT_ID")
INSTANCE_NAME = os.getenv("INSTANCE_NAME")
REGION = os.getenv("REGION")
DB_PASSWORD = os.getenv("DB_PASSWORD")
API_KEY = os.getenv("GOOGLE_API_KEY")
TABLE_NAME = os.getenv("TABLE_NAME")