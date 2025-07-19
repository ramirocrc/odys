from datetime import timedelta
from typing import Self

from pydantic import BaseModel, model_validator


class ScenarioConditions(BaseModel):
    demand_profile: list[float]
    timestep: timedelta
    available_capacity_profiles: dict[str, list[float]] | None = None

    @model_validator(mode="after")
    def _validate_capacity_profile_lengths(self) -> Self:
        if self.available_capacity_profiles is None:
            return self
        demand_profile_length = len(self.demand_profile)
        for asset_name, available_capacity_profile in self.available_capacity_profiles.items():
            if len(available_capacity_profile) != demand_profile_length:
                msg = (
                    f"Available capacity for asset '{asset_name}' has a length of {len(available_capacity_profile)}, "
                    "which does not match demand profile length {demand_profile_length}."
                )
                raise ValueError(msg)
        return self
