from fastapi import FastAPI
import model
from database import engine
from typing import Annotated



from routers import author, todos

app = FastAPI()

model.Base.metadata.create_all(bind=engine)

app.include_router(author.router)
app.include_router(todos.router)

