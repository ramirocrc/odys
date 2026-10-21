"""Integration test for flexible load optimization."""

from datetime import timedelta

import pytest

from odys import (
    AllowedTradeDirection,
    AssetPortfolio,
    AvailableCapacityProfile,
    Battery,
    BatteryStorage,
    CVaRTerm,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    FlexibleLoad,
    FlexibleLoadProfile,
    Generator,
    LoadProfile,
    Objective,
    PriceProfile,
    ProfitTerm,
    Scenario,
    StorageFinalState,
    StorageInitialState,
)

TOLERANCE = 1e-5
TWO_FLEXIBLE_LOADS = 2
SIX_ENTRIES = 6


def _constant_range(load: FlexibleLoad, lower: float, upper: float, steps: int) -> FlexibleLoadProfile:
    return FlexibleLoadProfile(load=load, lower_bound=[lower] * steps, upper_bound=[upper] * steps)


def test_flexible_load_runs_at_its_lower_bound_when_supply_costs_more_than_its_value() -> None:
    """value_of_consumption (30) < marginal supply cost (generator, 50): the load runs at its lower bound."""
    generator = Generator(name="gen1", nominal_power=200.0, variable_cost=50.0)
    flexible_load = FlexibleLoad(name="flex_load", value_of_consumption=30.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, flexible_load]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            profiles=(
                _constant_range(flexible_load, 70.0, 150.0, 3),
                PriceProfile(market=market, values=[80.0, 80.0, 80.0]),
            ),
        ),
    )

    consumption = system.optimize().flexible_loads.consumption

    assert consumption.to_numpy() == pytest.approx([70.0] * 3, abs=TOLERANCE)


def test_flexible_load_runs_at_its_upper_bound_when_its_value_exceeds_the_supply_cost() -> None:
    """value_of_consumption (100) > marginal supply cost (generator, 10): the load runs at its upper bound."""
    generator = Generator(name="gen1", nominal_power=200.0, variable_cost=10.0)
    flexible_load = FlexibleLoad(name="flex_load", value_of_consumption=100.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, flexible_load]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            profiles=(
                _constant_range(flexible_load, 70.0, 150.0, 3),
                PriceProfile(market=market, values=[20.0, 20.0, 20.0]),
            ),
        ),
    )

    consumption = system.optimize().flexible_loads.consumption

    assert consumption.to_numpy() == pytest.approx([150.0] * 3, abs=TOLERANCE)


def test_flexible_load_with_fixed_load() -> None:
    """value_of_consumption (50) > marginal cost (generator, 30): the flexible load runs at its upper bound."""
    generator = Generator(name="gen1", nominal_power=300.0, variable_cost=30.0)
    fixed_load = FixedLoad(name="fixed_load")
    flexible_load = FlexibleLoad(name="flex_load", value_of_consumption=50.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, fixed_load, flexible_load]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=2,
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=fixed_load, values=[100.0, 100.0]),
                _constant_range(flexible_load, 60.0, 120.0, 2),
                PriceProfile(market=market, values=[20.0, 20.0]),
            ),
        ),
    )

    results = system.optimize()
    consumption = results.flexible_loads.consumption

    assert consumption.to_numpy() == pytest.approx([120.0, 120.0], abs=TOLERANCE)

    solution = results.to_dataset()
    supply = solution["generator_power"].sum("generator") + (
        solution["market_buy_volume"] - solution["market_sell_volume"]
    ).sum("market")
    assert supply.to_numpy() == pytest.approx([100.0 + 120.0] * 2, abs=TOLERANCE)


