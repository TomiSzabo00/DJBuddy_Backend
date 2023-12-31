from sqlalchemy.orm import Session
from sql_app import models
from sql_app import schemas
import uuid
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepo:
    async def create(db: Session, user: schemas.UserCreate):
        uuid_str = str(uuid.uuid4())
        hashed_password = await UserRepo.get_password_hash(user.password_string)
        db_user = models.User(uuid=uuid_str,username=user.username,hashed_password=hashed_password,firstName=user.firstName,lastName=user.lastName,email=user.email,type=user.type,profilePicUrl=user.profilePicUrl)
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

    async def fetch_by_email(db: Session,email):
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
    
class EventRepo:  
    async def create(db: Session, event: schemas.EventCreate):
        uuid_str = str(uuid.uuid4())
        db_event = models.Event(uuid=uuid_str,name=event.name,dj_id=event.dj_id,latitude=event.latitude,longitude=event.longitude,address_title=event.address_title,address_subtitle=event.address_subtitle,date=event.date,state=event.state,theme=event.theme)
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