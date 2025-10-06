# PDF to CSV + AI Analysis SaaS

A full-stack web application that extracts tables from PDFs (including scanned documents) and provides an AI-powered chat interface for data analysis, cleaning, and visualization.

## Features

- 📄 **PDF Upload & Extraction**
  - Digital PDF table extraction using pdfplumber
  - Scanned PDF OCR using pytesseract + pdf2image
  - Automatic conversion to CSV format

- 🤖 **AI-Powered Data Analysis**
  - Chat interface with OpenAI GPT-4o or Anthropic Claude
  - Tool calling for data operations:
    - `inspect_data` - View structure, columns, and sample rows
    - `clean_data` - Handle missing values, remove duplicates
    - `dedupe` - Remove duplicate rows
    - `detect_outliers` - Find outliers using IQR method
    - `aggregate` - Group by and aggregate operations
    - `pivot` - Create pivot tables
    - `plot` - Generate visualizations (bar, line, scatter, histogram)
    - `export_csv` - Export cleaned data as CSV
    - `export_xlsx` - Export data as Excel files

- 📊 **Data Preview**
  - Interactive table preview with first 10 rows
  - Column information and data shape

- 💬 **Real-time Chat**
  - Conversational AI for data analysis
  - Action logs showing what the AI did
  - Downloadable outputs (CSV, Excel, charts)

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **pdfplumber** - PDF table extraction
- **pytesseract** - OCR for scanned documents
- **pdf2image** - PDF to image conversion
- **OpenAI / Anthropic** - LLM providers
- **Pandas** - Data manipulation
- **Matplotlib** - Data visualization
- **OpenPyXL** - Excel file generation
- **In-memory storage** - For POC (data resets on restart)

### Frontend
- **React + TypeScript** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Lucide React** - Icons

## Prerequisites

- Python 3.12+
- Node.js 20+
- tesseract-ocr (for OCR)
- poppler-utils (for PDF processing)
- OpenAI API key OR Anthropic API key

## Local Setup

### System Dependencies

Install required system packages:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
poetry install
```

3. Create `.env` file with your API keys:
```bash
# Use OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# OR use Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

4. Start the development server:
```bash
poetry run fastapi dev app/main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **Upload PDF**: Drop or select a PDF file containing tables
2. **Preview Data**: View the extracted data in a table format
3. **Chat with AI**: Ask the AI to analyze, clean, or transform your data
4. **Download Results**: Download cleaned data, charts, or Excel files

### Example AI Commands

- "Clean the data and remove duplicates"
- "Summarize totals by month"
- "Find outliers in the price column"
- "Create a bar chart of sales by region"
- "Export the cleaned data as Excel"
- "Aggregate revenue by category and calculate the mean"
- "Create a pivot table with month as rows and product as columns"

## API Endpoints

### `POST /api/upload`
Upload a PDF file for table extraction.

**Request**: multipart/form-data with `file` field
**Response**:
```json
{
  "file_id": "uuid",
  "filename": "example.pdf",
  "csv_path": "uuid.csv",
  "message": "Successfully extracted tables..."
}
```

### `POST /api/chat`
Send a message to the AI agent for data analysis.

**Request**:
```json
{
  "message": "Clean the data and remove duplicates",
  "file_id": "uuid"
}
```

**Response**:
```json
{
  "response": "I've cleaned the data...",
  "files": [
    {
      "file_id": "export_id",
      "filename": "cleaned_data.csv",
      "type": "text/csv"
    }
  ],
  "action_log": [
    "Executing: inspect_data",
    "Executing: clean_data with args ['drop_duplicates']"
  ]
}
```

### `GET /api/preview/{file_id}`
Get a preview of the extracted CSV data.

### `GET /api/download/{file_id}`
Download a generated file (CSV, Excel, or chart).

## Deployment

### Backend Deployment (Fly.io)

The backend can be deployed to Fly.io using:
```bash
cd backend
# Deploy command provided in deployment instructions
```

### Frontend Deployment

The frontend can be deployed using:
```bash
cd frontend
npm run build
# Deploy the dist/ folder
```

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│   Backend    │────────▶│  LLM API    │
│   (React)   │         │  (FastAPI)   │         │ (OpenAI/    │
│             │◀────────│              │◀────────│  Anthropic) │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               │
                        ┌──────▼──────┐
                        │  In-Memory  │
                        │   Storage   │
                        └─────────────┘
```

## Business Model (Suggested)

- **Free Tier**: 3 files/day, ≤5 MB
- **Pro Tier**: $19/mo, unlimited conversions + analysis
- **Team Tier**: $49/mo, batch uploads + saved recipes
- **Credits**: $10 = 25 jobs (pay-as-you-go)

## Future Enhancements

- [ ] PostgreSQL database for persistent storage
- [ ] User authentication and accounts
- [ ] Batch PDF processing
- [ ] Saved analysis recipes
- [ ] WebSocket for real-time streaming
- [ ] File size and rate limiting
- [ ] Team collaboration features
- [ ] API rate limiting and usage tracking

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
