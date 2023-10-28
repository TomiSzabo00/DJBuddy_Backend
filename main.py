from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sql_app import models
from database import get_db, engine
import sql_app.models as models
import sql_app.schemas as schemas
from sql_app.repositories import UserRepo
from sqlalchemy.orm import Session
import uvicorn
from typing import List,Optional
from fastapi.encoders import jsonable_encoder

app = FastAPI(title="Sample FastAPI Application",
    description="Sample FastAPI Application with Swagger and Sqlalchemy",
    version="1.0.0",)

models.Base.metadata.create_all(bind=engine)

@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})

@app.post('/users', tags=["User"],response_model=schemas.User,status_code=201)
async def create_user(user_request: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a User and store it in the database
    """
    
    db_user = UserRepo.fetch_by_email(db, email=user_request.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists!")

    return await UserRepo.create(db=db, user=user_request)

@app.get('/users', tags=["User"],response_model=List[schemas.User])
def get_all_users(email: Optional[str] = None,db: Session = Depends(get_db)):
    """
    Get all the Users stored in database
    """
    if email:
        users = []
        db_user = UserRepo.fetch_by_email(db,email)
        users.append(db_user)
        return users
    else:
        return UserRepo.fetch_all(db)


@app.get('/users/{user_id}', tags=["User"],response_model=schemas.User)
def get_user(user_id: int,db: Session = Depends(get_db)):
    """
    Get the User with the given ID
    """
    db_user = UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    return db_user

@app.delete('/users/{user_id}', tags=["User"])
async def delete_user(user_id: int,db: Session = Depends(get_db)):
    """
    Delete the User with the given ID
    """
    db_user = UserRepo.fetch_by_id(db,user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found with the given ID")
    await UserRepo.delete(db,user_id)
    return "User deleted successfully!"

@app.put('/users/{user_id}', tags=["User"],response_model=schemas.User)
async def update_user(user_id: int, user_request: schemas.User, db: Session = Depends(get_db)):
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
    
    
# @app.post('/stores', tags=["Store"],response_model=schemas.Store,status_code=201)
# async def create_store(store_request: schemas.StoreCreate, db: Session = Depends(get_db)):
#     """
#     Create a Store and save it in the database
#     """
#     db_store = StoreRepo.fetch_by_name(db, name=store_request.name)
#     print(db_store)
#     if db_store:
#         raise HTTPException(status_code=400, detail="Store already exists!")

#     return await StoreRepo.create(db=db, store=store_request)

# @app.get('/stores', tags=["Store"],response_model=List[schemas.Store])
# def get_all_stores(name: Optional[str] = None,db: Session = Depends(get_db)):
#     """
#     Get all the Stores stored in database
#     """
#     if name:
#         stores =[]
#         db_store = StoreRepo.fetch_by_name(db,name)
#         print(db_store)
#         stores.append(db_store)
#         return stores
#     else:
#         return StoreRepo.fetch_all(db)
    
# @app.get('/stores/{store_id}', tags=["Store"],response_model=schemas.Store)
# def get_store(store_id: int,db: Session = Depends(get_db)):
#     """
#     Get the Store with the given ID provided by User stored in database
#     """
#     db_store = StoreRepo.fetch_by_id(db,store_id)
#     if db_store is None:
#         raise HTTPException(status_code=404, detail="Store not found with the given ID")
#     return db_store

# @app.delete('/stores/{store_id}', tags=["Store"])
# async def delete_store(store_id: int,db: Session = Depends(get_db)):
#     """
#     Delete the Item with the given ID provided by User stored in database
#     """
#     db_store = StoreRepo.fetch_by_id(db,store_id)
#     if db_store is None:
#         raise HTTPException(status_code=404, detail="Store not found with the given ID")
#     await StoreRepo.delete(db,store_id)
#     return "Store deleted successfully!"
    

if __name__ == "__main__":
    uvicorn.run("main:app", port=9000, reload=True)