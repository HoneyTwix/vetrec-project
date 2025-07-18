# 🏥 VetRec Medical Action Extraction System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-13+-black.svg)](https://nextjs.org)
[![BAML](https://img.shields.io/badge/BAML-Boundary%20ML-orange.svg)](https://boundaryml.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A comprehensive AI-powered system for extracting actionable items from medical visit transcripts using **BAML** and **Large Language Models**. Built with **FastAPI** backend and **Next.js** frontend.

## ✨ Features

- 🤖 **AI-Powered Extraction**: Advanced LLM-based extraction using BAML and OpenAI
- 🧠 **Memory Context**: Leverages previous visits for enhanced extraction quality
- 📋 **Comprehensive Categories**: Extracts follow-up tasks, medication instructions, client reminders, and clinician to-dos
- 📊 **Quality Evaluation**: Built-in metrics and evaluation system for assessing extraction quality
- 🎨 **Modern UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- 📤 **Export Functionality**: Export results as JSON for further processing and integration

## 🏗️ Project Structure

```
vetrec-project/
├── 📁 backend/                    # FastAPI backend application
│   ├── 📁 api/
│   │   └── 📄 extract.py          # FastAPI endpoints
│   ├── 📁 baml/
│   │   └── 📄 extract.baml        # BAML task definition
│   ├── 📁 db/
│   │   ├── 📄 models.py           # SQLAlchemy models
│   │   ├── 📄 schema.py           # Pydantic schemas
│   │   └── 📄 crud.py             # Database operations
│   ├── 📁 evaluator/
│   │   └── 📄 metrics.py          # Quality evaluation metrics
│   ├── 📁 utils/
│   │   ├── 📄 embedding_service.py # Vector embeddings for memory
│   │   └── 📄 pdf_extractor.py    # PDF processing utilities
│   ├── 📄 main.py                 # FastAPI application entry point
│   ├── 📄 requirements.txt        # Python dependencies
│   └── 📄 .env.example           # Environment variables template
└── 📁 frontend/                   # Next.js frontend application
    ├── 📁 src/
    │   ├── 📁 app/
    │   │   ├── 📄 page.tsx        # Main UI component
    │   │   └── 📁 extract/
    │   │       └── 📄 page.tsx    # Extraction interface
    │   ├── 📁 components/
    │   │   ├── 📄 TranscriptExtractor.tsx
    │   │   └── 📄 SOPManager.tsx
    │   └── 📁 lib/
    │       └── 📄 api.ts          # API client
    ├── 📄 package.json            # Node.js dependencies
    └── 📄 README.md
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/vetrec-project.git
cd vetrec-project

# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=sqlite:///./vetrec.db  # For development
# DATABASE_URL=postgresql://user:pass@localhost:5432/vetrec  # For production
```

```bash
# Run the FastAPI server
python main.py
```

🌐 **Backend will be available at:** [http://localhost:8000](http://localhost:8000)

📚 **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
```

Edit `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

```bash
# Run the development server
npm run dev
```

🌐 **Frontend will be available at:** [http://localhost:3000](http://localhost:3000)

## 🔧 Configuration

### Environment Variables

#### Backend (`.env`)
| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `DATABASE_URL` | Database connection string | `sqlite:///./vetrec.db` |
| `MODEL_NAME` | LLM model to use | `gpt-4` |
| `TEMPERATURE` | Model temperature | `0.1` |

#### Frontend (`.env.local`)
| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |

## 🤖 BAML Integration

The system uses **BAML (Boundary ML)** for structured LLM prompting. The main extraction task is defined in `backend/baml/extract.baml`:

### Key Features
- **Structured Input**: Medical transcript, optional notes, and previous visit context
- **Structured Output**: Follow-up tasks, medication instructions, client reminders, and clinician to-dos
- **Model Configuration**: GPT-4 with temperature 0.1 for consistent results
- **Memory Integration**: Leverages previous visits for context-aware extraction

### BAML File Recognition
BAML files are automatically recognized when:
1. ✅ Located in the `baml/` directory
2. ✅ Have the `.baml` extension
3. ✅ BAML client is properly initialized

## 📡 API Endpoints

### Extract Medical Actions
**`POST /api/v1/extract`**

Extract actionable items from a medical transcript.

<details>
<summary><strong>Request Example</strong></summary>

```json
{
  "transcript_text": "Patient presents with symptoms of depression...",
  "notes": "Additional clinical context...",
  "user_id": 123
}
```
</details>

<details>
<summary><strong>Response Example</strong></summary>

```json
{
  "transcript": {
    "id": 1,
    "transcript_text": "Patient presents with symptoms of depression...",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "extraction": {
    "follow_up_tasks": [
      "Schedule follow-up appointment in 2 weeks",
      "Monitor medication side effects"
    ],
    "medication_instructions": [
      "Sertraline 50mg once daily",
      "Take with food"
    ],
    "client_reminders": [
      "Call if experiencing severe side effects",
      "Keep mood diary"
    ],
    "clinician_todos": [
      "Review blood work results",
      "Assess suicide risk"
    ]
  }
}
```
</details>

### Memory Context
**`GET /api/v1/memory/{user_id}`**

Retrieve previous visits for memory context.

### Get Extraction
**`GET /api/v1/extraction/{extraction_id}`**

Retrieve a specific extraction result.

## 🗄️ Database Schema

### Core Tables

<details>
<summary><strong>Users</strong></summary>

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
</details>

<details>
<summary><strong>VisitTranscripts</strong></summary>

```sql
CREATE TABLE visit_transcripts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    transcript_text TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
</details>

<details>
<summary><strong>ExtractionResults</strong></summary>

```sql
CREATE TABLE extraction_results (
    id INTEGER PRIMARY KEY,
    transcript_id INTEGER REFERENCES visit_transcripts(id),
    follow_up_tasks JSON,
    medication_instructions JSON,
    client_reminders JSON,
    clinician_todos JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
</details>

## 📊 Quality Evaluation

The system includes comprehensive evaluation metrics in `backend/evaluator/metrics.py`:

| Metric | Description | Formula |
|--------|-------------|---------|
| **Precision** | How many extracted items are correct | `TP / (TP + FP)` |
| **Recall** | How many actual items were extracted | `TP / (TP + FN)` |
| **F1 Score** | Harmonic mean of precision and recall | `2 × (P × R) / (P + R)` |
| **Category-specific** | Separate scores for each extraction category | Per-category metrics |

## 🛠️ Development

### Adding New Extraction Categories

1. **Update BAML Schema** (`backend/baml/extract.baml`)
2. **Update Database Models** (`backend/db/models.py`)
3. **Update Frontend Types** (`frontend/lib/api.ts`)
4. **Update UI Components** (`frontend/src/app/page.tsx`)

### Customizing LLM Prompts

Edit the prompt section in `backend/baml/extract.baml` to modify:
- 🎯 System instructions
- 📝 Input format requirements
- 📤 Output structure
- ⚙️ Model configuration

### Adding Evaluation Metrics

Extend functions in `backend/evaluator/metrics.py` to add:
- 🎯 Custom similarity measures
- 🏥 Domain-specific metrics
- 📊 Confidence scoring

## 🚀 Deployment

### Backend Deployment

1. **Database Setup**
   ```bash
   # PostgreSQL (recommended for production)
   createdb vetrec
   ```

2. **Environment Configuration**
   ```bash
   # Set production environment variables
   export OPENAI_API_KEY="your-production-key"
   export DATABASE_URL="postgresql://user:pass@host:5432/vetrec"
   ```

3. **Deploy with Docker**
   ```bash
   docker build -t vetrec-backend .
   docker run -p 8000:8000 vetrec-backend
   ```

### Frontend Deployment

1. **Build Application**
   ```bash
   npm run build
   ```

2. **Deploy to Vercel**
   ```bash
   npx vercel --prod
   ```

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><strong>BAML Issues</strong></summary>

- ✅ Ensure your OpenAI API key is valid
- ✅ Check BAML file syntax is correct
- ✅ Verify model name in BAML configuration
- ✅ Check API rate limits
</details>

<details>
<summary><strong>Database Issues</strong></summary>

- ✅ **SQLite**: Ensure database file is writable
- ✅ **PostgreSQL**: Check connection string and permissions
- ✅ Run migrations: `python -c "from db.models import Base; from sqlalchemy import create_engine; engine = create_engine('your-db-url'); Base.metadata.create_all(engine)"`
</details>

<details>
<summary><strong>Frontend Issues</strong></summary>

- ✅ Ensure backend is running and accessible
- ✅ Check CORS configuration
- ✅ Verify API endpoint URLs
- ✅ Check browser console for errors
</details>

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. 🍴 **Fork** the repository
2. 🌿 **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. 📤 **Push** to the branch (`git push origin feature/amazing-feature`)
5. 🔄 **Open** a Pull Request

### Development Guidelines

- 📝 Write clear commit messages
- 🧪 Add tests for new functionality
- 📚 Update documentation
- 🎨 Follow existing code style

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **BAML Team** for the amazing LLM framework
- **OpenAI** for providing the GPT models
- **FastAPI** for the excellent web framework
- **Next.js** for the React framework
- **Tailwind CSS** for the utility-first CSS framework

---

<div align="center">

**Made with ❤️ for the medical community**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/vetrec-project?style=social)](https://github.com/yourusername/vetrec-project/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/vetrec-project?style=social)](https://github.com/yourusername/vetrec-project/network)
[![GitHub issues](https://img.shields.io/github/issues/yourusername/vetrec-project)](https://github.com/yourusername/vetrec-project/issues)

</div>