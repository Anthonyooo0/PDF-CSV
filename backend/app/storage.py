from typing import Dict, Optional
import pandas as pd
from datetime import datetime
from app.models import FileInfo

class InMemoryStorage:
    def __init__(self):
        self.files: Dict[str, FileInfo] = {}
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.temp_files: Dict[str, bytes] = {}
    
    def store_file(self, file_id: str, filename: str, csv_path: str, df: pd.DataFrame):
        self.files[file_id] = FileInfo(
            file_id=file_id,
            original_filename=filename,
            csv_path=csv_path,
            created_at=datetime.now(),
            dataframe_shape=df.shape
        )
        self.dataframes[file_id] = df
    
    def get_dataframe(self, file_id: str) -> Optional[pd.DataFrame]:
        return self.dataframes.get(file_id)
    
    def update_dataframe(self, file_id: str, df: pd.DataFrame):
        self.dataframes[file_id] = df
        if file_id in self.files:
            self.files[file_id].dataframe_shape = df.shape
    
    def store_temp_file(self, file_id: str, content: bytes):
        self.temp_files[file_id] = content
    
    def get_temp_file(self, file_id: str) -> Optional[bytes]:
        return self.temp_files.get(file_id)
    
    def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        return self.files.get(file_id)

storage = InMemoryStorage()
