from typing import List, Optional
from pydantic import BaseModel
import uuid

class UserBase(BaseModel):
    username: str
    email: str
    name: str
    type: str
    profilePicUrl: str


class UserCreate(UserBase):
    pass


class User(UserBase):
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