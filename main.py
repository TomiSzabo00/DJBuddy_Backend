from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from sql_app import models
from database import get_db, engine
import sql_app.models as models
import sql_app.schemas as schemas
from sql_app.repositories import UserRepo, EventRepo, SongRepo
from sqlalchemy.orm import Session
import uvicorn
from typing import List
from fastapi.encoders import jsonable_encoder

SECRET_KEY = "5736f10d085954fd50e4706e4eabd16a420100588937319231822869bbdfe363"
ALGORITHM = "HS256"

app = FastAPI(title="Sample FastAPI Application",
    description="Sample FastAPI Application with Swagger and Sqlalchemy",
    version="1.0.0",)

models.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("main:app", port=9000, reload=True)

@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})

@app.post("/login", response_model=schemas.User,status_code=200)
async def login_for_access_token(login_data: schemas.LoginData, db: Session = Depends(get_db)):
    user = await UserRepo.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.post('/users', tags=["User"],response_model=schemas.User,status_code=201)
async def create_user(user_request: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a User and store it in the database
    """
    
    db_user = UserRepo.fetch_by_email(db, email=user_request.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists!")

    return await UserRepo.create(db=db, user=user_request)


@app.get('/users/{user_id}', tags=["User"],response_model=schemas.User)
def get_user(user_id: str,db: Session = Depends(get_db)):
    """
    Get the User with the given ID
    """
    db_user = UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    return db_user

@app.delete('/users/{user_id}', tags=["User"])
async def delete_user(user_id: str,db: Session = Depends(get_db)):
    """
    Delete the User with the given ID
    """
    db_user = UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    await UserRepo.delete(db,user_id)
    return "User deleted successfully!"

@app.put('/users/{user_id}', tags=["User"],response_model=schemas.User)
async def update_user(user_id: str, user_request: schemas.User, db: Session = Depends(get_db)):
    """
    Update a User stored in the database
    """
    db_user = UserRepo.fetch_by_id(db, user_id=user_id)
    if db_user:
        update_item_encoded = jsonable_encoder(user_request)
        db_user.profilePicUrl = update_item_encoded['profilePicUrl']
        return await UserRepo.update(db=db,user_data=db_user)
    else:
        raise HTTPException(status_code=400, detail="User not found with the given ID")

@app.post('/events', tags=["Event"],response_model=schemas.Event,status_code=201)
async def create_event(event_request: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Create an Event and store it in the database
    """
    return await EventRepo.create(db=db, event=event_request)

@app.get('/events/{event_id}', tags=["Event"],response_model=schemas.Event)
def get_event(event_id: str,db: Session = Depends(get_db)):
    """
    Get the Event with the given ID
    """
    db_event = EventRepo.fetch_by_uuid(db,event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found with the given ID")
    return db_event

@app.post('/songs', tags=["Song"],response_model=schemas.Song,status_code=201)
async def create_song(song_request: schemas.SongCreate, db: Session = Depends(get_db)):
    """
    Create a Song and store it in the database
    """
    return await SongRepo.create(db=db, song=song_request)