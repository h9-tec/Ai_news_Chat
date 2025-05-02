from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from .models import Subscriber
from .database import SessionLocal
from .qa import summary_today, answer
from .scraper import run as scrape_run
import threading
from .email_service import EmailService

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SubscribeRequest(BaseModel):
    email: EmailStr

class ChatRequest(BaseModel):
    question: str
    backend: str = "groq"  # or "ollama"

@app.post('/subscribe')
def subscribe(req: SubscribeRequest):
    db = SessionLocal()
    try:
        existing = db.query(Subscriber).filter_by(email=req.email).first()
        email_service = EmailService()
        if existing and existing.is_active:
            return {"message": "Already subscribed"}
        elif existing:
            existing.is_active = True
            db.commit()
            # Send confirmation email for reactivation
            email_service.send_simple_email(
                to_email=req.email,
                subject="Subscription Confirmed: AI News Aggregator",
                html_body="<p>You have subscribed to our AI news. Thank you!</p>"
            )
            return {"message": "Subscription reactivated"}
        else:
            new_sub = Subscriber(email=req.email)
            db.add(new_sub)
            db.commit()
            # Send confirmation email for new subscription
            email_service.send_simple_email(
                to_email=req.email,
                subject="Subscription Confirmed: AI News Aggregator",
                html_body="<p>You have subscribed to our AI news. Thank you!</p>"
            )
            return {"message": "Subscribed successfully"}
    finally:
        db.close()

@app.post('/unsubscribe')
def unsubscribe(req: SubscribeRequest):
    db = SessionLocal()
    try:
        existing = db.query(Subscriber).filter_by(email=req.email).first()
        if not existing or not existing.is_active:
            raise HTTPException(status_code=404, detail="Email not subscribed")
        existing.is_active = False
        db.commit()
        return {"message": "Unsubscribed successfully"}
    finally:
        db.close()

@app.get('/summarize')
def summarize(backend: str = "groq"):
    try:
        summary = summary_today(backend)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/chat')
def chat(req: ChatRequest):
    try:
        response = answer(req.question, req.backend)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/scrape')
def scrape():
    # Run scraping in a background thread to avoid blocking
    thread = threading.Thread(target=scrape_run)
    thread.start()
    return {"message": "Scraping started in background."} 