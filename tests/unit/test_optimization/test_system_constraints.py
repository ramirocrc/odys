import logging
from datetime import timedelta

import linopy
import numpy as np
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from odys.domain.entities.battery import Battery
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.profiles import AvailableCapacityProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.model.model_builder import build_model

logger = logging.getLogger(__name__)


@pytest.fixture
def battery1() -> StationaryStorage:
    return StationaryStorage(
        name="batt1",
        battery=Battery(
            max_charge_power=200.0,
            max_discharge_power=200.0,
            capacity=100.0,
            efficiency_charging=0.9,
            efficiency_discharging=0.8,
            soc_start=0.25,
            soc_end=0.5,
        ),
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: Generator,
    generator2: Generator,
    battery1: StationaryStorage,
    load1: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, generator2, battery1, load1])


@pytest.fixture
def energy_system_sample(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
    generator1: Generator,
    load1: FixedLoad,
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_sample,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile_sample),
        scenarios=Scenario(
            profiles=(
                AvailableCapacityProfile(generator=generator1, values=[80, 80, 100]),
                LoadProfile(load=load1, values=demand_profile_sample),
            ),
        ),
    )


@pytest.fixture
def energy_system_with_multiple_scenarios(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
    generator1: Generator,
    generator2: Generator,
    load1: FixedLoad,
) -> EnergySystem:
    stage_fixed_market = EnergyMarket(name="stage_fixed", max_trading_volume_per_step=100, stage_fixed=True)
    other_market = EnergyMarket(name="other", max_trading_volume_per_step=50, stage_fixed=False)
    scenarios = [
        Scenario(
            name="scenario_1",
            probability=0.6,
            profiles=(
                AvailableCapacityProfile(generator=generator1, values=[80, 80, 100]),
                AvailableCapacityProfile(generator=generator2, values=[150, 150, 150]),
                LoadProfile(load=load1, values=demand_profile_sample),
                PriceProfile(market=stage_fixed_market, values=[100, 110, 120]),
                PriceProfile(market=other_market, values=[90, 100, 110]),
            ),
        ),
        Scenario(
            name="scenario_2",
            probability=0.4,
            profiles=(
                AvailableCapacityProfile(generator=generator1, values=[90, 70, 80]),
                AvailableCapacityProfile(generator=generator2, values=[120, 140, 130]),
                LoadProfile(load=load1, values=demand_profile_sample),
                PriceProfile(market=stage_fixed_market, values=[105, 115, 125]),
                PriceProfile(market=other_market, values=[95, 105, 115]),
            ),
        ),
    ]
    return EnergySystem(
        portfolio=asset_portfolio_sample,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile_sample),
        scenarios=scenarios,
        markets=(stage_fixed_market, other_market),
    )


@pytest.fixture
def linopy_model_with_non_anticipativity(
    energy_system_with_multiple_scenarios: EnergySystem,
) -> linopy.Model:
    problem = energy_system_with_multiple_scenarios.build_problem()
    return build_model(problem)


class TestPowerBalanceAndAvailableCapacity:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model: linopy.Model,
        demand_profile_sample: list[float],
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model
        self.demand_profile_sample = demand_profile_sample
        self.time_index = time_index

    def test_constraint_power_balance(self) -> None:
        actual_constraint = self.linopy_model.constraints["power_balance_constraint"]

        generation_total = self.linopy_model.variables["generator_power"].sum("generator")
        discharge_total = self.linopy_model.variables["stationary_storage_power_out"].sum("stationary_storage")
        charge_total = self.linopy_model.variables["stationary_storage_power_in"].sum("stationary_storage")

        # Fixed loads are summed over the load dimension, so no load dimension in the constraint
        demand_data = [
            self.demand_profile_sample,  # Sum of all fixed loads
        ]
        demand_array = xr.DataArray(
            demand_data,
            coords={
                "scenario": ["base"],
                "time": [str(t) for t in self.time_index],
            },
            dims=["scenario", "time"],
        )

        expected_expr = generation_total + discharge_total - charge_total == demand_array

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_available_capacity_profiles(self) -> None:
        actual_constraint = self.linopy_model.constraints["available_capacity_constraint"]
        generator_power = self.linopy_model.variables["generator_power"]

        # Need to include scenario dimension as our system now uses scenarios
        available_capacity_data = [
            [
                [80, 80, 100],  # gen1
                [np.inf, np.inf, np.inf],  # gen2 defaults to inf when no profile provided
            ],
        ]

        available_capacity_array = xr.DataArray(
            available_capacity_data,
            coords={
                "scenario": ["base"],
                "generator": ["gen1", "gen2"],
                "time": [str(t) for t in self.time_index],
            },
            dims=["scenario", "generator", "time"],
        )

        expected_expr = generator_power <= available_capacity_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
        assert bool((actual_constraint.labels != -1).all())


class TestNonAnticipativityConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model_with_non_anticipativity: linopy.Model,
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model_with_non_anticipativity
        self.time_index = time_index

    def test_non_anticipativity_constraints(self) -> None:
        variable_names = (
            EnergyMarketFormulation.sell_volume_name,
            EnergyMarketFormulation.buy_volume_name,
            EnergyMarketFormulation.trade_mode_name,
        )
        for variable_name in variable_names:
            constraint_name = f"non_anticipativity_{variable_name}_constraint"
            actual_constraint = self.linopy_model.constraints[constraint_name]

            linopy_var = self.linopy_model.variables[variable_name]
            stage_fixed_markets = xr.DataArray(
                data=[True, False],
                coords=[["stage_fixed", "other"]],
                dims=["market"],
            )
            fixed_var = linopy_var.where(stage_fixed_markets, drop=True)
            first_scenario_var = fixed_var.isel(scenario=0)
            expected_expr = fixed_var - first_scenario_var == 0
            assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)
            assert bool((actual_constraint.labels != -1).all())
