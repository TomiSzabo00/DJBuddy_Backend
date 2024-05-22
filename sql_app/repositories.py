import datetime
import random
import string
from sqlalchemy.orm import Session
from sql_app import models
from sql_app import schemas
import uuid
from passlib.context import CryptContext
from pytz import utc
from social_auth_models.social_auth import SocialUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepo:
    async def create(db: Session, user: schemas.UserCreate):
        uuid_str = str(uuid.uuid4())
        hashed_password = await UserRepo.get_password_hash(user.password_string)
        db_user = models.User(uuid=uuid_str,username=user.username,hashed_password=hashed_password,firstName=user.firstName,lastName=user.lastName,email=user.email,type=user.type,profilePicUrl=user.profilePicUrl)
        db.add(db_user)
        await VerificationTokenRepo.create(db,uuid_str)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    async def create_social_user(db: Session, user: SocialUser):
        uuid_str = str(uuid.uuid4())
        first_name = user.name.split(' ')[0]
        last_name = user.name.split(' ')[1]
        db_user = models.User(uuid=uuid_str,username="",hashed_password="",firstName=first_name,lastName=last_name,email=user.email,type='user',profilePicUrl=user.picture_url,is_social=True, is_verified=True)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    async def authenticate_user(db: Session, email: str, password: str) -> schemas.User:
        user = await UserRepo.fetch_by_email(db,email)
        if not user:
            return False
        if not await UserRepo.verify_password(password, user.hashed_password):
            return False
        return user

    async def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    async def get_password_hash(password):
        return pwd_context.hash(password)

    async def fetch_by_id(db: Session, user_id):
        return db.query(models.User).filter(models.User.uuid == user_id).first()

    async def fetch_by_id_as_liked_dj(db: Session, user_id):
        query_result = db.query(models.User).filter(models.User.uuid == user_id).first()
        like_count = query_result.liked_by_count
        return schemas.LikedDJ(uuid=query_result.uuid,
                               username=query_result.username,
                               firstName=query_result.firstName,
                               lastName=query_result.lastName,
                               email=query_result.email,
                               type=query_result.type,
                               profilePicUrl=query_result.profilePicUrl,
                               balance=query_result.balance,
                               like_count=like_count,
                               is_verified=query_result.is_verified,
                               is_social=query_result.is_social)

    async def fetch_by_email(db: Session,email):
        query = db.query(models.User).filter(models.User.email == email).first()
        if query is None:
            return None
        return schemas.User.model_validate(query)

    async def fetch_by_email_as_db_model(db: Session,email):
        return db.query(models.User).filter(models.User.email == email).first()

    async def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.User).offset(skip).limit(limit).all()

    async def delete(db: Session,user_id):
        db_user = db.query(models.User).filter_by(id=user_id).first()
        db.delete(db_user)
        db.commit()
        
    async def update(db: Session,user_data):
        updated_user = db.merge(user_data)
        db.commit()
        return updated_user
    
    async def verify_user(db: Session,user_id,verification_token):
        db_verification_token = await VerificationTokenRepo.fetch_by_user_id(db,user_id)
        if db_verification_token is None:
            return False
        if db_verification_token.token == verification_token:
            db_user = db.query(models.User).filter_by(uuid=user_id).first()
            db_user.is_verified = True
            await VerificationTokenRepo.delete(db,user_id)
            db.commit()
            return True
        return False
    
    async def fetch_by_auth_token(db: Session,auth_token):
        user_id = await AuthenticationTokenRepo.fetch_uid_by_token(db,auth_token.token)
        if user_id is None:
            return None
        return await UserRepo.fetch_by_id(db,user_id)
    
