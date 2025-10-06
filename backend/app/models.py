from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    csv_path: str
    message: str

class ChatMessage(BaseModel):
    message: str
    file_id: str

class ChatResponse(BaseModel):
    response: str
    files: List[Dict[str, str]]
    action_log: List[str]

class FileInfo(BaseModel):
    file_id: str
    original_filename: str
    csv_path: str
    created_at: datetime
    dataframe_shape: Optional[tuple] = None
