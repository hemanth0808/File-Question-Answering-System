import os
import aiohttp
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openai
from .file_processing import FileProcessor
from .config import config
from transformers import pipeline
from pydantic import BaseModel
from typing import Dict, Any, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Hugging Face pipeline
# qa_pipeline = pipeline(
#     "question-answering",
#     model="distilbert-base-cased-distilled-squad",
#     tokenizer="distilbert-base-cased-distilled-squad"
# )

qa_pipeline = pipeline(
    "question-answering",
    model="deepset/roberta-base-squad2",
    tokenizer="deepset/roberta-base-squad2",
    # truncation="only_second",  # Only truncate the context, not the question
    # max_seq_len=512,  # Standard transformer limit
    # stride=128  # Allow some overlap between chunks
)

# OpenAI setup (will only be used if API key is provided)
if config.OPENAI_API_KEY:
    openai.api_key = config.OPENAI_API_KEY
    OPENAI_ENABLED = True
else:
    OPENAI_ENABLED = False
    print("OpenAI API key not found. Using Hugging Face models only.")

os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

class QuestionRequest(BaseModel):
    question: str
    filename: str
    data_type: str
    content: Dict[str, Any]
    use_openai: Optional[bool] = False 

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not FileProcessor.allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    filepath = os.path.join(config.UPLOAD_FOLDER, file.filename)
    
    try:
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())
        
        processed_data = FileProcessor.process_file(filepath)
        return {"filename": file.filename, "data": processed_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    try:
        if request.data_type == "structured":
            context = "\n".join([f"{k}: {v}" for item in request.content['data'] for k, v in item.items()])
        else:
            context = request.content['content']

        # Use OpenAI if requested and API key is available
        if request.use_openai and OPENAI_ENABLED:
            response = await ask_openai(request.question, context)
            return response
        elif request.use_openai and not OPENAI_ENABLED:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API not configured. Add OPENAI_API_KEY to .env to enable."
            )
        else:
            # Use Hugging Face 
            result = qa_pipeline(question=request.question, context=context)
            return {
                "answer": result['answer'],
                "confidence": float(result['score']),
                "model": "roberta-base-squad2",
                "service": "huggingface"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def ask_openai(question: str, context: str):
    """Handle questions using OpenAI API"""
    try:
        prompt = f"""Answer the question based on the context below. Keep answers concise.
        If the question can't be answered from the context, say "I don't know".

        Context: {context[:15000]}

        Question: {question}
        Answer:"""
        
        async with aiohttp.ClientSession() as session:
            openai.aiosession.set(session)
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You answer questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
        
        return {
            "answer": response.choices[0].message.content.strip(),
            "confidence": 1.0,
            "model": "gpt-3.5-turbo",
            "service": "openai"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)