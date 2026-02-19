
# Import FastAPI and related modules for building the API
from fastapi import FastAPI, HTTPException, Depends
# Import CORS middleware to allow frontend requests from other origins
from fastapi.middleware.cors import CORSMiddleware
# Import SQLAlchemy modules for database handling
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
# For type hints
from typing import List

# SQLite database URL (file will be created in project directory)
DATABASE_URL = "sqlite:///./app.db"


# Create the database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# Create a session factory for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base class for our ORM models
Base = declarative_base()


# Define the Item model (table)
class Item(Base):
    __tablename__ = "items"  # Table name in the database
    id = Column(Integer, primary_key=True, index=True)  # Unique ID
    name = Column(String, index=True)  # Name of the item
    description = Column(String, index=True)  # Description of the item

# Create the database tables (if they don't exist)
Base.metadata.create_all(bind=engine)



# Create the FastAPI app
app = FastAPI()


# Enable CORS so frontend (React) can access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Dependency to get a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create a new item (POST /items/)
# The frontend sends a JSON object with 'name' and optionally 'description'.
@app.post("/items/", response_model=dict)
def create_item(item: dict, db: Session = Depends(get_db)):
    # Create an Item object from the request data
    db_item = Item(name=item["name"], description=item.get("description", ""))
    db.add(db_item)  # Add to session
    db.commit()      # Save to database
    db.refresh(db_item)  # Refresh to get the new ID
    return {"id": db_item.id, "name": db_item.name, "description": db_item.description}


# Get all items (GET /items/)
# Returns a list of all items in the database.
@app.get("/items/", response_model=List[dict])
def read_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()  # Query all items
    return [{"id": i.id, "name": i.name, "description": i.description} for i in items]


# Get a single item by ID (GET /items/{item_id})
# Returns the item with the given ID, or 404 if not found.
@app.get("/items/{item_id}", response_model=dict)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item.id, "name": item.name, "description": item.description}


# Delete an item by ID (DELETE /items/{item_id})
# Removes the item from the database if it exists.
@app.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)  # Remove from database
    db.commit()      # Save changes
    return {"ok": True}
