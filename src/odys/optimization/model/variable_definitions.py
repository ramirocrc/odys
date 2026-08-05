"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

from pydantic import BaseModel, ConfigDict

from odys.optimization.model.dimensions import ModelDimension


class BoundType(Enum):
    """Lower bound type for optimization variables."""

    NON_NEGATIVE = "non_negative"
    UNBOUNDED = "unbounded"


class VariableDefinition(BaseModel):
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
class VariableDefinitionRegistry(Enum):
    """All decision variables in the energy system optimization model."""

    GENERATOR_POWER = VariableDefinition(
        name="generator_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    GENERATOR_STATUS = VariableDefinition(
        name="generator_status",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    GENERATOR_STARTUP = VariableDefinition(
        name="generator_startup",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    GENERATOR_SHUTDOWN = VariableDefinition(
        name="generator_shutdown",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    STANDALONE_STORAGE_POWER_IN = VariableDefinition(
        name="standalone_storage_power_in",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STANDALONE_STORAGE_POWER_NET = VariableDefinition(
        name="standalone_storage_net_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    STANDALONE_STORAGE_POWER_OUT = VariableDefinition(
        name="standalone_storage_power_out",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STANDALONE_STORAGE_SOC = VariableDefinition(
        name="standalone_storage_soc",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STANDALONE_STORAGE_CHARGE_MODE = VariableDefinition(
        name="standalone_storage_charge_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.StandaloneStorages],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    EV_POWER_IN = VariableDefinition(
        name="ev_power_in",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    EV_POWER_NET = VariableDefinition(
        name="ev_net_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    EV_POWER_OUT = VariableDefinition(
        name="ev_power_out",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    EV_SOC = VariableDefinition(
        name="ev_soc",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    EV_CHARGE_MODE = VariableDefinition(
        name="ev_charge_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.EVs],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    MARKET_SELL = VariableDefinition(
        name="market_sell_volume",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    MARKET_BUY = VariableDefinition(
        name="market_buy_volume",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    MARKET_TRADE_MODE = VariableDefinition(
        name="market_trade_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    LOAD_ADJUSTMENT = VariableDefinition(
        name="load_adjustment",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.FlexibleLoads],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    CHARGER_EV_ASSIGNMENT = VariableDefinition(
        name="charger_ev_assignment",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Chargers, ModelDimension.EVs],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    VALUE_AT_RISK = VariableDefinition(
        name="cvar_value_at_risk",
        is_binary=False,
        dimensions=None,
        lower_bound_type=BoundType.UNBOUNDED,
    )
    SHORTFALL_REVENUE = VariableDefinition(
        name="cvar_shortfall",
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
    var
    for var in VariableDefinitionRegistry
    if var.value.dimensions and ModelDimension.Generators in var.value.dimensions
]
STANDALONE_STORAGE_VARIABLES = [
    var
    for var in VariableDefinitionRegistry
    if var.value.dimensions and ModelDimension.StandaloneStorages in var.value.dimensions
]
FLEXIBLE_LOAD_VARIABLES = [
    var
    for var in VariableDefinitionRegistry
    if var.value.dimensions and ModelDimension.FlexibleLoads in var.value.dimensions
]
MARKET_VARIABLES = [
    var for var in VariableDefinitionRegistry if var.value.dimensions and ModelDimension.Markets in var.value.dimensions
]
CHARGER_VARIABLES = [
    var
    for var in VariableDefinitionRegistry
    if var.value.dimensions and ModelDimension.Chargers in var.value.dimensions
]
EV_VARIABLES = [
    var
    for var in VariableDefinitionRegistry
    if var.value.dimensions
    and ModelDimension.EVs in var.value.dimensions
    and var is not VariableDefinitionRegistry.CHARGER_EV_ASSIGNMENT
]
CVAR_VARIABLES = [VariableDefinitionRegistry.VALUE_AT_RISK, VariableDefinitionRegistry.SHORTFALL_REVENUE]
