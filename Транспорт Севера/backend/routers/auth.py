import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from bson import ObjectId

from config import settings
from database import get_database
from models import UserInDB, UserCreate

logger = logging.getLogger("transport_severa.auth")
router = APIRouter(prefix="/auth", tags=["Аутентификация"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

def hash_password(password: str) -> str:
    # Reliable SHA-256 with salt for guaranteed cross-platform compatibility
    salt = "sever_transport_salt_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные или срок сессии истек",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db_obj = get_database()
    user = None
    if db_obj.is_connected:
        user = await db_obj.db.users.find_one({"username": username})
    else:
        user = db_obj._fallback_store.get("users", {}).get(username)

    if user is None:
        raise credentials_exception
    return user

def require_role(roles: list[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется одна из ролей: {', '.join(roles)}"
            )
        return current_user
    return role_checker

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db_obj = get_database()
    username = form_data.username
    password = form_data.password

    user = None
    if db_obj.is_connected:
        user = await db_obj.db.users.find_one({"username": username})
    else:
        user = db_obj._fallback_store.get("users", {}).get(username)

    if not user or not verify_password(password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учетная запись заблокирована администратором"
        )

    access_token = create_access_token(data={"sub": user["username"], "role": user.get("role", "DISPATCHER")})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.get("_id") or user.get("id")),
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "role": user.get("role", "DISPATCHER")
        }
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": str(current_user.get("_id") or current_user.get("id")),
        "username": current_user["username"],
        "full_name": current_user.get("full_name", ""),
        "role": current_user.get("role", "DISPATCHER")
    }

@router.get("/users")
async def list_users(current_user: dict = Depends(require_role(["ADMIN"]))):
    db_obj = get_database()
    users = []
    if db_obj.is_connected:
        cursor = db_obj.db.users.find()
        raw = await cursor.to_list(length=100)
        for u in raw:
            users.append({
                "id": str(u.get("_id")),
                "username": u["username"],
                "full_name": u.get("full_name", ""),
                "role": u.get("role", "DISPATCHER"),
                "is_active": u.get("is_active", True),
                "created_at": u.get("created_at")
            })
    else:
        for u in db_obj._fallback_store.get("users", {}).values():
            users.append({
                "id": str(u.get("id") or u.get("_id")),
                "username": u["username"],
                "full_name": u.get("full_name", ""),
                "role": u.get("role", "DISPATCHER"),
                "is_active": u.get("is_active", True),
                "created_at": u.get("created_at")
            })
    return users

@router.post("/users")
async def create_user(user_in: UserCreate, current_user: dict = Depends(require_role(["ADMIN"]))):
    db_obj = get_database()
    user_doc = {
        "username": user_in.username,
        "full_name": user_in.full_name,
        "role": user_in.role,
        "is_active": user_in.is_active,
        "hashed_password": hash_password(user_in.password),
        "created_at": datetime.utcnow()
    }
    if db_obj.is_connected:
        existing = await db_obj.db.users.find_one({"username": user_in.username})
        if existing:
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
        res = await db_obj.db.users.insert_one(user_doc)
        user_doc["_id"] = str(res.inserted_id)
    else:
        if "users" not in db_obj._fallback_store:
            db_obj._fallback_store["users"] = {}
        if user_in.username in db_obj._fallback_store["users"]:
            raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
        uid = str(ObjectId())
        user_doc["id"] = uid
        user_doc["_id"] = uid
        db_obj._fallback_store["users"][user_in.username] = user_doc

    return {"message": "Пользователь успешно создан", "username": user_in.username}
