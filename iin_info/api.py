from __future__ import annotations

from aiohttp import ClientSession

from .schema import Person
import settings



class API:
    BASE_URL = settings.MAGIC_ENDPOINT
    SECRET = settings.MAGIC_SECRET
    
    def __init__(self, session: ClientSession | None = None) -> None:
        self.session = session
        
    async def __aenter__(self) -> API:
        if self.session is None:
            self.session = ClientSession()
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.session.close()
        
    async def person(self, iin: str) -> Person:
        
        async with self.session.post(
            f"{self.BASE_URL}/api/v1/person/",
            headers={"X-API-KEY": self.SECRET},
            json={"iin": iin}
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        
        async with self.session.post(
            f"{self.BASE_URL}/api/v1/address/",
            headers={"X-API-KEY": self.SECRET},
            json={"iin": iin}
        ) as resp:
            resp.raise_for_status()
            data |= await resp.json()
        
        return Person(**data)