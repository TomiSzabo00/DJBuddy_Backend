from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base
import uuid
    
class User(Base):
    __tablename__ = "users"
    
    uuid = Column(String, index=True, primary_key=True, default=str(uuid.uuid4()))
    username = Column(String(80), nullable=False)
    hashed_password = Column(String, nullable=False)
    firstName = Column(String(20), nullable=False)
    lastName = Column(String(20), nullable=False)
    email = Column(String(80), nullable=False, unique=True)
    type = Column(String(10), nullable=False)
    profilePicUrl = Column(String, nullable=False)
    balance = Column(Float, nullable=False, default=0)
    liked_by_count = Column(Integer, nullable=False, default=0)
    is_verified = Column(Integer, nullable=False, default=False)
    events = relationship("Event",secondary="association_table_user_events", back_populates="users")
    liked_by = relationship("User",secondary="association_table_user_likes", back_populates="liked", primaryjoin="User.uuid == association_table_user_likes.c.user_id", secondaryjoin="User.uuid == association_table_user_likes.c.dj_id")
    liked = relationship("User",secondary="association_table_user_likes", back_populates="liked_by", primaryjoin="User.uuid == association_table_user_likes.c.dj_id", secondaryjoin="User.uuid == association_table_user_likes.c.user_id")
    saved_songs = relationship("Song",secondary="association_table_user_saved_songs", back_populates="liked_by")
    playlists = relationship("Playlist",primaryjoin="User.uuid == Playlist.user_id",cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    
    uuid = Column(String, index=True, primary_key=True, default=str(uuid.uuid4()))
    name = Column(String(80), nullable=False)
    dj_id = Column(String, ForeignKey("users.uuid"), nullable=False)
    dj = relationship("User",primaryjoin="Event.dj_id == User.uuid")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address_title = Column(String, nullable=False)
    address_subtitle = Column(String, nullable=False)
    date = Column(String, nullable=False)
    state = Column(String, nullable=False)
    theme = Column(String, nullable=False)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=True, default=None)
    code = Column(String, nullable=False)
    songs = relationship("Song",primaryjoin="Event.uuid == Song.event_id",cascade="all, delete-orphan")
    users = relationship("User",secondary="association_table_user_events", back_populates="events")

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True,index=True)
    title = Column(String(80), nullable=False)
    artist = Column(String(80), nullable=False)
    amount = Column(Float, nullable=False)
    albumArtUrl = Column(String, nullable=False)
    event_id = Column(String, ForeignKey("events.uuid"), nullable=False)
    liked_by = relationship("User",secondary="association_table_user_saved_songs", back_populates="saved_songs")
    playlist = relationship("Playlist",secondary="association_table_playlist_songs", back_populates="songs")

association_table = Table(
    "association_table_user_events",
    Base.metadata,
    Column("user_id", ForeignKey("users.uuid"), primary_key=True),
    Column("event_id", ForeignKey("events.uuid"), primary_key=True),
)

association_table_user_likes = Table(
    "association_table_user_likes",
    Base.metadata,
    Column("user_id", ForeignKey("users.uuid"), primary_key=True),
    Column("dj_id", ForeignKey("users.uuid"), primary_key=True),
)

association_table_user_saved_songs = Table(
    "association_table_user_saved_songs",
    Base.metadata,
    Column("user_id", ForeignKey("users.uuid"), primary_key=True),
    Column("song_id", ForeignKey("songs.id"), primary_key=True),
)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True,index=True)
    user_id = Column(String, ForeignKey("users.uuid"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    amount = Column(Float, nullable=False)

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True,index=True)
    name = Column(String(80), nullable=False)
    user_id = Column(String, ForeignKey("users.uuid"), nullable=False)
    songs = relationship("Song",secondary="association_table_playlist_songs", back_populates="playlist")

association_table_playlist_songs = Table(
    "association_table_playlist_songs",
    Base.metadata,
    Column("playlist_id", ForeignKey("playlists.id"), primary_key=True),
    Column("song_id", ForeignKey("songs.id"), primary_key=True),
)