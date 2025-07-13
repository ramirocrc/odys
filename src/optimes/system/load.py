from datetime import timedelta

from pydantic import BaseModel


class LoadProfile(BaseModel):
    profile: list[float]
    timedelta: timedelta