def test_flexible_load_with_generator_capacity_constraint() -> None:
    """A flexible load consumes less than its upper bound when generator capacity can't cover it.

    No market is configured, so the generator is the only supply source. At t=1 the
    generator's available capacity (80 MW) leaves only 20 MW after the fixed load (60 MW),
    so the flexible load consumes exactly that. At t=0 and t=2 capacity is ample, and
    since value_of_consumption (100) > generator variable_cost (40) the load runs at
    its upper bound.
    """
    generator = Generator(name="gen1", nominal_power=150.0, variable_cost=40.0)
    fixed_load = FixedLoad(name="fixed_load")
    flexible_load = FlexibleLoad(name="flex_load", value_of_consumption=100.0)
    available_capacity = [150.0, 80.0, 150.0]

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, fixed_load, flexible_load]),
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            profiles=(
                AvailableCapacityProfile(generator=generator, values=available_capacity),
                LoadProfile(load=fixed_load, values=[60.0, 60.0, 60.0]),
                _constant_range(flexible_load, 10.0, 80.0, 3),
            ),
        ),
    )

    results = system.optimize()
    consumption = results.flexible_loads.consumption

    assert consumption.to_numpy() == pytest.approx([80.0, 20.0, 80.0], abs=TOLERANCE)

    gen_power = results.to_dataset()["generator_power"].sel(generator="gen1").to_numpy()
    assert gen_power == pytest.approx(60.0 + consumption.to_numpy(), abs=TOLERANCE)
    assert all(power <= capacity + TOLERANCE for power, capacity in zip(gen_power, available_capacity, strict=True))


def test_multiple_flexible_loads() -> None:
    """Of two flexible loads, the one worth more than the market price runs high, the other low."""
    generator = Generator(name="gen1", nominal_power=300.0, variable_cost=40.0)
    flex_load_1 = FlexibleLoad(name="flex_load_1", value_of_consumption=60.0)
    flex_load_2 = FlexibleLoad(name="flex_load_2", value_of_consumption=20.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, flex_load_1, flex_load_2]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            profiles=(
                _constant_range(flex_load_1, 80.0, 130.0, 3),
                _constant_range(flex_load_2, 65.0, 105.0, 3),
                PriceProfile(market=market, values=[50.0, 50.0, 50.0]),
            ),
        ),
    )

    results = system.optimize()

    assert len(results.flexible_loads) == TWO_FLEXIBLE_LOADS
    assert "flex_load_1" in results.flexible_loads
    assert "flex_load_2" in results.flexible_loads
    assert results.flexible_loads["flex_load_1"].consumption.to_numpy() == pytest.approx([130.0] * 3, abs=TOLERANCE)
    assert results.flexible_loads["flex_load_2"].consumption.to_numpy() == pytest.approx([65.0] * 3, abs=TOLERANCE)


def test_flexible_load_with_storage() -> None:
    """Flexible loads work with storage assets, and the power balance holds."""
    generator = Generator(name="gen1", nominal_power=150.0, variable_cost=50.0)
    battery = BatteryStorage(
        name="battery",
        battery=Battery(
            capacity=100.0,
            max_charge_power=50.0,
            max_discharge_power=50.0,
            efficiency_charging=0.9,
            efficiency_discharging=0.9,
        ),
    )
    flexible_load = FlexibleLoad(name="flex_load", value_of_consumption=70.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=500.0)

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, battery, flexible_load]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=4,
        scenarios=Scenario(
            profiles=(
                _constant_range(flexible_load, 80.0, 130.0, 4),
                PriceProfile(market=market, values=[60.0, 60.0, 60.0, 60.0]),
            ),
        ),
        initial_conditions=(StorageInitialState(storage=battery, soc=0.5),),
        final_conditions=(StorageFinalState(storage=battery, soc=0.5),),
    )

    results = system.optimize()
    consumption = results.flexible_loads.consumption

    assert consumption.to_numpy() == pytest.approx([130.0] * 4, abs=TOLERANCE)
    assert len(results.battery_storages.soc) > 0

    solution = results.to_dataset()
    supply = (
        solution["generator_power"].sum("generator")
        + (solution["battery_storage_power_out"] - solution["battery_storage_power_in"]).sum("battery_storage")
        + (solution["market_buy_volume"] - solution["market_sell_volume"]).sum("market")
    )
    assert supply.to_numpy() == pytest.approx(consumption.to_numpy(), abs=TOLERANCE)


