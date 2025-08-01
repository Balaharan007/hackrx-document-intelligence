from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_type = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    content = Column(Text)
    processed = Column(String, default="pending")  # pending, processed, failed


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding_id = Column(String)  # Pinecone vector ID


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text)
    document_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    decision = Column(String)  # Approved, Rejected
    amount = Column(Float, nullable=True)
    justification = Column(Text)  # JSON string


# Database connection
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
