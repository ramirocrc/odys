"""Tests for the EnergySystem class.

This module contains tests for the EnergySystem class which represents
the complete energy system configuration including asset portfolio,
demand profile, and validation logic.
"""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.exceptions import OdysValidationError
from odys.domain.profiles import AvailableCapacityProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem

OVERWEIGHTED_SCENARIO_PROBABILITY = 0.7
HALF_PROBABILITY = 0.5


@pytest.fixture
def testing_generator() -> Generator:
    return Generator(
        name="test_generator",
        nominal_power=100.0,  # 100 MW
        variable_cost=50.0,  # 50 currency/MWh
    )


@pytest.fixture
def testing_battery() -> StationaryStorage:
    return StationaryStorage(
        name="test_battery",
        battery=Battery(
            capacity=50.0,
            max_charge_power=25.0,
            max_discharge_power=25.0,
            efficiency_charging=0.9,
            efficiency_discharging=0.9,
            soc_start=0.5,
        ),
    )


@pytest.fixture
def testing_load() -> FixedLoad:
    return FixedLoad(name="test_load")


@pytest.fixture
def testing_portfolio(
    testing_generator: Generator,
    testing_battery: StationaryStorage,
    testing_load: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[testing_generator, testing_battery, testing_load])


@pytest.fixture
def valid_demand_profile() -> list[float]:
    return [80.0, 100.0, 90.0, 120.0]


@pytest.fixture
def valid_timestep() -> timedelta:
    return timedelta(hours=1)


def test_energy_system_creation_with_valid_inputs(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    valid_timestep: timedelta,
    testing_load: FixedLoad,
) -> None:
    """Test that EnergySystem can be created with valid inputs."""
    EnergySystem(
        portfolio=testing_portfolio,
        number_of_steps=len(valid_demand_profile),
        timestep=valid_timestep,
        scenarios=Scenario(profiles=(LoadProfile(load=testing_load, values=valid_demand_profile),)),
    )


def test_validation_of_capacity_profile_lengths(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    valid_timestep: timedelta,
    testing_generator: Generator,
    testing_load: FixedLoad,
) -> None:
    """Test validation that available capacity profiles match demand profile length."""
    demand = LoadProfile(load=testing_load, values=valid_demand_profile)
    valid_capacity = AvailableCapacityProfile(generator=testing_generator, values=[90.0, 100.0, 95.0, 100.0])

    energy_system = EnergySystem(
        portfolio=testing_portfolio,
        number_of_steps=len(valid_demand_profile),
        timestep=valid_timestep,
        scenarios=Scenario(profiles=(valid_capacity, demand)),
    )

    assert energy_system.scenario_set.scenarios[0].profiles == (valid_capacity, demand)

    invalid_capacity = AvailableCapacityProfile(generator=testing_generator, values=[90.0, 100.0])

    with pytest.raises(
        OdysValidationError,
        match=r"the AvailableCapacityProfile for '.*' has 2 values, but the horizon has 4 steps",
    ):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(valid_demand_profile),
            timestep=valid_timestep,
            scenarios=Scenario(profiles=(invalid_capacity, demand)),
        )


def test_validation_that_capacity_profiles_only_for_generators(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    testing_generator: Generator,
    testing_battery: StationaryStorage,
    testing_load: FixedLoad,
) -> None:
    """Test that a capacity profile cannot target a non-generator asset through a name clash."""
    generator_named_like_battery = testing_generator.model_copy(update={"name": testing_battery.name})

    with pytest.raises(
        OdysValidationError,
        match="AvailableCapacityProfile for 'test_battery' does not reference the entity of that name",
    ):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(valid_demand_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(
                profiles=(
                    AvailableCapacityProfile(generator=generator_named_like_battery, values=[25.0, 25.0, 25.0, 25.0]),
                    LoadProfile(load=testing_load, values=valid_demand_profile),
                ),
            ),
        )


