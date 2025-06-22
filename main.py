import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from datetime import date
from contextlib import asynccontextmanager

# --- Database and Model Imports ---
from database import get_session, create_db_and_tables
from models import User, JournalEntry, EntryStatus
from auth import get_current_user
from sqlmodel import Session, select

# --- LangChain Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

# --- Load Environment Variables ---
from dotenv import load_dotenv
load_dotenv()

# --- Explicitly get the API Key ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

# --- NEW: Modern Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code here runs on startup
    print("Lifespan startup: Creating database and tables...")
    create_db_and_tables()
    print("Lifespan startup: Database is ready.")
    yield
    # Code here would run on shutdown
    print("Lifespan shutdown.")

# --- Initialize FastAPI and AI Model ---
app = FastAPI(
    title="Simplified AI Journal API",
    description="Analyzes journal entries and saves to a database.",
    lifespan=lifespan # Use the new lifespan manager
)

# --- Pass the API key to the model ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GEMINI_API_KEY, temperature=0.7)


# ==============================================================================
#      SIMPLIFIED ANALYSIS AND DATABASE INTEGRATION
# ==============================================================================

# 1. Define the Pydantic "Blueprint" for the SIMPLIFIED AI output.
class SimplifiedAnalysis(BaseModel):
    sentimentScore: int = Field(
        description="Sentiment of the text rated on a scale from -10 to 10, where -10 is extremely negative, 0 is neutral, and 10 is extremely positive."
    )
    counsel: str = Field(
        description="A short paragraph of constructive, supportive advice based on the entry."
    )

# 2. Define the Pydantic model for the incoming request data.
class EntryCreateRequest(BaseModel):
    text: str
    entry_status: EntryStatus = EntryStatus.PUBLISHED

# 3. Create the Output Parser for our new simplified blueprint.
parser = PydanticOutputParser(pydantic_object=SimplifiedAnalysis)

# 4. Create the new, SIMPLIFIED Prompt Template.
prompt_template_str = """
You are a compassionate journaling assistant. Analyze the following journal entry.
Follow the instructions and format your response to match the format instructions, no matter what!
{format_instructions}
---
JOURNAL ENTRY:
{entry}
"""
prompt = PromptTemplate(
    template=prompt_template_str,
    input_variables=["entry"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

@app.post("/analyze-entry", response_model=SimplifiedAnalysis)
def analyze_and_save_entry(
    entry_data: EntryCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Analyzes a journal entry for sentiment and advice, saves the entry to the
    database for the current user, and returns the AI's analysis.
    """
    if not entry_data.text:
        raise HTTPException(status_code=400, detail="Entry text cannot be empty.")

    final_prompt = prompt.invoke({"entry": entry_data.text})
    try:
        output = llm.invoke(final_prompt)
        analysis_result = parser.parse(output.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get a structured response from the AI: {e}")

    try:
        db_journal_entry = JournalEntry(
            user_id=current_user.user_id,
            entry_date=date.today(),
            text=entry_data.text,
            sentiment_score=analysis_result.sentimentScore,
            entry_status=entry_data.entry_status,
            word_count=len(entry_data.text.split()),
            ai_suggestion={"counsel": analysis_result.counsel} 
        )
        
        session.add(db_journal_entry)
        session.commit()
        session.refresh(db_journal_entry)
        
    except Exception as db_e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save the entry to the database: {db_e}")

    return analysis_result

@app.get("/")
def read_root():
    return {"status": "Simplified AI Journal API is running"}
