import logging

import uvicorn
from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from enum import Enum

from db.base import SessionLocal
from db.models import User, UserData
from iin_info.api import API
from iin_info.schema import Person
from utils import random_sentence


app = FastAPI(debug=True)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        await request.state.db.close()
    return response

# CORS
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

def get_db(request: Request) -> AsyncSession:
    return request.state.db

class Status(str, Enum):
    waiting = "waiting"
    accepted = "accepted"
    rejected = "rejected"

@app.get("/")
async def root():
    return {"message": "Hello World"}


class PersonOut(BaseModel):
    is_exists: bool
    status: Status | None = None
    person: Person | None = None

@app.get("/person/{person_iin}", response_model=PersonOut, tags=["Registration"])
async def person(person_iin: str, db: AsyncSession = Depends(get_db)):
    status = await User.get_status(db, person_iin)
    
    # find userdata in db
    user_data = await db.execute(select(UserData).where(UserData.iin == person_iin))
    user_data = user_data.scalars().first()
    if user_data is not None:
        return {
            **status,
            "person": Person(
                address=user_data.address,
                firstName=user_data.firstName,
                lastName=user_data.lastName,
                secondName=user_data.secondName,
                org=user_data.org,
                birthDate=user_data.birthDate,
                phoneNumber=user_data.phoneNumber
            )
        }
    
    try:
        async with API() as api:
            person = await api.person(person_iin)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
        
    if person is not None:
        await UserData.create(
            db,
            iin=person_iin,
            address=person.address,
            firstName=person.firstName,
            lastName=person.lastName,
            secondName=person.secondName,
            org=person.org,
            birthDate=person.birthDate,
            phoneNumber=person.phoneNumber
        )
    
    return {
        **status,
        "person": person
    }
    
@app.post("/register", tags=["Registration"])
async def register(response: Response, iin: str, db: AsyncSession = Depends(get_db)):
    is_exists = (await User.get_status(db, iin))["is_exists"]
    if is_exists:
        return {
            "is_exists": True
        }
    
    password = random_sentence()
    user = await User.register(db, iin, password)
    response.set_cookie("access_token", user.access_token, expires=60*60*24*7)
    response.set_cookie("access_token", user.access_token, expires=60*60*24*7)
    return {
        "is_exists": False,
        "password": password
    }
    
@app.post("/login", tags=["Registration"])
async def login(response: Response, iin: str, password: str, db: AsyncSession = Depends(get_db)):
    user = await User.get_status(db, iin)
    if not user["is_exists"]:
        return {
            "is_exists": False
        }
    
    user = await User.login(db, iin, password)
    if user is None:
        return {
            "is_exists": True,
            "is_correct": False
        }
    
    response.set_cookie("access_token", user.access_token, expires=60*60*24*7)
    response.headers["access_token"] = user.access_token
    return {
        "is_exists": True,
        "is_correct": True
    }
    

class UserDataScheme(BaseModel):
    address: str
    firstName: str
    lastName: str
    secondName: str
    org: str
    birthDate: str
    phoneNumber: str | None = None
    
    class Config:
        orm_mode = True

class UserOut(BaseModel):
    iin: str
    created_at: str
    status: Status
    user_data: UserDataScheme | None = None
    
    class Config:
        orm_mode = True

@app.get("/get_users", response_model=list[UserOut], tags=["Admin"])
async def get_users(db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(User))
    users = users.scalars().all()
    return users

@app.put("/update_status", tags=["Admin"])
async def update_status(iin: str, status: Status, db: AsyncSession = Depends(get_db)):
    await User.update(db, iin, status.value)
    return {
        "status": "ok"
    }
    
@app.get("/get_status", tags=["Client"])
async def get_status(request: Request, db: AsyncSession = Depends(get_db)):
    # get access token from cookies
    access_token = request.cookies.get("access_token")
    
    # get user from db
    user = await db.execute(select(User).where(User.access_token == access_token))
    user: User = user.scalars().first()
    if user is None:
        return {
            "is_exists": False,
        }
    else:
        return {
            "is_exists": True,
            "status": user.status
        }