class EventRepo:  
    async def create(db: Session, event: schemas.EventCreate):
        uuid_str = str(uuid.uuid4())
        event_code = '{}-{}-{}'.format(
            uuid.uuid4().hex[:4],
            uuid.uuid4().hex[:4],
            uuid.uuid4().hex[:4]
        )
        db_event = models.Event(uuid=uuid_str,name=event.name,dj_id=event.dj_id,latitude=event.latitude,longitude=event.longitude,address_title=event.address_title,address_subtitle=event.address_subtitle,date=event.date,state=event.state,theme=event.theme, code=event_code)
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    
    async def fetch_by_uuid(db: Session,uuid:str):
        query_result = db.query(models.Event).filter(models.Event.uuid == uuid).first()
        if query_result is None:
            return None
        return schemas.Event.model_validate(query_result)
    
    async def fetch_by_uuid_as_db_model(db: Session,uuid:str):
        return db.query(models.Event).filter(models.Event.uuid == uuid).first()
    
    async def fetch_by_dj_id(db: Session,dj_id:str):
        query_results = db.query(models.Event).filter(models.Event.dj_id == dj_id).all()
        list = []
        for result in query_results:
            list.append(schemas.Event.from_orm(result))
        return list
    
    async def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        query_results = db.query(models.Event).offset(skip).limit(limit).all()
        list = []
        for result in query_results:
            list.append(schemas.Event.from_orm(result))
        return list
        
    async def update(db: Session,event_data):
        db.merge(event_data)
        db.commit()

class SongRepo:
    async def create(db: Session, song: schemas.SongCreate):
        db_song = models.Song(title=song.title,artist=song.artist,amount=song.amount,albumArtUrl=song.albumArtUrl,event_id=song.event_id)
        db.add(db_song)
        db.commit()
        db.refresh(db_song)
        return schemas.Song.from_orm(db_song)
    
    async def fetch_by_id(db: Session,_id:int):
        query_result = db.query(models.Song).filter(models.Song.id == _id).first()
        return schemas.Song.from_orm(query_result)
    
    async def fetch_by_id_as_db_model(db: Session,_id:int):
        return db.query(models.Song).filter(models.Song.id == _id).first()
    
    async def fetch_by_event_id(db: Session,event_id:str):
        query_results = db.query(models.Song).filter(models.Song.event_id == event_id).all()
        list = []
        for result in query_results:
            list.append(schemas.Song.from_orm(result))
        return list
    
    async def delete(db: Session,_id:int):
        db_song = db.query(models.Song).filter_by(id=_id).first()
        db.delete(db_song)
        db.commit()
        
    async def update(db: Session,song_data):
        db.merge(song_data)
        db.commit()

class TransactionRepo:
    async def create(db: Session, transaction: schemas.TransactionCreate):
        db_transaction = models.Transaction(user_id=transaction.user_id,song_id=transaction.song_id,amount=transaction.amount)
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return schemas.Transaction.from_orm(db_transaction)
    
    async def fetch_by_id(db: Session,_id:int):
        return db.query(models.Transaction).filter(models.Transaction.id == _id).first()
    
    async def fetch_by_song_id(db: Session,song_id:int):
        query_results = db.query(models.Transaction).filter(models.Transaction.song_id == song_id).all()
        list = []
        for result in query_results:
            list.append(schemas.Transaction.from_orm(result))
        return list
    
    async def delete(db: Session,_id:int):
        db_transaction = db.query(models.Transaction).filter_by(id=_id).first()
        db.delete(db_transaction)
        db.commit()

    async def delete_by_song_id(db: Session,song_id:int):
        db_transactions = db.query(models.Transaction).filter_by(song_id=song_id).all()
        for db_transaction in db_transactions:
            db.delete(db_transaction)
        db.commit()
        
    async def update(db: Session,transaction_data):
        db.merge(transaction_data)
        db.commit()

class PlaylistRepo:
    async def create(db: Session, playlist: schemas.PlaylistCreate):
        db_playlist = models.Playlist(name=playlist.name,user_id=playlist.user_id)
        db.add(db_playlist)
        db.commit()
        db.refresh(db_playlist)
        return db_playlist
    
    async def fetch_by_id(db: Session,_id:int):
        return db.query(models.Playlist).filter(models.Playlist.id == _id).first()
    
    async def delete(db: Session,_id:int):
        db_playlist = db.query(models.Playlist).filter_by(id=_id).first()
        db.delete(db_playlist)
        db.commit()
        
    async def update(db: Session,playlist_data):
        db.merge(playlist_data)
        db.commit()
    
    async def add_song_to_playlist(db: Session,playlist_id:int,song_id:int):
        db_playlist = db.query(models.Playlist).filter_by(id=playlist_id).first()
        db_song = db.query(models.Song).filter_by(id=song_id).first()
        db_playlist.songs.append(db_song)
        db.commit()
        db.refresh(db_playlist)
    
    async def remove_song_from_playlist(db: Session,playlist_id:int,song_id:int):
        db_playlist = db.query(models.Playlist).filter_by(id=playlist_id).first()
        db_song = db.query(models.Song).filter_by(id=song_id).first()
        db_playlist.songs.remove(db_song)
        db.commit()
        db.refresh(db_playlist)
    
    async def fetch_songs_by_playlist_id(db: Session,playlist_id:int):
        db_playlist = db.query(models.Playlist).filter_by(id=playlist_id).first()
        return db_playlist.songs
    
    async def fetch_by_user_id(db: Session,user_id:str):
        query_results = db.query(models.Playlist).filter(models.Playlist.user_id == user_id).all()
        return query_results

