from typing import List, Optional
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
    balance: float
    is_verified: bool
    is_social: bool

    class Config:
        from_attributes = True

class LikedDJ(User):
    like_count: int

    class Config:
        from_attributes = True

class LoginData(BaseModel):
    email: str
    password: str
    auth_token: str

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
    latitude: float
    longitude: float
    address_title: str
    address_subtitle: str
    date: str
    state: str
    theme: str
    playlist_id: Optional[int] = None
    songs: List[Song] = []

class EventCreate(EventBase):
    pass

class Event(EventBase):
    uuid: str
    dj: User
    code: str

    class Config:
        from_attributes = True


class PaymentIntent(BaseModel):
    paymentIntent: str
    ephemeralKey: str
    customer: str
    publishableKey: str

class Transaction(BaseModel):
    user_id: str
    song_id: int
    amount: float

    class Config:
        from_attributes = True

class TransactionCreate(Transaction):
    pass

class PlaylistBase(BaseModel):
    name: str
    user_id: str

class PlaylistCreate(PlaylistBase):
    pass

class Playlist(PlaylistBase):
    id: int
    songs: List[Song] = []

    class Config:
        from_attributes = True

class VerificationToken(BaseModel):
    token: str
    user_id: str

    class Config:
        from_attributes = True

class AuthenticationToken(BaseModel):
    token: str
    user_id: str
    expires: str

    class Config:
        from_attributes = True