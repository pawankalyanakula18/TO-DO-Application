from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from model import Todos
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean
from pydantic import BaseModel, Field
from .author import get_current_user


router = APIRouter()

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_depcy_injctn = Annotated[Session, Depends(get_db)]
user_depcy_injctn = Annotated[dict, Depends(get_current_user)]


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all_todos(db: db_depcy_injctn):
    return db.query(Todos).all()

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo_by_id(db: db_depcy_injctn, todo_id: int = Path(gt=0)):
    todo_tuple = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_tuple is not None:
        return todo_tuple
    else:
        raise HTTPException(status_code=404, detail='ToDo not found...')

@router.post("/todo/create", status_code=status.HTTP_201_CREATED)
async def create_db_tuple(user: user_depcy_injctn, db: db_depcy_injctn, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail= "Failed authentication, sign up to create a user")
    todo_model = Todos(**todo_request.dict(), owner= user.get('id'))
    # .dict() in BaseModel is outdated..
    db.add(todo_model)
    db.commit() 

@router.put("/todo/{todo_id}", status_code = status.HTTP_204_NO_CONTENT)
async def update_todos(db: db_depcy_injctn, todo_request: TodoRequest, todo_id: int=Path(gt=0)):
    todo_model = db.query(Todos).filter(todo_id == Todos.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='ToDo not found to UPDATE...')
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.add(todo_model)
    db.commit()

@router.delete("/todos/delete/{todo_id}",status_code = status.HTTP_204_NO_CONTENT)
async def delete_tuple(db: db_depcy_injctn, todo_id: int=Path(gt=0)):
    todo_model = db.query(Todos).filter(todo_id == Todos.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='ToDo not found to DELETE...')
    db.query(Todos).filter(todo_id == Todos.id).delete()
    db.commit()


