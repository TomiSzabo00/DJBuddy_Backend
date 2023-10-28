from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
    
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True,index=True)
    username = Column(String(80), nullable=False)
    name = Column(String(80), nullable=False)
    email = Column(String(80), nullable=False, unique=True)
    type = Column(String(10), nullable=False)
    profilePicUrl = Column(String(200), nullable=False)

    def __repr__(self):
        return 'UserModel(name=%s, email=%s, type=%s)' % (self.name, self.email, self.type)
    
# class Store(Base):
#     __tablename__ = "stores"
#     id = Column(Integer, primary_key=True,index=True)
#     name = Column(String(80), nullable=False, unique=True)
#     items = relationship("Item",primaryjoin="Store.id == Item.store_id",cascade="all, delete-orphan")

#     def __repr__(self):
#         return 'Store(name=%s)' % self.name