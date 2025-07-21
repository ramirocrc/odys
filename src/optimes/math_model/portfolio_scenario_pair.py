from typing import Self

from pydantic import BaseModel, model_validator

from optimes.assets.generator import PowerGenerator
from optimes.assets.portfolio import AssetPortfolio
from optimes.system.scenario import ScenarioConditions
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class PortfolioScenarioPair(BaseModel, arbitrary_types_allowed=True):
    portfolio: AssetPortfolio
    scenario: ScenarioConditions

    @model_validator(mode="after")
    def _validate_inputs(self) -> Self:
        self._validate_available_capacity()
        self._validate_demand_can_be_met()
        return self

    def _validate_available_capacity(self) -> None:
        if self.scenario.available_capacity_profiles is None:
            return
        for asset_name, capacities in self.scenario.available_capacity_profiles.items():
            asset = self.portfolio.get_asset(asset_name)
            if not isinstance(asset, PowerGenerator):
                msg = (
                    "Available capacity can only be specified for generators, "
                    f"but got '{asset_name}' of type {type(asset)}."
                )
            if len(capacities) != len(self.scenario.demand_profile):
                msg = (
                    f"Available capacity for '{asset_name}' has a length of {len(capacities)}, "
                    f"which doesn't  match the length of the load profile ({len(self.scenario.demand_profile)})."
                )
                raise ValueError(msg)

    def _validate_demand_can_be_met(self) -> None:
        self._validate_enough_power_to_meet_demand()
        self._valiate_enough_energy_to_meet_demand()

    def _validate_enough_power_to_meet_demand(self) -> None:
        cumulative_generators_power = sum(gen.nominal_power for gen in self.portfolio.generators)
        # TODO: We assume full capacity can be discharged -> Needs to be limited by max power
        cumulative_battery_capacities = sum(bat.capacity for bat in self.portfolio.batteries)
        max_available_power = cumulative_generators_power + cumulative_battery_capacities
        for t, demand_t in enumerate(self.scenario.demand_profile):
            if max_available_power < demand_t:
                msg = (
                    f"Infeasible problem at time index {t}: "
                    f"Demand = {demand_t}, but maximum available generation + battery = {max_available_power}."
                )
                raise ValueError(msg)

    def _valiate_enough_energy_to_meet_demand(self) -> None:
        # TODO: Validate that:
        # sum(demand * deltat) <= sum(generator.nominal_power) + sum(battery.soc_initial - battery.soc_terminal) # noqa: ERA001, E501
        pass
