from typing import List, Optional
from pydantic import BaseModel
import uuid

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

# class StoreBase(BaseModel):
#     name: str

# class StoreCreate(StoreBase):
#     pass

# class Store(StoreBase):
#     id: int
#     items: List[User] = []

#     class Config:
#         from_attributes = True