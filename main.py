from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List

DATABASE_URL = "sqlite:///./app.db"  # SQLite file created in project directory

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Item model - stores items
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    date = Column(DateTime, default=func.now(), index=True)
    user_id = Column(Integer, index=True)  # Dummy field for development

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


# ======================= ITEM ENDPOINTS =======================


@app.post("/items/", response_model=dict)
def create_item(item: dict, db: Session = Depends(get_db)):
    """Create a new item (dev mode - no authentication)"""
    db_item = Item(
        title=item["title"], 
        description=item.get("description", ""),
        user_id=1  # Use a dummy user ID (1) for development
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"id": db_item.id, "title": db_item.title, "description": db_item.description, "date": db_item.date}


@app.get("/items/", response_model=List[dict])
def read_items(db: Session = Depends(get_db)):
    """Get all items (dev mode - no authentication)"""
    items = db.query(Item).all()  # Get all items without user filtering
    return [{"id": i.id, "title": i.title, "description": i.description, "date": i.date} for i in items]


@app.get("/items/{item_id}", response_model=dict)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """Get a single item by ID (dev mode - no authentication)"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item.id, "title": item.title, "description": item.description, "date": item.date}


@app.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Delete an item by ID (dev mode - no authentication)"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}

app.put("items/{item_id}", response_model=dict)
def edit_item(item_id: int, updated_item: dict, db: Session = Depends(get_db)):
    """Edit an item by ID (dev mode - no authentication)"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.title = updated_item.get("title", item.title)
    item.description = updated_item.get("description", item.description)

    db.commit()
    db.refresh(item)
    return {"id": item.id, "title": item.title, "description": item.description, "date": item.date}