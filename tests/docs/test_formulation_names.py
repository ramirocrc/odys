"""The Mathematical Formulation pages name exactly the constraints and variables the model builds.

One reference model holds every asset type and every conditional constraint. Each documented page owns the
model names with its prefixes: every one of them must appear on the page, and every constraint name the page
mentions must exist in the model. Names written with a placeholder, such as
`generator_min_uptime_{name}_constraint`, stand for one constraint per asset.
"""

import re
from datetime import timedelta
from pathlib import Path

import linopy
import pytest

from odys import (
    AllowedTradeDirection,
    AssetPortfolio,
    Battery,
    Charger,
    CVaRTerm,
    ElectricVehicle,
    ElectricVehicleFinalState,
    ElectricVehicleInitialState,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    FlexibleLoad,
    Generator,
    GeneratorFinalState,
    GeneratorInitialState,
    LoadProfile,
    Objective,
    PriceProfile,
    ProfitTerm,
    Scenario,
    StationaryStorage,
    StorageFinalState,
    StorageInitialState,
    Trip,
)
from odys.optimization.model.model_builder import build_model

FORMULATION_DIR = Path(__file__).parents[2] / "docs" / "formulation"

DOCUMENTED_PAGES: dict[str, tuple[str, ...]] = {
    "generators.md": ("generator_", "available_capacity_"),
    "markets.md": ("market_",),
    "non_anticipativity.md": ("non_anticipativity_",),
    "objective.md": ("cvar_",),
    "power_balance.md": ("power_balance_",),
}

NUMBER_OF_STEPS = 4
TIMESTEP = timedelta(hours=1)
GENERATOR_POWER = 100.0
GENERATOR_MIN_POWER = 20.0
GENERATOR_INITIAL_POWER = 50.0
GENERATOR_MIN_UP_TIME = timedelta(hours=3)
GENERATOR_TIME_ON_BEFORE_START = timedelta(hours=1)
PEAKER_POWER = 30.0
PEAKER_MIN_DOWN_TIME = timedelta(hours=3)
PEAKER_TIME_OFF_BEFORE_START = timedelta(hours=1)
BATTERY_CAPACITY = 10.0
BATTERY_POWER = 5.0
BATTERY_SOC = 0.5
EV_INITIAL_SOC = 0.6
TRIP_ENERGY = 2.0
CHARGER_POWER = 5.0
FLEXIBLE_RANGE = 5.0
FLEXIBLE_VALUE = 30.0
BASE_LOAD = [10.0] * NUMBER_OF_STEPS
MARKET_VOLUME = 200.0
SCENARIO_PRICES = {"high": [80.0, 90.0, 100.0, 70.0], "low": [20.0, 30.0, 40.0, 10.0]}
CVAR_WEIGHT = 0.5
CVAR_CONFIDENCE = 0.9
CONDITIONAL_CONSTRAINTS = (
    "generator_initial_min_uptime_constraint",
    "generator_initial_min_downtime_constraint",
    "generator_final_power_constraint",
    "stationary_storage_soc_end_constraint",
    "ev_soc_end_constraint",
    "market_buy_only_constraint",
    "non_anticipativity_market_sell_volume_constraint",
    "cvar_shortfall_constraint",
)

