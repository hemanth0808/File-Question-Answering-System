import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'json'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

config = Config()