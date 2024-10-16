from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from model import Users

from passlib.context import CryptContext
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = 'Password_secret_key'
ALGORITHM = 'HS256'

class CreateUserRequest(BaseModel):
    id : int
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: str

#for the user-defined token style we wanted, this class is created.
class token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_depcy_injctn = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(username == Users.username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user
#here above, if the user is true, return user itself for JWT issuance.

def create_access_token(username: str, user_id: str, expires_delta: timedelta):
    encoder = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encoder.update({'exp': expires})
    return jwt.encode(encoder, SECRET_KEY, algorithm= ALGORITHM)

#This fn. is used for other API endpoints to be able to verify the current user
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username= payload.get('sub')
        user_id= payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Failed authentication, sign up to create a user")
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Failed authentication, sign up to create a user")



@router.post("/sign_up/", status_code = status.HTTP_201_CREATED)
async def create_user(db: db_depcy_injctn, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        role = create_user_request.role,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        is_active = True
    )
    db.add(create_user_model)
    db.commit()

@router.post("/token", response_model= token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_depcy_injctn):

    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Failed authentication, sign up to create a user")   
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}