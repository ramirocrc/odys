"""Asset system-contribution ports (power balance + profit).

Contract (Phase 2 / ADR 0003):
- ``power_balance_terms(model, params)`` → expression with dims ``(scenario, time)`` only;
  positive = injection into the bus, negative = withdrawal.
- ``profit_terms(model, params)`` → expression with dims ``(scenario,)`` only;
  positive = revenue, negative = cost (objective maximizes).
- Return ``None`` when the asset has no contribution of that kind.
- Kernel skips empty parameter blocks and ``None`` contributors.
- FixedLoad remains a kernel residual (not a registry contributor) until G15.
- Charger has no balance/profit contributions (coupling infrastructure only).
"""

from odys.optimization.model.contributions.electric_vehicle import (
    electric_vehicle_power_balance_terms,
    electric_vehicle_profit_terms,
)
from odys.optimization.model.contributions.flexible_load import (
    flexible_load_power_balance_terms,
    flexible_load_profit_terms,
)
from odys.optimization.model.contributions.generator import (
    generator_power_balance_terms,
    generator_profit_terms,
)
from odys.optimization.model.contributions.market import (
    market_power_balance_terms,
    market_profit_terms,
)
from odys.optimization.model.contributions.standalone_storage import (
    standalone_storage_power_balance_terms,
    standalone_storage_profit_terms,
)

__all__ = [
    "electric_vehicle_power_balance_terms",
    "electric_vehicle_profit_terms",
    "flexible_load_power_balance_terms",
    "flexible_load_profit_terms",
    "generator_power_balance_terms",
    "generator_profit_terms",
    "market_power_balance_terms",
    "market_profit_terms",
    "standalone_storage_power_balance_terms",
    "standalone_storage_profit_terms",
]
