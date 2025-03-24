# main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import requests
import os
from typing import List, Dict, Any
from datetime import datetime
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi.middleware.cors import CORSMiddleware

# Download nltk data
nltk.download('vader_lexicon')

app = FastAPI()

# Configurações CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ambiente
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./news.db')

# Banco de Dados
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class News(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    content = Column(Text)
    sentiment = Column(String)
    category = Column(String)
    source = Column(String)
    published_at = Column(DateTime)


Base.metadata.create_all(bind=engine)


class NewsResponse(BaseModel):
    status: str
    totalResults: int
    articles: List[Dict[str, Any]]


analyzer = SentimentIntensityAnalyzer()


CATEGORIES = {
    "empresa": ["Apple", "Amazon", "Microsoft", "Tesla", "Google", "Meta"],
    "setor_agrícola": ["Agriculture", "Farming", "Crops", "Fertilizers", "Commodities"],
    "setor_petrolífero": ["Oil", "Petroleum", "Gas", "Energy", "Exxon", "Shell"],
    "setor_bancário": ["Bank", "Finance", "Investment", "Credit", "JP Morgan", "Goldman Sachs"],
    "setor_saúde": ["Health", "Pharmaceutical", "Hospitals", "Biotechnology", "Pfizer", "Moderna", "Johnson & Johnson"],
    "decisões_políticas": ["Government", "Policy", "Regulation", "Law", "President", "Minister"]
}


def categorize_article(text: str) -> str:
    for category, keywords in CATEGORIES.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return category
    return "outros"


def analyze_sentiment(text: str) -> str:
    score = analyzer.polarity_scores(text)
    if score['compound'] >= 0.05:
        return 'positive'
    elif score['compound'] <= -0.05:
        return 'negative'
    else:
        return 'neutral'


def fetch_news_from_newsapi(query: str) -> NewsResponse:
    url = f'https://newsapi.org/v2/everything?q={query}&language=en&apiKey={NEWS_API_KEY}'
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Error fetching news: {response.text}")

    return NewsResponse(**response.json())


@app.get("/health")
def health_check():
    return {"status": "Server is running", "timestamp": datetime.now().isoformat()}