class VerificationTokenRepo:
    def generate_verification_code(length=6):
        characters = string.ascii_letters + string.digits
        verification_code = ''.join(random.choice(characters) for _ in range(length))
        return verification_code

    async def create(db: Session, user_id:str):
        verification_token = VerificationTokenRepo.generate_verification_code()
        db_verification_token = models.VerificationToken(user_id=user_id,token=verification_token)
        db.add(db_verification_token)
        db.commit()
        db.refresh(db_verification_token)
        return verification_token
    
    async def fetch_by_user_id(db: Session,user_id:str):
        return db.query(models.VerificationToken).filter(models.VerificationToken.user_id == user_id).first()
    
    async def delete(db: Session,user_id:str):
        db_verification_token = db.query(models.VerificationToken).filter_by(user_id=user_id).first()
        db.delete(db_verification_token)
        db.commit()
        
    async def delete_by_token(db: Session,token:str):
        db_verification_token = db.query(models.VerificationToken).filter_by(token=token).first()
        db.delete(db_verification_token)
        db.commit()
        
    async def update(db: Session,verification_token_data):
        db.merge(verification_token_data)
        db.commit()

class AuthenticationTokenRepo:
    async def create(db: Session, user_id:str, token:str | None = None):
        existing_token = await AuthenticationTokenRepo.fetch_by_user_id(db,user_id)
        if existing_token is not None:
            await AuthenticationTokenRepo.delete(db,user_id)

        if token is None:
            token = uuid.uuid4().hex
        expires = datetime.datetime.now().astimezone(utc) + datetime.timedelta(hours=12)
        expires_str = expires.isoformat()
        db_authentication_token = models.AuthenticationToken(user_id=user_id,token=token,expires=expires_str)
        db.add(db_authentication_token)
        db.commit()
        db.refresh(db_authentication_token)
        return db_authentication_token
    
    async def fetch_by_user_id(db: Session,user_id:str):
        return db.query(models.AuthenticationToken).filter(models.AuthenticationToken.user_id == user_id).first()
    
    async def fetch_uid_by_token(db: Session,token:str):
        query_result = db.query(models.AuthenticationToken).filter(models.AuthenticationToken.token == token).first()
        if query_result is None:
            return None
        return query_result.user_id
    
    async def delete(db: Session,user_id:str):
        db_authentication_token = db.query(models.AuthenticationToken).filter_by(user_id=user_id).first()
        db.delete(db_authentication_token)
        db.commit()
    
    async def refresh(db: Session,user_id:str):
        db_authentication_token = await AuthenticationTokenRepo.fetch_by_user_id(db,user_id)
        if db_authentication_token is None:
            return await AuthenticationTokenRepo.create(db,user_id)
        db_authentication_token.expires = datetime.datetime.now() + datetime.timedelta(hours=12)
        db.refresh(db_authentication_token)
        db.commit()
        return db_authentication_token
    
    async def authenticate(db: Session,auth_token:str):
        query_result = db.query(models.AuthenticationToken).filter(models.AuthenticationToken.token == auth_token).first()
        if query_result is None:
            return False
        
        token_model = schemas.AuthenticationToken.model_validate(query_result)
        expiry = datetime.datetime.fromisoformat(token_model.expires)
        now = datetime.datetime.now().astimezone(utc)
        if expiry < now:
            print('Now:',now)
            print('Expiry:',expiry)
            await AuthenticationTokenRepo.delete(db,token_model.user_id)
            return False
        return True
    
    async def validate_and_get_user_id(db: Session,auth_token:str):
        if not await AuthenticationTokenRepo.authenticate(db,auth_token):
            return None
        return await AuthenticationTokenRepo.fetch_uid_by_token(db,auth_token)
