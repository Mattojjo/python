from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List
from datetime import datetime

DATABASE_URL = "sqlite:///./app.db"  # SQLite file created in project directory

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    date = Column(DateTime, default=func.now(), index=True)

Base.metadata.create_all(bind=engine)



app = FastAPI()

# Enable CORS for frontend access (all origins allowed for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():  # Dependency for database session in each request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/items/", response_model=dict)
def create_item(item: dict, db: Session = Depends(get_db)):
    db_item = Item(
        name=item["name"], 
        description=item.get("description", ""),
        )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)  # Refresh to obtain the auto-generated ID
    return {"id": db_item.id, "name": db_item.name, "description": db_item.description, "date": db_item.date}


@app.get("/items/", response_model=List[dict])
def read_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return [{"id": i.id, "name": i.name, "description": i.description, "date": i.date} for i in items]


@app.get("/items/{item_id}", response_model=dict)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item.id, "name": item.name, "description": item.description, "date": item.date}


@app.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
