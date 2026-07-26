"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

from pydantic import BaseModel, ConfigDict

from odys.optimization.model.sets import ModelDimension


class BoundType(Enum):
    """Lower bound type for optimization variables."""

    NON_NEGATIVE = "non_negative"
    UNBOUNDED = "unbounded"


class VariableSpec(BaseModel):
    """Specification for an optimization variable (name, type, dimensions, bounds)."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    name: str
    is_binary: bool
    dimensions: list[ModelDimension] | None
    lower_bound_type: BoundType


@unique
class ModelVariable(Enum):
    """All decision variables in the energy system optimization model."""

    GENERATOR_POWER = VariableSpec(
        name="generator_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    GENERATOR_STATUS = VariableSpec(
        name="generator_status",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    GENERATOR_STARTUP = VariableSpec(
        name="generator_startup",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    GENERATOR_SHUTDOWN = VariableSpec(
        name="generator_shutdown",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    STANDALONE_STORAGE_POWER_IN = VariableSpec(
        name="standalone_storage_power_in",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STANDALONE_STORAGE_POWER_NET = VariableSpec(
        name="standalone_storage_net_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    STANDALONE_STORAGE_POWER_OUT = VariableSpec(
        name="standalone_storage_power_out",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STANDALONE_STORAGE_SOC = VariableSpec(
        name="standalone_storage_soc",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STANDALONE_STORAGE_CHARGE_MODE = VariableSpec(
        name="standalone_storage_charge_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    EV_POWER_IN = VariableSpec(
        name="ev_power_in",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    EV_POWER_NET = VariableSpec(
        name="ev_net_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    EV_POWER_OUT = VariableSpec(
        name="ev_power_out",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    EV_SOC = VariableSpec(
        name="ev_soc",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    EV_CHARGE_MODE = VariableSpec(
        name="ev_charge_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    MARKET_SELL = VariableSpec(
        name="market_sell_volume",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    MARKET_BUY = VariableSpec(
        name="market_buy_volume",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    MARKET_TRADE_MODE = VariableSpec(
        name="market_trade_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    LOAD_ADJUSTMENT = VariableSpec(
        name="load_adjustment",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.FlexibleLoads],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    CHARGER_EV_ASSIGNMENT = VariableSpec(
        name="charger_ev_assignment",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Chargers, ModelDimension.EVs],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    VALUE_AT_RISK = VariableSpec(
        name="value_at_risk",
        is_binary=False,
        dimensions=None,
        lower_bound_type=BoundType.UNBOUNDED,
    )
    SHORTFALL_REVENUE = VariableSpec(
        name="shortfall_revenue",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )

    @property
    def var_name(self) -> str:
        """Return the variable name used in the linopy model."""
        return self.value.name

    @property
    def dimensions(self) -> list[ModelDimension] | None:
        """Return the dimensions this variable is defined over."""
        return self.value.dimensions

    @property
    def lower_bound_type(self) -> BoundType:
        """Return the lower bound type for this variable."""
        return self.value.lower_bound_type

    @property
    def is_binary(self) -> bool:
        """Return whether this variable is binary."""
        return self.value.is_binary


GENERATOR_VARIABLES = [
    var for var in ModelVariable if var.value.dimensions and ModelDimension.Generators in var.value.dimensions
]
STANDALONE_STORAGE_VARIABLES = [
    var for var in ModelVariable if var.value.dimensions and ModelDimension.StandaloneStorages in var.value.dimensions
]
FLEXIBLE_LOAD_VARIABLES = [
    var for var in ModelVariable if var.value.dimensions and ModelDimension.FlexibleLoads in var.value.dimensions
]
MARKET_VARIABLES = [
    var for var in ModelVariable if var.value.dimensions and ModelDimension.Markets in var.value.dimensions
]
CHARGER_VARIABLES = [
    var for var in ModelVariable if var.value.dimensions and ModelDimension.Chargers in var.value.dimensions
]
EV_VARIABLES = [
    var
    for var in ModelVariable
    if var.value.dimensions
    and ModelDimension.EVs in var.value.dimensions
    and var is not ModelVariable.CHARGER_EV_ASSIGNMENT
]
CVAR_VARIABLES = [ModelVariable.VALUE_AT_RISK, ModelVariable.SHORTFALL_REVENUE]
