# FastAPI Best Practices

## Overview

This skill covers FastAPI patterns and best practices for building robust, scalable, and secure APIs.

## Key Topics

### 1. Project Structure

Recommended FastAPI project structure:

```python
project/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   └── items.py
│   │   └── __init__.py
│   ├── config/
│   │   └── settings.py
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   └── services/
│       ├── base.py
│       └── auth.py
├── tests/
│   ├── conftest.py
│   │   └── test_api.py
└── docs/
    └── openapi.yaml
```

### 2. Application Setup

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="API",
    description="API description",
    version="1.0.0",
    docs_url="/docs" if settings.env == "development" else None,
    redoc_url="/redoc" if settings.env == "development" else None,
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

if settings.trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

# Routes
app.include_router(v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

### 3. CRUD Routers

```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return None
```

### 4. Dependencies

```python
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import jwt
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated=["auto"])

# JWT utilities
class JWTService:
    SECRET_KEY = "your-secret-key"
    ALGORITHM = "HS256"
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        from datetime import datetime, timedelta
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWTService.SECRET_KEY, algorithm=JWTService.ALGORITHM)
        return encoded_jwt

# Database dependency
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./data.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
def get_current_user(token: str = None):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, JWTService.SECRET_KEY, algorithms=[JWTService.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    return username

def require_auth(user: str = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user
```

### 5. Models with Pydantic

```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from typing_extensions import Self

class BaseBaseModel(BaseModel):
    id: int
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str
    
    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Must be a valid email address")
        return v.lower()

class UserCreate(UserBase):
    password: str
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]

class UserResponse(UserBase, BaseBaseModel):
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, orm_obj: Self) -> Self:
        # Custom conversion logic here
        data = orm_obj.__dict__
        return cls(**data)
```

### 6. Testing

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.database.models import User

client = TestClient(app)

def test_create_user(test_db):
    """Test creating a new user."""
    response = client.post(
        "/api/v1/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_list_users(test_db):
    """Test listing users."""
    # Create a test user
    client.post(
        "/api/v1/users",
        json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpassword123",
        },
    )
    
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all("username" in user and "email" in user for user in data)

def test_get_user(test_db):
    """Test getting a single user."""
    # Create a test user
    create_response = client.post(
        "/api/v1/users",
        json={
            "username": "testuser3",
            "email": "test3@example.com",
            "password": "testpassword123",
        },
    )
    user = create_response.json()
    
    response = client.get(f"/api/v1/users/{user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user["id"]
    assert data["username"] == "testuser3"

def test_update_user(test_db):
    """Test updating a user."""
    # Create a test user
    create_response = client.post(
        "/api/v1/users",
        json={
            "username": "testuser4",
            "email": "test4@example.com",
            "password": "testpassword123",
        },
    )
    user = create_response.json()
    
    # Update the user
    update_response = client.put(
        f"/api/v1/users/{user['id']}",
        json={
            "email": "updated@example.com",
        },
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == user["id"]
    assert data["username"] == "testuser4"
    assert data["email"] == "updated@example.com"

def test_delete_user(test_db):
    """Test deleting a user."""
    # Create a test user
    create_response = client.post(
        "/api/v1/users",
        json={
            "username": "testuser5",
            "email": "test5@example.com",
            "password": "testpassword123",
        },
    )
    user = create_response.json()
    
    response = client.delete(f"/api/v1/users/{user['id']}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(f"/api/v1/users/{user['id']}")
    assert get_response.status_code == 404

@pytest.fixture
def test_db(monkeypatch):
    """Fixture for database with test data."""
    from app.database import SessionLocal
    
    # Create an in-memory SQLite database for tests
    test_engine = create_engine("sqlite:///:memory:")
    test_session = sessionmaker(bind=test_engine)()
    
    # Monkey-patch the database dependency
    def override_get_db():
        yield test_session
    
    monkeypatch.setattr("app.api.v1.users.get_db", override_get_db)
    
    # Create test user
    test_user = User(
        username="fixtureuser",
        email="fixture@example.com",
        hashed_password=pwd_context.hash("testpassword"),
    )
    test_session.add(test_user)
    test_session.commit()
    
    yield
    
    test_session.close()
```

### 7. Environment Variables

```bash
# .env
DATABASE_URL=sqlite:///./data.db
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
TRUSTED_HOSTS=*.example.com,localhost,127.0.0.1
```

### 8. Logging

```python
# app/logging.py
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

log_directory = "logs"
Path(log_directory).mkdir(exist_ok=True)

# Application logger
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)

# File handler with rotation
file_handler = RotatingFileHandler(
    f"{log_directory}/app.log",
    maxBytes=10485760,  # 10MB
    backupCount=5,
)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
app_logger.addHandler(file_handler)
app_logger.addHandler(console_handler)
app_logger.propagate = False

# Error logger
error_logger = logging.getLogger("error")
error_logger.setLevel(logging.ERROR)
error_handler = RotatingFileHandler(
    f"{log_directory}/error.log",
    maxBytes=10485760,
    backupCount=5,
)
error_handler.setFormatter(formatter)
error_logger.addHandler(error_handler)
error_logger.propagate = False
```

### 9. Error Handling

```python
# app/api/errors.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Union
import traceback

class APIException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code

async def validation_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Validation Error",
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )

async def generic_exception_handler(request: Request, exc: Exception):
    # Log the full traceback for debugging
    error_logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_host": request.client.host,
            "user_agent": request.headers.get("User-Agent"),
        },
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )
```