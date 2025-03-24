from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import requests
import os
from typing import List, Dict, Any
from datetime import datetime
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
#DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./news.db')
#DATABASE_URL = os.getenv('DATABASE_URL', 
DATABASE_URL = 'sqlite:////home/site/news.db'

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
    url = Column(String)  # Adiciona o link da notícia

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
    "setor_saúde": ["Health", "Pharmaceutical", "Hospitals", "Biotechnology", "Pfizer", "Moderna"],
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

@app.get("/health")
def health_check():
    return {"status": "Server is running", "timestamp": datetime.now().isoformat()}

@app.get("/fetch-news/{query}")
def fetch_news(query: str, db: Session = Depends(get_db)):
    url = f'https://newsapi.org/v2/everything?q={query}&language=en&apiKey={NEWS_API_KEY}'
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Error fetching news: {response.text}")

    data = response.json()
    for article in data.get("articles", []):
        sentiment = analyze_sentiment(article["title"])
        category = categorize_article(article["title"])
        
        news_item = News(
            title=article["title"],
            description=article.get("description", ""),
            content=article.get("content", ""),
            sentiment=sentiment,
            category=category,
            source=article.get("source", {}).get("name", "Unknown"),
            published_at=datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"),
            url=article.get("url")  # Salva o link da notícia
        )
        
        db.add(news_item)
    
    db.commit()
    return {"status": data["status"], "totalResults": data["totalResults"], "articles": data["articles"]}

@app.get("/news")
def get_news(db: Session = Depends(get_db)):
    news_items = db.query(News).all()
    return [{
        "title": n.title, 
        "description": n.description, 
        "sentiment": n.sentiment, 
        "category": n.category, 
        "source": n.source, 
        "published_at": n.published_at,
        "url": n.url  # Retorna o link da notícia
    } for n in news_items]

@app.get("/test-sentiment")
def test_sentiment():
    text = "The stock market is performing very well today."
    score = analyzer.polarity_scores(text)
    return {"text": text, "score": score}

@app.get("/create-database")
def create_database():
    try:
        Base.metadata.create_all(bind=engine)
        
        # Criar um arquivo de teste no diretório persistente /home/site/
        with open("/home/site/backend_test.txt", "w") as f:
            f.write("Teste de gravação bem-sucedido no diretório /home/site/.")
        
        return {"message": "Database created successfully, and test file written in /home/site/."}
    except Exception as e:
        return {"error": str(e)}


@app.get("/check-directory")
def check_directory():
    try:
        # Verificar se o arquivo kudu_test.txt é visível pelo backend
        file_path = "/tmp/kudu_test.txt"
        if os.path.exists(file_path):
            return {"message": "O arquivo kudu_test.txt foi encontrado pelo backend.", "file_path": file_path}
        else:
            return {"message": "O backend NÃO conseguiu encontrar o arquivo kudu_test.txt.", "file_path": file_path}
    except Exception as e:
        return {"error": str(e)}
