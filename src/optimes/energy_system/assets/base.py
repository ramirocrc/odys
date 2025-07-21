from abc import ABC

from pydantic import BaseModel


class EnergyAsset(BaseModel, ABC):
    name: str
