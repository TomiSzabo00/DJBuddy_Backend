from fastapi import Depends, FastAPI, HTTPException, status, WebSocket, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from sql_app import models
from database import get_db, engine
import sql_app.models as models
import sql_app.schemas as schemas
from sql_app.repositories import UserRepo, EventRepo, SongRepo, TransactionRepo, PlaylistRepo
from sqlalchemy.orm import Session
import uvicorn
from typing import List
import math
import stripe

stripe.api_key = 'sk_test_51O84UAKBcww6so5SD73G0w50hwkZaxaA90i86otBIkmMhApg4RgLrknonQJyjsjk2mFS8NW10xLcd2GxnLfzMxhz00eewtKn2R'
SECRET_KEY = "5736f10d085954fd50e4706e4eabd16a420100588937319231822869bbdfe363"
ALGORITHM = "HS256"
IMAGE_UPLOAD_PATH = "images/"

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





# MARK: User

@app.post("/users/login", tags=["User"], response_model=schemas.User,status_code=200)
async def login_user(login_data: schemas.LoginData, db: Session = Depends(get_db)):
    user = await UserRepo.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

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
    if db_user.type == "dj":
        events = await EventRepo.fetch_by_dj_id(db,user_id)
        return events
    return db_user.events

@app.put('/users/{user_id}/balance/{amount}', tags=["User"],response_model=float)
async def add_to_user_balance(user_id: str, amount: float, db: Session = Depends(get_db)):
    """
    Update the balance of the User with the given ID
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    db_user.balance += amount
    await UserRepo.update(db=db,user_data=db_user)
    return db_user.balance

@app.put('/users/{user_id}/balance/{amount}/remove', tags=["User"],response_model=float)
async def remove_from_user_balance(user_id: str, amount: float, db: Session = Depends(get_db)):
    """
    Update the balance of the User with the given ID
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user.balance < amount:
        raise HTTPException(status_code=400, detail="You do not have enough money to make this transaction")
    db_user.balance -= amount
    await UserRepo.update(db=db,user_data=db_user)
    return db_user.balance

@app.get('/users/{user_id}', tags=["User"],response_model=schemas.User)
async def get_user(user_id: str,db: Session = Depends(get_db)):
    """
    Get the User with the given ID
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    return db_user

@app.put('/users/{user_id}/withdraw/', tags=["User"],response_model=float)
async def withdraw_user_balance(user_id: str, amount: float | None = None, db: Session = Depends(get_db)):
    """
    Withdraw the balance of the User with the given ID
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if amount is None:
        amount = db_user.balance
    if db_user.balance < amount:
        raise HTTPException(status_code=400, detail="You do not have enough money to make this transaction")
    db_user.balance -= amount
    await UserRepo.update(db=db,user_data=db_user)

    # TODO: send money to user's bank account

    return db_user.balance

