from pydantic import BaseModel


class Person(BaseModel):
    address: str
    firstName: str
    lastName: str
    secondName: str
    org: str
    birthDate: str
    phoneNumber: str | None = None
    