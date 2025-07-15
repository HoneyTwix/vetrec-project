# Quick Start Guide

Get VetRec Medical Action Extraction System running in 5 minutes!

## Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key

## 1. Clone and Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd vetrec-project

# Run the setup script
python setup.py
```

## 2. Configure API Keys

Edit `backend/.env`:
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
DATABASE_URL=sqlite:///./vetrec.db  # Use SQLite for quick start
```

## 3. Start the Backend

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

## 4. Start the Frontend

In a new terminal:
```bash
cd frontend
npm run dev
```

The UI will be available at `http://localhost:3000`

## 5. Test the System

1. Open `http://localhost:3000` in your browser
2. Copy the sample transcript from `backend/sample_transcript.txt`
3. Paste it into the transcript field
4. Click "Extract Actions"
5. View the structured results!

## Sample Transcript

```
Doctor: Good morning, Mrs. Johnson. How are you feeling today?

Patient: I've been having these headaches for the past week, and they're getting worse. I also noticed some dizziness when I stand up quickly.

Doctor: I see. Let me check your blood pressure first. [Checks blood pressure] Your blood pressure is elevated at 160/95. Have you been taking your lisinopril regularly?

Patient: I ran out about a week ago and haven't been able to get to the pharmacy.

Doctor: That explains the elevated blood pressure. I'm going to prescribe a refill of lisinopril 10mg once daily, and I want you to monitor your blood pressure at home. Also, let's schedule some blood work to check your kidney function and cholesterol levels.

Nurse: I'll order the blood work for tomorrow morning, and I'll call in the prescription to your pharmacy.

Doctor: Mrs. Johnson, I want you to return in 2 weeks for a follow-up to check your blood pressure. If it's still elevated, we might need to adjust your medication. Also, please make sure to take your medication at the same time each day.
```

## Expected Results

The system should extract:

- **Follow-up Tasks**: Schedule follow-up in 2 weeks, order blood work
- **Medication Instructions**: Lisinopril 10mg once daily
- **Client Reminders**: Monitor blood pressure at home, pick up medication
- **Clinician To-dos**: Schedule follow-up, order blood work, call in prescription

## Troubleshooting

### Backend Issues
- Check that your OpenAI API key is valid
- Ensure all Python dependencies are installed: `pip install -r requirements.txt`
- For database issues, try using SQLite: `DATABASE_URL=sqlite:///./vetrec.db`

### Frontend Issues
- Make sure the backend is running on port 8000
- Check that all Node.js dependencies are installed: `npm install`
- Verify the API URL in `frontend/.env.local`

### BAML Issues
- Ensure the BAML file is in the correct location: `backend/baml/extract.baml`
- Check that the BAML SDK is properly installed
- Verify the OpenAI API key has sufficient credits

## Next Steps

- Try different types of medical transcripts
- Add user IDs to test the memory feature
- Explore the evaluation metrics in `backend/evaluator/`
- Deploy to production using Docker

## API Testing

Test the API directly:

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Doctor: Patient presents with hypertension. Prescribing lisinopril 10mg daily. Follow up in 2 weeks.",
    "notes": "Patient has history of high blood pressure"
  }'
```

## Docker Deployment

For production deployment:

```bash
cd backend/docker
docker-compose up -d
```

This will start both the backend and PostgreSQL database in containers. 