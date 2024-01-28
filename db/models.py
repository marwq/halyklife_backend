from __future__ import annotations

from db.base import Base  # Import Base from base.py
from sqlalchemy import Column, String, Integer, select
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import bcrypt
import secrets
from sqlalchemy import ForeignKey

class User(Base):
    __tablename__ = 'users'

    iin = Column(String, nullable=False, primary_key=True)
    password_hash = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    created_at = Column(String, default=func.now())
    status = Column(String, default='waiting')
    
    user_data = relationship("UserData", back_populates="user", uselist=False, lazy='joined')

    @classmethod
    async def register(cls, session: AsyncSession, iin: str, password: str) -> 'User':
        password_hash = bcrypt.hash(password)
        access_token = secrets.token_hex(16)
        user = User(iin=iin, password_hash=password_hash, access_token=access_token)
        session.add(user)
        await session.commit()
        return user
    
    @classmethod
    async def get_status(cls, session: AsyncSession, iin: str) -> dict[str]:
        user = await session.execute(select(User).where(cls.iin == iin))
        user = user.scalars().first()
        is_exists = user is not None
        if is_exists:
            return {'is_exists': True, 'status': user.status}
        else:
            return {'is_exists': False}
        
    @classmethod
    async def login(cls, session: AsyncSession, iin: str, password: str) -> User | None:
        user = await session.execute(select(User).where(cls.iin == iin))
        user: User = user.scalars().first()
        if user is None:
            return None
        if bcrypt.verify(password, user.password_hash):
            return user
        else:
            return None
        
    @classmethod
    async def update(cls, session: AsyncSession, iin: str, status: str) -> User | None:
        user = await session.execute(select(User).where(cls.iin == iin))
        user: User = user.scalars().first()
        if user is None:
            return None
        user.status = status
        await session.commit()
        return user
    
    
# class that contain user details like address, firstName, lastName, secondName, org, birthDate, phoneNumber. One-to-one relationship with User. Primary key is iin
class UserData(Base):
    __tablename__ = 'user_data'

    iin = Column(String, ForeignKey('users.iin'), nullable=False, primary_key=True)
    address = Column(String, nullable=False)
    firstName = Column(String, nullable=False)
    lastName = Column(String, nullable=False)
    secondName = Column(String, nullable=False)
    org = Column(String, nullable=False)
    birthDate = Column(String, nullable=False)
    phoneNumber = Column(String)

    user = relationship("User", back_populates="user_data", uselist=False)

    @classmethod
    async def create(cls, session: AsyncSession, iin: str, address: str, firstName: str, lastName: str, secondName: str, org: str, birthDate: str, phoneNumber: str) -> UserData:
        user_data = UserData(iin=iin, address=address, firstName=firstName, lastName=lastName, secondName=secondName, org=org, birthDate=birthDate, phoneNumber=phoneNumber)
        session.add(user_data)
        await session.commit()
        return user_data
    
    @classmethod
    async def get(cls, session: AsyncSession, iin: str) -> UserData | None:
        user_data = await session.execute(select(UserData).where(cls.iin == iin))
        user_data: UserData = user_data.scalars().first()
        return user_data

