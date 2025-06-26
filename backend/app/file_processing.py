import os
import pandas as pd
import pdfplumber
import json
from typing import Union, Dict, List
from pathlib import Path

# from backend.app.config import Config
from .config import Config

class FileProcessor:
    @staticmethod
    def allowed_file(filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @staticmethod
    def process_file(filepath: str) -> Union[Dict, str]:
        ext = Path(filepath).suffix.lower()
        
        if ext == '.csv':
            return FileProcessor._process_csv(filepath)
        elif ext == '.json':
            return FileProcessor._process_json(filepath)
        elif ext == '.pdf':
            return FileProcessor._process_pdf(filepath)
        elif ext == '.txt':
            return FileProcessor._process_txt(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def _process_csv(filepath: str) -> Dict:
        df = pd.read_csv(filepath)
        return {
            "type": "structured",
            "data": df.to_dict(orient="records"),
            "columns": list(df.columns)
        }

    @staticmethod
    def _process_json(filepath: str) -> Dict:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return {
            "type": "structured",
            "data": data
        }

    @staticmethod
    def _process_pdf(filepath: str) -> str:
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return {
            "type": "unstructured",
            "content": text
        }

    @staticmethod
    def _process_txt(filepath: str) -> str:
        with open(filepath, 'r') as f:
            content = f.read()
        return {
            "type": "unstructured",
            "content": content
        }