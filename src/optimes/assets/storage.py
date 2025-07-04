from optimes.assets.base import EnergyAsset


class Battery(EnergyAsset):
    capacity: float  # Energy capacity [MWh]
    max_power: float  # Max charge/discharge power [MW]
    efficiency_charging: float  # Charge efficiency [0-1]
    efficiency_discharging: float  # Charge efficiency [0-1]
    soc_start: float  # Initial SoC [MWh]
    soc_end: float | None = None  # Optional final SoC [MWh]
    soc_min: float = 0.0  # Minimum SoC [MWh]
    degradation_cost: float | None = None  # €/MWh cycled
    self_discharge_rate: float | None = None  # [% per timestep]