def test_validation_that_system_can_meet_power_demand(
    testing_portfolio: AssetPortfolio,
    valid_timestep: timedelta,
    testing_load: FixedLoad,
) -> None:
    """Test validation that the system has enough power capacity to meet peak demand."""

    excessive_demand = [80.0, 200.0, 90.0, 150.0]  # 200 MW exceeds 150 MW capacity

    with pytest.raises(OdysValidationError, match="Infeasible problem"):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(excessive_demand),
            timestep=valid_timestep,
            scenarios=Scenario(profiles=(LoadProfile(load=testing_load, values=excessive_demand),)),
        )


@pytest.fixture
def testing_market() -> EnergyMarket:
    return EnergyMarket(name="test_market", max_trading_volume_per_step=100.0)


@pytest.fixture
def portfolio_without_loads() -> AssetPortfolio:
    return AssetPortfolio(assets=[Generator(name="gen", nominal_power=100.0, variable_cost=50.0)])


@pytest.fixture
def portfolio_without_generators() -> AssetPortfolio:
    return AssetPortfolio(
        assets=[
            StationaryStorage(
                name="battery",
                battery=Battery(
                    capacity=50.0,
                    max_charge_power=25.0,
                    max_discharge_power=25.0,
                    efficiency_charging=0.9,
                    efficiency_discharging=0.9,
                    soc_start=0.5,
                ),
            ),
            FixedLoad(name="load"),
        ],
    )


@pytest.fixture
def empty_portfolio() -> AssetPortfolio:
    return AssetPortfolio()


def test_load_validation_missing_load_profiles(testing_portfolio: AssetPortfolio) -> None:
    """Test validation when portfolio has loads but scenario has no load profiles."""
    with pytest.raises(
        OdysValidationError,
        match=r"Scenario 'base' is missing a LoadProfile for: \['",
    ):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(),
        )


def test_load_validation_missing_specific_load_profile(
    testing_generator: Generator,
    testing_load: FixedLoad,
) -> None:
    """Test validation when scenario is missing profiles for specific loads."""
    other_load = FixedLoad(name="other_load")
    with pytest.raises(OdysValidationError, match=r"Scenario.*is missing a LoadProfile for: \['other_load'\]"):
        EnergySystem(
            portfolio=AssetPortfolio(assets=[testing_generator, testing_load, other_load]),
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(profiles=(LoadProfile(load=testing_load, values=[80.0, 20.0, 30.0, 40.0]),)),
        )


def test_load_validation_extra_load_profiles(testing_portfolio: AssetPortfolio, testing_load: FixedLoad) -> None:
    """Test validation when scenario has profiles for loads not in portfolio."""
    with pytest.raises(
        OdysValidationError,
        match=r"Scenario.*has a LoadProfile for 'extra_load', which is not in the energy system",
    ):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(
                profiles=(
                    LoadProfile(load=testing_load, values=[80.0, 120.0, 90.0, 150.0]),
                    LoadProfile(load=FixedLoad(name="extra_load"), values=[10.0, 20.0, 30.0, 40.0]),
                ),
            ),
        )


def test_load_validation_no_loads_but_has_profiles(portfolio_without_loads: AssetPortfolio) -> None:
    """Test validation when portfolio has no loads but scenario has load profiles."""
    with pytest.raises(
        OdysValidationError,
        match=r"Scenario.*has a LoadProfile for 'some_load', which is not in the energy system",
    ):
        EnergySystem(
            portfolio=portfolio_without_loads,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(
                profiles=(LoadProfile(load=FixedLoad(name="some_load"), values=[80.0, 120.0, 90.0, 150.0]),),
            ),
        )


def test_market_validation_missing_market_prices(
    testing_portfolio: AssetPortfolio,
    testing_market: EnergyMarket,
    testing_load: FixedLoad,
) -> None:
    """Test validation when portfolio has markets but scenario has no market prices."""
    with pytest.raises(OdysValidationError, match=r"Scenario 'base' is missing a PriceProfile for: \['"):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            markets=testing_market,
            scenarios=Scenario(profiles=(LoadProfile(load=testing_load, values=[80.0, 120.0, 90.0, 150.0]),)),
        )


