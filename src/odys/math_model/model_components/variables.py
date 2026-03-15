"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

from pydantic import BaseModel

from odys.math_model.model_components.sets import ModelDimension


class BoundType(Enum):
    """Lower bound type for optimization variables."""

    NON_NEGATIVE = "non_negative"
    UNBOUNDED = "unbounded"


class VariableSpec(BaseModel):
    """Specification for an optimization variable (name, type, dimensions, bounds)."""

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
    STORAGE_POWER_IN = VariableSpec(
        name="storage_power_in",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Storages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STORAGE_POWER_NET = VariableSpec(
        name="storage_net_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Storages],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    STORAGE_POWER_OUT = VariableSpec(
        name="storage_power_out",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Storages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STORAGE_SOC = VariableSpec(
        name="storage_soc",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Storages],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    STORAGE_CHARGE_MODE = VariableSpec(
        name="storage_charge_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Storages],
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
    def asset_dimension(self) -> ModelDimension | None:
        """Get the asset dimension (Generators or Storages) if present."""
        if self.value.dimensions is None:
            return None
        for dim in self.value.dimensions:
            if dim in (ModelDimension.Generators, ModelDimension.Storages):
                return dim
        return None

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
STORAGE_VARIABLES = [
    var for var in ModelVariable if var.value.dimensions and ModelDimension.Storages in var.value.dimensions
]
MARKET_VARIABLES = [
    var for var in ModelVariable if var.value.dimensions and ModelDimension.Markets in var.value.dimensions
]
CVAR_VARIABLES = [ModelVariable.VALUE_AT_RISK, ModelVariable.SHORTFALL_REVENUE]
