import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import pandas as pd
import io
import subprocess
from typing import List, Tuple, Optional

class PDFProcessor:
    def __init__(self):
        pass
    
    def _check_ocr_dependencies(self) -> Optional[str]:
        try:
            subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "tesseract-ocr is not installed or not in PATH"
        
        try:
            subprocess.run(['pdftotext', '-v'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "poppler-utils is not installed or not in PATH"
        
        return None
    
    def extract_tables_from_pdf(self, pdf_content: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
        pdfplumber_error = None
        try:
            df = self._extract_with_pdfplumber(pdf_content)
            if df is not None and not df.empty:
                return df, "digital"
        except Exception as e:
            pdfplumber_error = str(e)
            print(f"pdfplumber extraction failed: {e}")
        
        try:
            dep_error = self._check_ocr_dependencies()
            if dep_error:
                raise Exception(f"OCR dependencies missing: {dep_error}")
            
            df = self._extract_with_ocr(pdf_content)
            if df is not None and not df.empty:
                return df, "ocr"
        except Exception as e:
            ocr_error = str(e)
            print(f"OCR extraction failed: {e}")
            error_msg = f"Failed to extract tables from PDF using both pdfplumber and OCR."
            if pdfplumber_error:
                error_msg += f" PDFPlumber error: {pdfplumber_error}."
            error_msg += f" OCR error: {ocr_error}"
            raise Exception(error_msg)
        
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
        
        if len(all_rows) < 2:
            return None
        
        headers = all_rows[0]
        data_rows = all_rows[1:]
        
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
        
        if len(rows) < 2:
            return None
        
        max_cols = max(len(row) for row in rows)
        
        for row in rows:
            while len(row) < max_cols:
                row.append("")
        
        headers = rows[0]
        data_rows = rows[1:]
        
        df = pd.DataFrame(data_rows, columns=headers)
        return df

pdf_processor = PDFProcessor()
