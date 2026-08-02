"""Energy system input validation.

This package provides validation functions for cross-domain consistency
checks on energy system configurations. Each function validates a specific
invariant and raises OdysValidationError on failure.
"""

from odys.domain.validation.electric_vehicles import (
    validate_chargers_and_evs_consistency,
    validate_electric_vehicle_trips,
)
from odys.domain.validation.feasibility import (
    validate_enough_energy_to_meet_demand,
    validate_enough_power_to_meet_demand,
)
from odys.domain.validation.profiles import (
    validate_available_capacity_profiles,
    validate_flexible_load_max_decrease_within_base_profile,
    validate_load_profiles,
)
from odys.domain.validation.scenario_consistency import (
    validate_fixed_loads_consistent_with_scenarios,
    validate_flexible_loads_consistent_with_scenarios,
    validate_markets_consistent_with_scenarios,
)
from odys.domain.validation.system import validate_energy_system_inputs

__all__ = [
    "validate_available_capacity_profiles",
    "validate_chargers_and_evs_consistency",
    "validate_electric_vehicle_trips",
    "validate_energy_system_inputs",
    "validate_enough_energy_to_meet_demand",
    "validate_enough_power_to_meet_demand",
    "validate_fixed_loads_consistent_with_scenarios",
    "validate_flexible_load_max_decrease_within_base_profile",
    "validate_flexible_loads_consistent_with_scenarios",
    "validate_load_profiles",
    "validate_markets_consistent_with_scenarios",
]