def test_market_validation_missing_specific_market_prices(
    testing_portfolio: AssetPortfolio,
    testing_market: EnergyMarket,
    testing_load: FixedLoad,
) -> None:
    """Test validation when scenario is missing prices for specific markets."""
    other_market = testing_market.model_copy(update={"name": "other_market"})
    with pytest.raises(OdysValidationError, match=r"Scenario.*is missing a PriceProfile for: \['other_market'\]"):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            markets=[testing_market, other_market],
            scenarios=Scenario(
                profiles=(
                    LoadProfile(load=testing_load, values=[80.0, 120.0, 90.0, 150.0]),
                    PriceProfile(market=testing_market, values=[10.0, 20.0, 30.0, 40.0]),
                ),
            ),
        )


def test_market_validation_extra_market_prices(
    testing_portfolio: AssetPortfolio,
    testing_market: EnergyMarket,
    testing_load: FixedLoad,
) -> None:
    """Test validation when scenario has prices for markets not in portfolio."""
    with pytest.raises(
        OdysValidationError,
        match=r"Scenario.*has a PriceProfile for 'extra_market', which is not in the energy system",
    ):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            markets=testing_market,
            scenarios=Scenario(
                profiles=(
                    LoadProfile(load=testing_load, values=[80.0, 120.0, 90.0, 150.0]),
                    PriceProfile(market=testing_market, values=[10.0, 20.0, 30.0, 40.0]),
                    PriceProfile(
                        market=testing_market.model_copy(update={"name": "extra_market"}),
                        values=[5.0, 15.0, 25.0, 35.0],
                    ),
                ),
            ),
        )


def test_market_validation_no_markets_but_has_prices(
    portfolio_without_loads: AssetPortfolio,
    testing_market: EnergyMarket,
) -> None:
    """Test validation when portfolio has no markets but scenario has market prices."""
    with pytest.raises(
        OdysValidationError,
        match=r"Scenario.*has a PriceProfile for '.*', which is not in the energy system",
    ):
        EnergySystem(
            portfolio=portfolio_without_loads,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(profiles=(PriceProfile(market=testing_market, values=[10.0, 20.0, 30.0, 40.0]),)),
        )


def test_load_profile_length_validation(testing_portfolio: AssetPortfolio, testing_load: FixedLoad) -> None:
    """Test validation of load profile length mismatch."""
    with pytest.raises(
        OdysValidationError,
        match=r"the LoadProfile for '.*' has 2 values, but the horizon has 4 steps",
    ):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(profiles=(LoadProfile(load=testing_load, values=[80.0, 120.0]),)),
        )


def test_capacity_profile_value_validation(
    testing_portfolio: AssetPortfolio,
    testing_generator: Generator,
    testing_load: FixedLoad,
) -> None:
    """Test validation of capacity profile values outside valid range."""
    with pytest.raises(OdysValidationError, match=r"Available capacity value.*is invalid"):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(
                profiles=(
                    AvailableCapacityProfile(generator=testing_generator, values=[90.0, 150.0, 95.0, 100.0]),
                    LoadProfile(load=testing_load, values=[80.0, 120.0, 90.0, 100.0]),
                ),
            ),
        )


def test_empty_load_profiles_validation(portfolio_without_loads: AssetPortfolio) -> None:
    """Test validation when load profiles is empty (should trigger empty load profile error)."""
    with pytest.raises(OdysValidationError, match="Load profile is empty, there is nothing to balance"):
        EnergySystem(
            portfolio=portfolio_without_loads,
            number_of_steps=4,
            timestep=timedelta(hours=1),
            scenarios=Scenario(),
        )


@pytest.mark.parametrize("sequence_type", [list, tuple], ids=["list", "tuple"])
def test_stochastic_scenarios_not_summing_to_one_raise_for_any_sequence_type(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    sequence_type: type[list[Scenario]] | type[tuple[Scenario, ...]],
    testing_load: FixedLoad,
) -> None:
    scenarios = sequence_type(
        Scenario(
            name=f"s{i}",
            probability=OVERWEIGHTED_SCENARIO_PROBABILITY,
            profiles=(LoadProfile(load=testing_load, values=valid_demand_profile),),
        )
        for i in range(2)
    )
    with pytest.raises(OdysValidationError, match="Scenarios should add up to 1"):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(valid_demand_profile),
            timestep=timedelta(hours=1),
            scenarios=scenarios,
        )


