from optimes.assets.base import EnergyAsset


class PowerGenerator(EnergyAsset):
    nominal_power: float  # Max capacity [MW]
    variable_cost: float  # [€/MWh]
    availability: list[float] | None = None  # [0-1] per timestep, e.g. for outages
    ramp_up: float | None = None  # MW per timestep
    ramp_down: float | None = None
    min_up_time: int | None = None
    min_down_time: int | None = None
    startup_cost: float | None = None
    shutdown_cost: float | None = None
    emission_factor: float | None = None