CONSTRAINT_NAME = re.compile(r"\b[a-z][a-z0-9_]*(?:\{[a-z_]+\}[a-z0-9_]*)*_constraint\b")
PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def _reference_system() -> EnergySystem:
    generator = Generator(
        name="ccgt",
        nominal_power=GENERATOR_POWER,
        variable_cost=40.0,
        min_power=GENERATOR_MIN_POWER,
        min_up_time=GENERATOR_MIN_UP_TIME,
    )
    peaker = Generator(
        name="peaker",
        nominal_power=PEAKER_POWER,
        variable_cost=90.0,
        min_down_time=PEAKER_MIN_DOWN_TIME,
    )
    storage = StationaryStorage(
        name="bess",
        battery=Battery(capacity=BATTERY_CAPACITY, max_charge_power=BATTERY_POWER, max_discharge_power=BATTERY_POWER),
    )
    vehicle = ElectricVehicle(
        name="van",
        battery=Battery(capacity=BATTERY_CAPACITY, max_charge_power=BATTERY_POWER, max_discharge_power=BATTERY_POWER),
        trips=(Trip(name="round", start_time=TIMESTEP, end_time=2 * TIMESTEP, energy_consumption=TRIP_ENERGY),),
    )
    charger = Charger(name="depot", max_power=CHARGER_POWER)
    fixed_load = FixedLoad(name="site")
    flexible_load = FlexibleLoad(
        name="process",
        max_increase=FLEXIBLE_RANGE,
        max_decrease=FLEXIBLE_RANGE,
        value_of_consumption=FLEXIBLE_VALUE,
    )
    day_ahead = EnergyMarket(name="day_ahead", max_trading_volume_per_step=MARKET_VOLUME, stage_fixed=True)
    grid = EnergyMarket(
        name="grid",
        max_trading_volume_per_step=MARKET_VOLUME,
        allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
    )
    scenarios = [
        Scenario(
            name=name,
            probability=1 / len(SCENARIO_PRICES),
            profiles=(
                LoadProfile(load=fixed_load, values=BASE_LOAD),
                LoadProfile(load=flexible_load, values=BASE_LOAD),
                PriceProfile(market=day_ahead, values=prices),
                PriceProfile(market=grid, values=prices),
            ),
        )
        for name, prices in SCENARIO_PRICES.items()
    ]
    return EnergySystem(
        portfolio=AssetPortfolio([generator, peaker, storage, vehicle, charger, fixed_load, flexible_load]),
        markets=(day_ahead, grid),
        scenarios=scenarios,
        timestep=TIMESTEP,
        number_of_steps=NUMBER_OF_STEPS,
        objective=Objective(
            terms=(ProfitTerm(weight=1.0), CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE)),
        ),
        initial_conditions=(
            GeneratorInitialState(
                generator=generator,
                power=GENERATOR_INITIAL_POWER,
                time_in_state=GENERATOR_TIME_ON_BEFORE_START,
            ),
            GeneratorInitialState(generator=peaker, power=0.0, time_in_state=PEAKER_TIME_OFF_BEFORE_START),
            StorageInitialState(storage=storage, soc=BATTERY_SOC),
            ElectricVehicleInitialState(vehicle=vehicle, soc=EV_INITIAL_SOC),
        ),
        final_conditions=(
            GeneratorFinalState(generator=generator, power=GENERATOR_INITIAL_POWER),
            StorageFinalState(storage=storage, soc=BATTERY_SOC),
            ElectricVehicleFinalState(vehicle=vehicle, soc=BATTERY_SOC),
        ),
    )


@pytest.fixture(scope="module")
def model() -> linopy.Model:
    system = _reference_system()
    return build_model(system.build_problem())


def _model_names(model: linopy.Model) -> set[str]:
    return {*model.constraints, *model.variables}


def _documented_constraints(page: str) -> set[str]:
    return set(CONSTRAINT_NAME.findall((FORMULATION_DIR / page).read_text(encoding="utf-8")))


def _matches(documented: str, name: str) -> bool:
    pattern = PLACEHOLDER.sub("[a-z0-9_]+", documented)
    return re.fullmatch(pattern, name) is not None


@pytest.mark.parametrize("name", CONDITIONAL_CONSTRAINTS)
def test_reference_model_conditional_constraint_has_rows(model: linopy.Model, name: str) -> None:
    assert model.constraints[name].labels.size > 0


@pytest.mark.parametrize(("page", "prefixes"), DOCUMENTED_PAGES.items(), ids=list(DOCUMENTED_PAGES))
def test_formulation_page_owned_model_name_is_documented(
    model: linopy.Model,
    page: str,
    prefixes: tuple[str, ...],
) -> None:
    text = (FORMULATION_DIR / page).read_text(encoding="utf-8")
    documented = _documented_constraints(page)
    owned = sorted(name for name in _model_names(model) if name.startswith(prefixes))

    missing = [
        name for name in owned if name not in text and not any(_matches(pattern, name) for pattern in documented)
    ]

    assert owned, f"no model name starts with {prefixes}"
    assert not missing, f"{page} does not name: {missing}"


@pytest.mark.parametrize("page", DOCUMENTED_PAGES, ids=list(DOCUMENTED_PAGES))
def test_formulation_page_documented_constraint_exists_in_model(model: linopy.Model, page: str) -> None:
    constraints = list(model.constraints)

    unknown = sorted(
        documented
        for documented in _documented_constraints(page)
        if not any(_matches(documented, name) for name in constraints)
    )

    assert not unknown, f"{page} names constraints the model does not build: {unknown}"
