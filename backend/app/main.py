from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
import psycopg
import os
from dotenv import load_dotenv
import uuid
from io import BytesIO
import subprocess
import sys

from app.models import UploadResponse, ChatMessage, ChatResponse
from app.pdf_processor import pdf_processor
from app.ai_agent import DataAnalysisAgent
from app.storage import storage

load_dotenv()

def check_system_dependencies():
    dependencies = {
        'tesseract': 'tesseract-ocr',
        'pdftotext': 'poppler-utils'
    }
    
    missing = []
    for cmd, package in dependencies.items():
        try:
            result = subprocess.run(['which', cmd], 
                          capture_output=True, 
                          check=True)
            if not result.stdout.strip():
                missing.append(package)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(package)
    
    if missing:
        print(f"ERROR: Missing system dependencies: {', '.join(missing)}")
        print("Please install them using: sudo apt-get install -y " + " ".join(missing))
        sys.exit(1)

check_system_dependencies()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_id = str(uuid.uuid4())
    
    try:
        pdf_content = await file.read()
        
        df, extraction_method = pdf_processor.extract_tables_from_pdf(pdf_content, file.filename)
        
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        csv_path = f"{file_id}.csv"
        
        storage.store_file(file_id, file.filename, csv_path, df)
        storage.store_temp_file(csv_path, csv_buffer.getvalue())
        
        method_msg = "digital PDF" if extraction_method == "digital" else "scanned PDF using OCR"
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            csv_path=csv_path,
            message=f"Successfully extracted tables from {method_msg}. Found {len(df)} rows and {len(df.columns)} columns."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_msg: ChatMessage):
    df = storage.get_dataframe(chat_msg.file_id)
    if df is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="No API key configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
        agent = DataAnalysisAgent(provider=provider)
        
        response_text, generated_files, action_log = agent.process_request(chat_msg.message, df)
        
        files_info = []
        for file_data in generated_files:
            file_id = f"{chat_msg.file_id}_{file_data['file_id']}"
            storage.store_temp_file(file_id, file_data['content'])
            files_info.append({
                "file_id": file_id,
                "filename": file_data['filename'],
                "type": file_data['type']
            })
        
        return ChatResponse(
            response=response_text,
            files=files_info,
            action_log=action_log
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    file_content = storage.get_temp_file(file_id)
    if file_content is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    content_type = "application/octet-stream"
    filename = file_id
    
    if file_id.endswith('.csv'):
        content_type = "text/csv"
    elif file_id.endswith('.xlsx'):
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_id.endswith('.png'):
        content_type = "image/png"
    
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/api/preview/{file_id}")
async def preview_csv(file_id: str):
    df = storage.get_dataframe(file_id)
    if df is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    preview_data = {
        "columns": list(df.columns),
        "rows": df.head(10).to_dict('records'),
        "total_rows": len(df),
        "total_columns": len(df.columns)
    }
    
    return preview_data
