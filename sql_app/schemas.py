from typing import List
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    hashed_password: str = ""
    firstName: str
    lastName: str
    type: str
    profilePicUrl: str


class UserCreate(UserBase):
    password_string: str


class User(UserBase):
    uuid: str

    class Config:
        from_attributes = True

class LoginData(BaseModel):
    email: str
    password: str

class SongBase(BaseModel):
    title: str
    artist: str
    amount: float
    albumArtUrl: str
    event_id: str

class SongCreate(SongBase):
    pass

class Song(SongBase):
    id: int

    class Config:
        from_attributes = True

class EventBase(BaseModel):
    name: str
    dj_id: str
    dj: User
    latitude: float
    longitude: float
    date: str
    state: str
    theme: str
    songs: List[Song] = []

class EventCreate(EventBase):
    pass

class Event(EventBase):
    uuid: str

    class Config:
        from_attributes = True

# class StoreBase(BaseModel):
#     name: str

# class StoreCreate(StoreBase):
#     pass

# class Store(StoreBase):
#     id: int
#     items: List[User] = []

#     class Config:
#         from_attributes = True