@app.put('/users/{user_id}/profile_pic/upload', tags=["User"],response_model=str)
async def upload_user_profile_pic(user_id: str, pic: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a profile picture for the User with the given ID
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    
    try:
        pic.filename = user_id + ".jpg"
        contents = await pic.read()
        with open(IMAGE_UPLOAD_PATH + pic.filename, "wb") as f:
            f.write(contents)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to upload image")
    finally:
        pic.file.close()

    db_user.profilePicUrl = "users/{user_id}/profile_pic".format(user_id=user_id)
    await UserRepo.update(db=db,user_data=db_user)
    return db_user.profilePicUrl

@app.get('/users/{user_id}/profile_pic', tags=["User"])
async def get_user_profile_pic(user_id: str, db: Session = Depends(get_db)):
    """
    Get the profile picture of the User with the given ID
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    path = IMAGE_UPLOAD_PATH + user_id + ".jpg"
    # check if file exists
    try:
        with open(path, "rb") as f:
            pass
    except Exception:
        return ""
    return FileResponse(path)

# like a dj
@app.put('/users/{user_id}/like/{dj_id}', tags=["User"])
async def like_dj(user_id: str, dj_id: str, db: Session = Depends(get_db)):
    """
    Like a DJ
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    db_dj = await UserRepo.fetch_by_id(db,dj_id)
    if db_user and db_dj:
        db_dj.liked_by.append(db_user)
        db_dj.liked_by_count += 1
        await UserRepo.update(db=db,user_data=db_user)
    else:
        raise HTTPException(status_code=400, detail="User or DJ not found with the given ID")

# unlike a dj
@app.put('/users/{user_id}/unlike/{dj_id}', tags=["User"])
async def unlike_dj(user_id: str, dj_id: str, db: Session = Depends(get_db)):
    """
    Unlike a DJ
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    db_dj = await UserRepo.fetch_by_id(db,dj_id)
    if db_user and db_dj:
        db_dj.liked_by.remove(db_user)
        db_dj.liked_by_count -= 1
        await UserRepo.update(db=db,user_data=db_user)
    else:
        raise HTTPException(status_code=400, detail="User or DJ not found with the given ID")

# is a dj liked by a user
@app.get('/users/{user_id}/likes/{dj_id}', tags=["User"],response_model=bool)
async def is_dj_liked_by_user(user_id: str, dj_id: str, db: Session = Depends(get_db)):
    """
    Check if a DJ is liked by a User
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    db_dj = await UserRepo.fetch_by_id(db,dj_id)
    if db_user and db_dj:
        return db_user in db_dj.liked_by
    else:
        raise HTTPException(status_code=400, detail="User or DJ not found with the given ID")

# get all djs liked by a user
@app.get('/users/{user_id}/likes', tags=["User"],response_model=List[schemas.LikedDJ])
async def get_djs_liked_by_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get all DJs liked by a User
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user:
        liked_djs = []
        for dj in db_user.liked:
            liked_dj = await UserRepo.fetch_by_id_as_liked_dj(db,dj.uuid)
            liked_djs.append(liked_dj)
        return liked_djs
    else:
        raise HTTPException(status_code=400, detail="User not found with the given ID")

# get all saved songs of a user
@app.get('/users/{user_id}/saved_songs', tags=["User"],response_model=List[schemas.Song])
async def get_saved_songs_of_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get all saved Songs of a User
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user:
        return db_user.saved_songs
    else:
        raise HTTPException(status_code=404, detail="User not found with the given ID")

# post request to create and save a song
@app.post('/users/{user_id}/save', tags=["User"],response_model=schemas.Song,status_code=201)
async def save_song(user_id: str, song_request: schemas.SongCreate, db: Session = Depends(get_db)):
    """
    Save a Song
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    schema_song = await SongRepo.create(db=db, song=song_request)
    db_song = await SongRepo.fetch_by_id_as_db_model(db=db, _id=schema_song.id)
    if not db_song:
        raise HTTPException(status_code=404, detail="Song couldn't be created or couldn't be found")
    db_user.saved_songs.append(db_song)
    await UserRepo.update(db=db,user_data=db_user)
    return schema_song


# unsave a song
@app.put('/users/{user_id}/unsave/{song_id}', tags=["User"])
async def unsave_song(user_id: str, song_id: int, db: Session = Depends(get_db)):
    """
    Unsave a Song
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    db_song = await SongRepo.fetch_by_id_as_db_model(db=db, _id=song_id)
    if db_user and db_song:
        db_user.saved_songs.remove(db_song)
        await UserRepo.update(db=db,user_data=db_user)
        await SongRepo.delete(db=db,_id=song_id)
    else:
        raise HTTPException(status_code=404, detail="User or Song not found with the given ID")



# MARK: Playlist

@app.post('/playlists/create', tags=["Playlist"],response_model=int,status_code=201)
async def create_playlist(playlist_request: schemas.PlaylistCreate, db: Session = Depends(get_db)):
    """
    Create a Playlist and store it in the database
    """
    playlist = await PlaylistRepo.create(db=db, playlist=playlist_request)
    return playlist.id

# @app.get('/playlists/{playlist_id}', tags=["Playlist"],response_model=schemas.Playlist)
# async def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
#     """
#     Get the Playlist with the given ID
#     """
#     db_playlist = await PlaylistRepo.fetch_by_id(db,playlist_id)
#     if db_playlist is None:
#         raise HTTPException(status_code=404, detail="Playlist not found with the given ID")
#     return db_playlist

@app.post('/playlists/{playlist_id}/remove', tags=["Playlist"],status_code=200)
async def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    """
    Delete a Playlist from the database
    """
    return await PlaylistRepo.delete(db,playlist_id)

# create and add a song to a playlist
@app.post('/playlists/{playlist_id}/add_song', tags=["Playlist"],status_code=201)
async def add_song_to_playlist(playlist_id: int, song_request: schemas.SongCreate, db: Session = Depends(get_db)):
    """
    Add a Song to a Playlist
    """
    db_playlist = await PlaylistRepo.fetch_by_id(db,playlist_id)
    if db_playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found with the given ID")
    schema_song = await SongRepo.create(db=db, song=song_request)
    db_song = await SongRepo.fetch_by_id_as_db_model(db=db, _id=schema_song.id)
    if db_song is None:
        raise HTTPException(status_code=404, detail="Song couldn't be created or couldn't be found")
    db_playlist.songs.append(db_song)
    await PlaylistRepo.update(db=db,playlist_data=db_playlist)
    return JSONResponse(status_code=201, content={"message": "Song added to playlist successfully"})

# remove a song from a playlist
@app.post('/playlists/{playlist_id}/remove_song/{song_id}', tags=["Playlist"],status_code=200)
async def remove_song_from_playlist(playlist_id: int, song_id: int, db: Session = Depends(get_db)):
    """
    Remove a Song from a Playlist
    """
    db_playlist = await PlaylistRepo.fetch_by_id(db,playlist_id)
    db_song = await SongRepo.fetch_by_id_as_db_model(db, song_id)
    if db_playlist and db_song:
        db_playlist.songs.remove(db_song)
        await PlaylistRepo.update(db=db,playlist_data=db_playlist)
        await SongRepo.delete(db=db,_id=song_id)
    else:
        raise HTTPException(status_code=404, detail="Playlist or Song not found with the given ID")

# get all songs in a playlist
@app.get('/playlists/{playlist_id}/songs', tags=["Playlist"],response_model=List[schemas.Song])
async def get_playlist_songs(playlist_id: int, db: Session = Depends(get_db)):
    """
    Get all Songs in a Playlist
    """
    db_playlist = await PlaylistRepo.fetch_by_id(db,playlist_id)
    if db_playlist:
        return db_playlist.songs
    else:
        raise HTTPException(status_code=404, detail="Playlist not found with the given ID")
    
# get all playlists of a user
@app.get('/playlists/{user_id}', tags=["Playlist"],response_model=List[schemas.Playlist])
async def get_user_playlists(user_id: str, db: Session = Depends(get_db)):
    """
    Get all Playlists of a User
    """
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user:
        return db_user.playlists
    else:
        raise HTTPException(status_code=404, detail="User not found with the given ID")



# MARK: Event

@app.post('/events/create', tags=["Event"],response_model=schemas.Event,status_code=201)
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
    # check if event_websockets has key for event_id
    if event_id not in event_websockets:
        event_websockets[event_id] = []
    event_websockets[event_id].append(websocket)
    while True:
        # don't receive just keep connection alive
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
                print("!!!!!  Sent event update to websocket")
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

@app.post('/events/{event_id}/theme/{theme}', tags=["Event"],response_model=schemas.Event)
async def update_event_theme(event_id: str, theme: str, db: Session = Depends(get_db)):
    """
    Update the theme of the Event with the given ID
    """
    db_event = await EventRepo.fetch_by_uuid_as_db_model(db,event_id)
    if db_event:
        db_event.theme = theme
        await EventRepo.update(db=db,event_data=db_event)
        await send_event_theme_update_to_websocket(event_id, theme=theme)
        return schemas.Event.from_orm(db_event)
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

@app.get('/events/all/', tags=["Event"],response_model=List[schemas.Event])
async def get_all_events(skip: int = 0, limit: int = 100,db: Session = Depends(get_db)):
    """
    Get all Events
    """
    return await EventRepo.fetch_all(db=db, skip=skip, limit=limit)

@app.get('/events/near_me/', tags=["Event"],response_model=List[schemas.Event])
async def get_near_me_events(latitude: float, longitude: float, distance: float = 20, db: Session = Depends(get_db)):
    """
    Get all Events near the given latitude and longitude
    """
    all_events = await EventRepo.fetch_all(db=db)
    events_near_me = []
    for event in all_events:
        if haversine_distance(latitude, longitude, event.latitude, event.longitude) <= distance:
            events_near_me.append(event)
    return events_near_me

@app.get('/events/{event_id}/songs', tags=["Event"],response_model=List[schemas.Song])
async def get_event_songs(event_id: str,db: Session = Depends(get_db)):
    """
    Get the Songs associated with the given Event ID
    """
    db_event = await EventRepo.fetch_by_uuid(db,event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found with the given ID")
    return db_event.songs

@app.post('/events/{event_id}/state/{state}', tags=["Event"],response_model=schemas.Event)
async def update_event_state(event_id: str, state: str, db: Session = Depends(get_db)):
    """
    Update the state of the Event with the given ID
    """
    db_event = await EventRepo.fetch_by_uuid_as_db_model(db,event_id)
    if db_event:
        db_event.state = state
        await EventRepo.update(db=db,event_data=db_event)
        await send_event_update_to_websocket(event_id, event=db_event)
        return schemas.Event.from_orm(db_event)
    else:
        raise HTTPException(status_code=400, detail="Event not found with the given ID")

@app.put('/events/{event_id}/join/{user_id}', tags=["Event"],response_model=schemas.Event)
async def join_event(event_id: str, user_id: str, db: Session = Depends(get_db)):
    """
    Add a User to an Event
    """
    db_event = await EventRepo.fetch_by_uuid_as_db_model(db,event_id)
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user.type == "dj":
        raise HTTPException(status_code=400, detail="DJ cannot join an event")
    if db_event and db_user:
        db_event.users.append(db_user)
        await EventRepo.update(db=db,event_data=db_event)
        return schemas.Event.from_orm(db_event)
    else:
        raise HTTPException(status_code=400, detail="User or Event not found with the given ID")

@app.put('/events/{event_id}/leave/{user_id}', tags=["Event"],response_model=schemas.Event)
async def leave_event(event_id: str, user_id: str, db: Session = Depends(get_db)):
    """
    Remove a User from an Event
    """
    db_event = await EventRepo.fetch_by_uuid_as_db_model(db,event_id)
    db_user = await UserRepo.fetch_by_id(db,user_id)
    if db_user.type == "dj":
        raise HTTPException(status_code=400, detail="DJ cannot leave an event")
    if db_event and db_user:
        db_event.users.remove(db_user)
        await EventRepo.update(db=db,event_data=db_event)
        return schemas.Event.from_orm(db_event)
    else:
        raise HTTPException(status_code=400, detail="User or Event not found with the given ID")

@app.get('/events/{event_id}/users/count', tags=["Event"],response_model=int)
async def count_event_users(event_id: str, db: Session = Depends(get_db)):
    """
    Count the number of Users in an Event
    """
    db_event = await EventRepo.fetch_by_uuid_as_db_model(db,event_id)
    if db_event:
        return len(db_event.users)
    else:
        raise HTTPException(status_code=400, detail="Event not found with the given ID")





# MARK: Song

@app.post('/songs/request/by/{user_id}', tags=["Song"],response_model=schemas.Song,status_code=201)
async def request_song(user_id: str, song_request: schemas.SongCreate, db: Session = Depends(get_db)):
    """
    Request a Song
    """
    # check if the event exists
    db_event = await EventRepo.fetch_by_uuid(db,song_request.event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found with the given ID")
    # check if the song already exists
    all_songs = await SongRepo.fetch_by_event_id(db,song_request.event_id)
    for song in all_songs:
        if song.title == song_request.title and song.artist == song_request.artist:
            raise HTTPException(status_code=400, detail="Song already exists in the event")
    
    song = await SongRepo.create(db=db, song=song_request)
    event_of_song = await EventRepo.fetch_by_uuid(db=db, uuid=song_request.event_id)
    await send_event_update_to_websocket(event_of_song.uuid, event_of_song)

    # create a transaction
    transaction = schemas.TransactionCreate(user_id=user_id,song_id=song.id,amount=song.amount)
    await TransactionRepo.create(db=db, transaction=transaction)

    await remove_from_user_balance(user_id=user_id, amount=song.amount, db=db)

    return song

@app.post('/songs/{song_id}/remove', tags=["Song"])
async def delete_song(song_id: int, db: Session = Depends(get_db)):
    """
    Delete a Song from the database
    """
    song = await SongRepo.fetch_by_id(db=db, _id=song_id)
    await SongRepo.delete(db=db, _id=song_id)
    event_of_song = await EventRepo.fetch_by_uuid(db=db, uuid=song.event_id)
    await send_event_update_to_websocket(event_of_song.uuid, event_of_song)

    # refund balance based on transaction
    transaction = await TransactionRepo.fetch_by_song_id(db=db, song_id=song_id)
    for t in transaction:
        await add_to_user_balance(user_id=t.user_id, amount=t.amount, db=db)
    await TransactionRepo.delete_by_song_id(db=db, song_id=song_id)

    return JSONResponse(status_code=200, content={"message": "Song deleted successfully"})

@app.put('/songs/{song_id}/amount/increase_by/{amount}', tags=["Song"],response_model=float)
async def increase_song_amount(song_id: int, amount: float, db: Session = Depends(get_db)):
    """
    Update the amount of a Song
    """
    song = await SongRepo.fetch_by_id_as_db_model(db=db, _id=song_id)
    song.amount += amount
    await SongRepo.update(db=db,song_data=song)
    event_of_song = await EventRepo.fetch_by_uuid(db=db, uuid=song.event_id)
    await send_event_update_to_websocket(event_of_song.uuid, event_of_song)
    return song.amount




# MARK: Helpers

def haversine_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    earth_radius = 6371

    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance
    distance = earth_radius * c

    return distance





# MARK: Payment
@app.get('/payment/create/', tags=["Payment"],response_model=schemas.PaymentIntent)
async def create_payment(amount: float, db: Session = Depends(get_db)):
    """
    Create a Payment and return the Payment Intent Client Secret
    """
    customer = stripe.Customer.create()
    ephemeralKey = stripe.EphemeralKey.create(
    customer=customer['id'],
    stripe_version='2023-10-16',
    )
    intent = stripe.PaymentIntent.create(
        amount=int(amount*100),
        currency='usd',
        automatic_payment_methods={
            'enabled': True,
        },
    )

    return schemas.PaymentIntent(paymentIntent=intent.client_secret, ephemeralKey=ephemeralKey.secret, customer=customer['id'],publishableKey="pk_test_51O84UAKBcww6so5Sqnlsm12nzm2PK46wTJiMzTDOPOuLifRqk4HNqKrfM4yNsyL7sS4G6n4nSXbjEFaeIkelF1Bj00gOxZnYET")