def test_flexible_load_stochastic_scenarios() -> None:
    """Each scenario's consumption follows that scenario's range."""
    generator = Generator(name="gen1", nominal_power=200.0, variable_cost=30.0)
    flexible_load = FlexibleLoad(name="flex_load", value_of_consumption=50.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=500.0)

    scenarios = [
        Scenario(
            name="high_demand",
            probability=0.6,
            profiles=(
                _constant_range(flexible_load, 95.0, 160.0, 3),
                PriceProfile(market=market, values=[40.0, 40.0, 40.0]),
            ),
        ),
        Scenario(
            name="low_demand",
            probability=0.4,
            profiles=(
                _constant_range(flexible_load, 55.0, 120.0, 3),
                PriceProfile(market=market, values=[40.0, 40.0, 40.0]),
            ),
        ),
    ]

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, flexible_load]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=scenarios,
    )

    results = system.optimize()

    assert results.solver_status == "ok"
    assert results.termination_condition == "optimal"

    consumption = results.flexible_loads.consumption

    assert len(consumption) == SIX_ENTRIES
    assert consumption.xs("high_demand", level="scenario").to_numpy() == pytest.approx([160.0] * 3, abs=TOLERANCE)
    assert consumption.xs("low_demand", level="scenario").to_numpy() == pytest.approx([120.0] * 3, abs=TOLERANCE)


def _build_cvar_flexible_load_system(objective: Objective) -> EnergySystem:
    generator = Generator(name="gen1", nominal_power=100.0, variable_cost=0.0)
    flexible_load = FlexibleLoad(name="flex_load", value_of_consumption=30.0)
    market = EnergyMarket(
        name="market1",
        max_trading_volume_per_step=50.0,
        stage_fixed=True,
        allowed_trade_direction=AllowedTradeDirection.SELL_ONLY,
    )
    flexible_range = _constant_range(flexible_load, 49.0, 90.0, 1)

    scenarios = [
        Scenario(
            name="high",
            probability=1 / 3,
            profiles=(flexible_range, PriceProfile(market=market, values=[100.0])),
        ),
        Scenario(
            name="mid",
            probability=1 / 3,
            profiles=(flexible_range, PriceProfile(market=market, values=[100.0])),
        ),
        Scenario(
            name="low",
            probability=1 / 3,
            profiles=(flexible_range, PriceProfile(market=market, values=[-50.0])),
        ),
    ]

    return EnergySystem(
        portfolio=AssetPortfolio([generator, flexible_load]),
        markets=market,
        scenarios=scenarios,
        number_of_steps=1,
        timestep=timedelta(hours=1),
        objective=objective,
    )


