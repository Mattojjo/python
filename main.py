from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

# Configuration for JWT tokens
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change this to a random secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context - uses bcrypt to hash passwords securely
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme - tells FastAPI to expect a Bearer token in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

DATABASE_URL = "sqlite:///./app.db"  # SQLite file created in project directory

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# User model - stores username, email, and hashed password
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


# Item model - stores items with a user relationship
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    date = Column(DateTime, default=func.now(), index=True)
    user_id = Column(Integer, index=True)  # Links item to the user who created it

Base.metadata.create_all(bind=engine)


# Utility functions for password hashing
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token with optional expiration"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Dependency to get current user from token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())) -> User:
    """Extract user from JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


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


# ======================= AUTHENTICATION ENDPOINTS =======================

@app.post("/signup")
def signup(username: str, email: str, password: str, db: Session = Depends(get_db)):
    """
    Register a new user
    - username: unique username
    - email: user's email
    - password: plain text password (will be hashed)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user with hashed password
    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint - returns JWT token
    - username: user's username
    - password: user's password
    """
    # Find user in database
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # Verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# ======================= ITEM ENDPOINTS (WITH AUTHENTICATION) =======================

@app.post("/items/", response_model=dict)
def create_item(item: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new item (requires authentication)"""
    db_item = Item(
        name=item["name"], 
        description=item.get("description", ""),
        user_id=current_user.id  # Associate item with the logged-in user
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"id": db_item.id, "name": db_item.name, "description": db_item.description, "date": db_item.date}


@app.get("/items/", response_model=List[dict])
def read_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all items for the logged-in user (requires authentication)"""
    items = db.query(Item).filter(Item.user_id == current_user.id).all()
    return [{"id": i.id, "name": i.name, "description": i.description, "date": i.date} for i in items]


@app.get("/items/{item_id}", response_model=dict)
def read_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a single item by ID (only if it belongs to the logged-in user)"""
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item.id, "name": item.name, "description": item.description, "date": item.date}


@app.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete an item by ID (only if it belongs to the logged-in user)"""
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
