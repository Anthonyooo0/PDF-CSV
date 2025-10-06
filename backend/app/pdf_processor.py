import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import pandas as pd
import io
from typing import List, Tuple

class PDFProcessor:
    def __init__(self):
        pass
    
    def extract_tables_from_pdf(self, pdf_content: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
        try:
            df = self._extract_with_pdfplumber(pdf_content)
            if df is not None and not df.empty:
                return df, "digital"
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
        
        try:
            df = self._extract_with_ocr(pdf_content)
            if df is not None and not df.empty:
                return df, "ocr"
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            raise Exception("Failed to extract tables from PDF using both pdfplumber and OCR")
        
        raise Exception("No tables found in PDF")
    
    def _extract_with_pdfplumber(self, pdf_content: bytes) -> pd.DataFrame:
        all_rows = []
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 0:
                        all_rows.extend(table)
        
        if not all_rows:
            return None
        
        headers = all_rows[0] if all_rows else []
        data_rows = all_rows[1:] if len(all_rows) > 1 else []
        
        if not headers or not data_rows:
            return pd.DataFrame(all_rows)
        
        df = pd.DataFrame(data_rows, columns=headers)
        return df
    
    def _extract_with_ocr(self, pdf_content: bytes) -> pd.DataFrame:
        images = convert_from_bytes(pdf_content)
        
        all_text = []
        for img in images:
            text = pytesseract.image_to_string(img)
            all_text.append(text)
        
        combined_text = "\n".join(all_text)
        
        lines = [line.strip() for line in combined_text.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        rows = []
        for line in lines:
            parts = [p.strip() for p in line.split() if p.strip()]
            if parts:
                rows.append(parts)
        
        if not rows:
            return None
        
        max_cols = max(len(row) for row in rows)
        
        for row in rows:
            while len(row) < max_cols:
                row.append("")
        
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        if not data_rows:
            return pd.DataFrame(rows)
        
        df = pd.DataFrame(data_rows, columns=headers)
        return df

pdf_processor = PDFProcessor()