def test_flexible_load_with_cvar_objective() -> None:
    """Test that a CVaR objective shifts a flexible load toward safer local consumption.

    Three equally-likely scenarios share one stage-fixed sell-only market
    (non-anticipative: the traded volume must be the same across scenarios).
    Prices are 100 in two scenarios and -50 in the third. The flexible load's
    value_of_consumption (30) is below the expected market price (50), so a
    pure profit-maximizer sells the maximum feasible volume into the market
    and the flexible load consumes the rest of the generator's 100 MW (50 MW).
    But because the market decision is shared across scenarios, selling more
    also means losing 50/unit in the bad scenario. A CVaR-averse optimizer
    pulls back the (shared) market volume and instead directs that capacity to
    the flexible load's unconditionally-safe, scenario-independent consumption
    value, up to its upper bound (90 MW).

    The consumption is uniquely determined by the LP in both cases (checked
    with an exact assertion). The shared market volume under CVaR sits in a
    provably flat region of the objective (any value in [0, 10] is equally
    optimal), so that comparison uses an upper bound and a strict
    less-than instead of an exact value, to avoid asserting a specific point
    in a mathematically non-unique optimum.
    """
    profit_only_results = _build_cvar_flexible_load_system(Objective(terms=(ProfitTerm(weight=1),))).optimize()

    assert profit_only_results.solver_status == "ok"
    assert profit_only_results.termination_condition == "optimal"
    assert profit_only_results.flexible_loads.consumption.to_numpy() == pytest.approx([50.0] * 3, abs=TOLERANCE)
    assert profit_only_results.markets.sell_volume.to_numpy() == pytest.approx([50.0] * 3, abs=TOLERANCE)

    cvar_results = _build_cvar_flexible_load_system(
        Objective(terms=(ProfitTerm(weight=1), CVaRTerm(weight=1, confidence_level=0.8))),
    ).optimize()

    assert cvar_results.solver_status == "ok"
    assert cvar_results.termination_condition == "optimal"
    assert cvar_results.flexible_loads.consumption.to_numpy() == pytest.approx([90.0] * 3, abs=TOLERANCE)
    assert all(value <= 10.0 + TOLERANCE for value in cvar_results.markets.sell_volume)


def test_cvar_objective_does_not_depend_on_term_order() -> None:
    """Listing the CVaR term before the profit term gives the same optimum."""
    profit = ProfitTerm(weight=1)
    cvar = CVaRTerm(weight=1, confidence_level=0.8)

    profit_first = _build_cvar_flexible_load_system(Objective(terms=(profit, cvar))).optimize()
    cvar_first = _build_cvar_flexible_load_system(Objective(terms=(cvar, profit))).optimize()

    assert profit_first.termination_condition == "optimal"
    assert cvar_first.termination_condition == "optimal"
    assert cvar_first.objective_value == pytest.approx(profit_first.objective_value, abs=TOLERANCE)


def test_multiple_flexible_loads_different_value_of_consumption() -> None:
    """The load worth more than the market price runs at its upper bound, the one worth less at its lower bound."""
    generator = Generator(name="gen1", nominal_power=300.0, variable_cost=40.0)
    flex_load_high = FlexibleLoad(name="flex_load_high", value_of_consumption=80.0)
    flex_load_low = FlexibleLoad(name="flex_load_low", value_of_consumption=40.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, flex_load_high, flex_load_low]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            profiles=(
                _constant_range(flex_load_high, 80.0, 130.0, 3),
                _constant_range(flex_load_low, 80.0, 130.0, 3),
                PriceProfile(market=market, values=[60.0, 60.0, 60.0]),
            ),
        ),
    )

    results = system.optimize()

    assert results.flexible_loads["flex_load_high"].consumption.to_numpy() == pytest.approx([130.0] * 3)
    assert results.flexible_loads["flex_load_low"].consumption.to_numpy() == pytest.approx([80.0] * 3)


def test_flexible_load_follows_time_varying_bounds() -> None:
    """The range can change from step to step, and the consumption follows whichever bound pays."""
    generator = Generator(name="gen1", nominal_power=200.0, variable_cost=50.0)
    flexible_load = FlexibleLoad(name="compressor", min_load=20.0, max_load=100.0, value_of_consumption=40.0)
    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)
    lower_bound = [20.0, 30.0, 25.0]
    upper_bound = [100.0, 60.0, 80.0]

    system = EnergySystem(
        portfolio=AssetPortfolio([generator, flexible_load]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            profiles=(
                FlexibleLoadProfile(load=flexible_load, lower_bound=lower_bound, upper_bound=upper_bound),
                PriceProfile(market=market, values=[10.0, 90.0, 10.0]),
            ),
        ),
    )

    consumption = system.optimize().flexible_loads.consumption.to_numpy()

    assert consumption == pytest.approx([upper_bound[0], lower_bound[1], upper_bound[2]], abs=TOLERANCE)
