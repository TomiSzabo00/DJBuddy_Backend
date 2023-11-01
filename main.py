from fastapi import Depends, FastAPI, HTTPException, status, WebSocket
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

# MARK: Websockets
event_websockets = {}
event_theme_websockets = {}

if __name__ == "__main__":
    uvicorn.run("main:app", port=9000, reload=True)

@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})

# MARK: Login

@app.post("/users/login", response_model=schemas.User,status_code=200)
async def login_user(login_data: schemas.LoginData, db: Session = Depends(get_db)):
    user = await UserRepo.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# MARK: User

@app.post('/users/register', tags=["User"],response_model=schemas.User,status_code=201)
async def register_user(user_request: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a User and store it in the database
    """
    
    db_user = await UserRepo.fetch_by_email(db, email=user_request.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists!")

    return await UserRepo.create(db=db, user=user_request)

@app.get('/users/{user_id}/events', tags=["User"],response_model=List[schemas.Event])
async def get_user_events(user_id: str,db: Session = Depends(get_db)):
    """
    Get the Events associated with the given User ID
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    return db_user.events

@app.post('/users/{user_id}/events/{event_id}', tags=["User"])
async def add_event_to_user(user_id: str, event_id: str, db: Session = Depends(get_db)):
    """
    Add an Event to a User
    """
    db_user = await UserRepo.fetch_by_id(db, user_id=user_id)
    db_event = await EventRepo.fetch_by_uuid(db, uuid=event_id)
    if db_user and db_event:
        db_user.events.append(db_event)
        db.commit()
        db.refresh(db_user)
        return db_user
    else:
        raise HTTPException(status_code=400, detail="User or Event not found with the given ID")


# MARK: Event

@app.post('/events', tags=["Event"],response_model=schemas.Event,status_code=201)
async def create_event(event_request: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Create an Event and store it in the database
    """
    return await EventRepo.create(db=db, event=event_request)

@app.get('/events/{event_id}', tags=["Event"],response_model=schemas.Event)
async def get_event(event_id: str,db: Session = Depends(get_db)):
    """
    Get the Event with the given ID
    """
    db_event = await EventRepo.fetch_by_uuid(db,event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found with the given ID")
    return db_event

@app.websocket("/ws/events/{event_id}")
async def websocket_endpoint_for_event(websocket: WebSocket, event_id: str):
    await websocket.accept()
    # check if event_websockets has key for event_id and if there is a list of websockets
    if event_id not in event_websockets:
        event_websockets[event_id] = []
    event_websockets[event_id].append(websocket)
    while True:
        # dont receive just keep connection alive
        await websocket.receive_text()

@app.websocket("/ws/events/{event_id}/themes")
async def websocket_endpoint_for_event_theme(websocket: WebSocket, event_id: str):
    await websocket.accept()
    # check if event_websockets has key for event_id and if there is a list of websockets
    if event_id not in event_theme_websockets:
        event_theme_websockets[event_id] = []
    event_theme_websockets[event_id].append(websocket)
    while True:
        # dont receive just keep connection alive
        await websocket.receive_text()

async def send_event_update_to_websocket(event_id: str, event: schemas.Event):
    if event_id in event_websockets:
        event_schema = schemas.Event.from_orm(event)
        for websocket in event_websockets[event_id]:
            try: 
                await websocket.send_json(event_schema.model_dump())
                print("!!!!!  Sent event update to websocket, new theme: " + event.theme)
            except:
                print("!!!!!  Failed to send event update to websocket, it was probably closed")

async def send_event_theme_update_to_websocket(event_id: str, theme: schemas.Event):
    if event_id in event_theme_websockets:
        for websocket in event_theme_websockets[event_id]:
            try:
                await websocket.send_text(theme)
                print("!!!!!  Sent event update to websocket, new theme: " + theme)
            except:
                print("!!!!!  Failed to send event update to websocket, it was probably closed")

@app.delete('/events/{event_id}', tags=["Event"])
async def delete_event(event_id: str,db: Session = Depends(get_db)):
    """
    Delete the Event with the given ID
    """
    db_event = await EventRepo.fetch_by_uuid(db,event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found with the given ID")
    await EventRepo.delete(db,event_id)
    return "Event deleted successfully!"

@app.post('/events/{event_id}/theme/{theme}', tags=["Event"],response_model=schemas.Event)
async def update_event_theme(event_id: str, theme: str, db: Session = Depends(get_db)):
    """
    Update the theme of the Event with the given ID
    """
    db_event = await EventRepo.fetch_by_uuid(db,event_id)
    if db_event:
        db_event.theme = theme
        await EventRepo.update(db=db,event_data=db_event)
        await send_event_theme_update_to_websocket(event_id, theme=theme)
        return db_event
    else:
        raise HTTPException(status_code=400, detail="Event not found with the given ID")

@app.get('/events/{event_id}/theme', tags=["Event"],response_model=str)
async def get_event_theme(event_id: str, db: Session = Depends(get_db)):
    """
    Get the theme of the Event with the given ID
    """
    db_event = await EventRepo.fetch_by_uuid(db,event_id)
    if db_event:
        return db_event.theme
    else:
        raise HTTPException(status_code=400, detail="Event not found with the given ID")

@app.put('/events/{event_id}', tags=["Event"],response_model=schemas.Event)
async def update_event(event_id: str, event_request: schemas.Event, db: Session = Depends(get_db)):
    """
    Update an Event stored in the database
    """
    db_event = await EventRepo.fetch_by_uuid(db, event_id=event_id)
    if db_event:
        update_item_encoded = jsonable_encoder(event_request)
        db_event.name = update_item_encoded['name']
        db_event.latitude = update_item_encoded['latitude']
        db_event.longitude = update_item_encoded['longitude']
        db_event.date = update_item_encoded['date']
        db_event.state = update_item_encoded['state']
        db_event.theme = update_item_encoded['theme']
        return await EventRepo.update(db=db,event_data=db_event)
    else:
        raise HTTPException(status_code=400, detail="Event not found with the given ID")

@app.get('/events', tags=["Event"],response_model=List[schemas.Event])
async def get_events(skip: int = 0, limit: int = 100,db: Session = Depends(get_db)):
    """
    Get all Events
    """
    return await EventRepo.fetch_all(db=db, skip=skip, limit=limit)

# MARK: Song

@app.post('/songs', tags=["Song"],response_model=schemas.Song,status_code=201)
async def create_song(song_request: schemas.SongCreate, db: Session = Depends(get_db)):
    """
    Create a Song and store it in the database
    """
    return await SongRepo.create(db=db, song=song_request)