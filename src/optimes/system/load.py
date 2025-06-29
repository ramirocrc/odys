from pydantic import BaseModel


class LoadProfile(BaseModel):
    profile: list[float]
