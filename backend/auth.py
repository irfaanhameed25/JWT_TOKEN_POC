from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import JWTError, jwt


# to initiate the fastapi app
app = FastAPI(title="JWT Auth & RBAC POC")


# Enable CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configuration
SECRET_KEY = "super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ==========================================
# 1. TEMPORARY IN-MEMORY DATABASE (DICTIONARY)
# ==========================================
fake_users_db = {
    "admin_user": {
        "user_id": 100,
        "username": "admin_user",
        "password": "adminpassword",
        "role": "admin",
        "department": "Executive",
        "is_active": True
    },
    "manager_boss": {
        "user_id": 101,
        "username": "manager_boss",
        "password": "managerpassword",
        "role": "manager",
        "department": "Sales",
        "is_active": True
    },
    "regular_guy": {
        "user_id": 103,
        "username": "regular_guy",
        "password": "userpassword",
        "role": "user",
        "department": "Support",
        "is_active": True
    }
}


# ==========================================
# 2. TOKEN GENERATION FUNCTIONS
# ==========================================
def create_access_token(user_id: int, username: str, role: str, department: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "department": department,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ==========================================
# 3. REQUEST SCHEMAS (Pydantic)
# ==========================================
class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ==========================================
# 4. DEPENDENCIES & AUTHENTICATION WRAPPERS
# ==========================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates Access Tokens for protected routes"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Ensure it is an ACCESS token, not a refresh token
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Access token required."
            )
            
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "department": payload.get("department")
        }
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (Token expired or invalid)"
        )


def require_role(required_role: str):
    """Role-Based Wrapper Dependency"""
    def role_dependency(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires '{required_role}' role."
            )
        return current_user
    return role_dependency


# ==========================================
# 5. ENDPOINTS
# ==========================================


@app.post("/auth/login")
def login(body: LoginRequest):
    user = fake_users_db.get(body.username)
    
    if not user or user["password"] != body.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="User account is inactive")
    
    # Generate both tokens
    access_token = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
        department=user["department"]
    )
    refresh_token = create_refresh_token(user_id=user["user_id"])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user["role"]
    }


@app.post("/auth/refresh")
def refresh_token(body: RefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Ensure it is explicitly a REFRESH token
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type. Refresh token required.")
            
        user_id = payload.get("sub")
        
        # Find user details from dictionary database to populate the new access token
        user = next((u for u in fake_users_db.values() if str(u["user_id"]) == user_id), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Issue a new access token
        new_access_token = create_access_token(
            user_id=user["user_id"],
            username=user["username"],
            role=user["role"],
            department=user["department"]
        )
        
        return {"access_token": new_access_token, "token_type": "bearer"}
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


# --- Protected Routes ---


@app.get("/dashboard")
def general_dashboard(current_user: dict = Depends(get_current_user)):
    """Open to any user with a valid access token"""
    return {"message": f"Welcome back, {current_user['username']}!", "user_info": current_user}


@app.get("/manager/reports")
def manager_reports(current_user: dict = Depends(require_role("manager"))):
    """Wrapped specifically for managers"""
    return {"message": "Here are the secret manager reports.", "department": current_user["department"]}


@app.get("/admin/system-logs")
def admin_logs(current_user: dict = Depends(require_role("admin"))):
    """Wrapped specifically for admins"""
    return {"message": "Here are the confidential system logs.", "admin": current_user["username"]}