@pytest.mark.parametrize("sequence_type", [list, tuple], ids=["list", "tuple"])
def test_stochastic_scenarios_with_duplicate_names_raise_for_any_sequence_type(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    sequence_type: type[list[Scenario]] | type[tuple[Scenario, ...]],
    testing_load: FixedLoad,
) -> None:
    scenarios = sequence_type(
        Scenario(
            name="duplicate",
            probability=HALF_PROBABILITY,
            profiles=(LoadProfile(load=testing_load, values=valid_demand_profile),),
        )
        for _ in range(2)
    )
    with pytest.raises(OdysValidationError, match="must have a unique name"):
        EnergySystem(
            portfolio=testing_portfolio,
            number_of_steps=len(valid_demand_profile),
            timestep=timedelta(hours=1),
            scenarios=scenarios,
        )


class _UnsupportedHeatPump(Asset):
    """An asset type the optimizer has no model for."""


@pytest.mark.parametrize(
    "unsupported_asset",
    [Asset(name="bare_asset"), _UnsupportedHeatPump(name="heat_pump")],
    ids=["bare_asset", "unknown_subclass"],
)
def test_energy_system_rejects_asset_types_the_optimizer_cannot_model(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    unsupported_asset: Asset,
    testing_load: FixedLoad,
) -> None:
    portfolio = AssetPortfolio([*testing_portfolio.assets.values(), unsupported_asset])
    with pytest.raises(OdysValidationError, match=rf"not supported.*'{unsupported_asset.name}'"):
        EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(valid_demand_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(profiles=(LoadProfile(load=testing_load, values=valid_demand_profile),)),
        )


def test_single_scenario_is_normalized_to_a_one_element_scenario_set(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    testing_load: FixedLoad,
    testing_market: EnergyMarket,
) -> None:
    scenario = Scenario(
        profiles=(
            LoadProfile(load=testing_load, values=valid_demand_profile),
            PriceProfile(market=testing_market, values=[10.0, 20.0, 30.0, 40.0]),
        ),
    )
    energy_system = EnergySystem(
        portfolio=testing_portfolio,
        number_of_steps=len(valid_demand_profile),
        timestep=timedelta(hours=1),
        markets=testing_market,
        scenarios=scenario,
    )

    assert energy_system.scenario_set.scenarios == (scenario,)
    assert energy_system.scenario_set.names == ("base",)
    assert energy_system.collection_of_markets == (testing_market,)


def test_scenario_sequence_is_normalized_to_a_scenario_set_in_order(
    testing_portfolio: AssetPortfolio,
    valid_demand_profile: list[float],
    testing_load: FixedLoad,
) -> None:
    demand = LoadProfile(load=testing_load, values=valid_demand_profile)
    scenarios = [
        Scenario(name="low", probability=HALF_PROBABILITY, profiles=(demand,)),
        Scenario(name="high", probability=HALF_PROBABILITY, profiles=(demand,)),
    ]
    energy_system = EnergySystem(
        portfolio=testing_portfolio,
        number_of_steps=len(valid_demand_profile),
        timestep=timedelta(hours=1),
        scenarios=scenarios,
    )

    assert energy_system.scenario_set.scenarios == tuple(scenarios)
    assert energy_system.collection_of_markets == ()


@pytest.mark.parametrize(
    ("timestep", "number_of_steps", "message"),
    [
        (timedelta(0), 2, r"timestep\n  Input should be greater than 0 seconds"),
        (timedelta(hours=1), 0, r"number_of_steps\n  Input should be greater than or equal to 1"),
    ],
    ids=["zero_timestep", "no_steps"],
)
def test_energy_system_rejects_an_invalid_horizon(
    testing_load: FixedLoad,
    timestep: timedelta,
    number_of_steps: int,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        EnergySystem(
            portfolio=AssetPortfolio(assets=[testing_load]),
            number_of_steps=number_of_steps,
            timestep=timestep,
            scenarios=Scenario(profiles=(LoadProfile(load=testing_load, values=[1.0, 1.0]),)),
        )
