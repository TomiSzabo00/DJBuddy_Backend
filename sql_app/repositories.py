from sqlalchemy.orm import Session
from sql_app import models
from sql_app import schemas

class UserRepo:
 async def create(db: Session, user: schemas.UserCreate):
        db_user = models.User(username=user.username,name=user.name,email=user.email,type=user.type,profilePicUrl=user.profilePicUrl)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
 def fetch_by_id(db: Session, user_id):
     return db.query(models.User).filter(models.User.id == user_id).first()
 
 def fetch_by_email(db: Session,email):
     return db.query(models.User).filter(models.User.email == email).first()
 
 def fetch_all(db: Session, skip: int = 0, limit: int = 100):
     return db.query(models.User).offset(skip).limit(limit).all()
 
 async def delete(db: Session,user_id):
     db_user = db.query(models.User).filter_by(id=user_id).first()
     db.delete(db_user)
     db.commit()
      
 async def update(db: Session,user_data):
    updated_user = db.merge(user_data)
    db.commit()
    return updated_user
    

class StoreRepo:
    
    async def create(db: Session, store: schemas.StoreCreate):
            db_store = models.Store(name=store.name)
            db.add(db_store)
            db.commit()
            db.refresh(db_store)
            return db_store
        
    def fetch_by_id(db: Session,_id:int):
        return db.query(models.Store).filter(models.Store.id == _id).first()
    
    def fetch_by_name(db: Session,name:str):
        return db.query(models.Store).filter(models.Store.name == name).first()
    
    def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Store).offset(skip).limit(limit).all()
    
    async def delete(db: Session,_id:int):
        db_store= db.query(models.Store).filter_by(id=_id).first()
        db.delete(db_store)
        db.commit()
        
    async def update(db: Session,store_data):
        db.merge(store_data)
        db.commit()