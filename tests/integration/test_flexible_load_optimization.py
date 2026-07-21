"""Integration test for flexible load optimization."""

from datetime import timedelta

from odys import (
    AssetPortfolio,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    FlexibleLoad,
    Generator,
    Scenario,
    StochasticScenario,
    Storage,
)

MAX_DECREASE = 30.0
MAX_INCREASE = 50.0
TOLERANCE = 1e-5
TWO_FLEXIBLE_LOADS = 2
SIX_ENTRIES = 6


def test_flexible_load_optimization_decrease() -> None:
    """Test that flexible load decreases when value_of_consumption < marginal supply cost."""
    # Generator with variable cost = 50 $/MWh
    generator = Generator(
        name="gen1",
        nominal_power=200.0,
        variable_cost=50.0,
    )

    # Flexible load with value of consumption = 30 $/MWh
    # Marginal supply cost is 50 $/MWh (generator variable cost)
    # Since voc (30) < var_cost (50), optimizer should decrease load
    flexible_load = FlexibleLoad(
        name="flex_load",
        max_increase=50.0,
        max_decrease=30.0,
        value_of_consumption=30.0,
    )

    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    portfolio = AssetPortfolio([generator, flexible_load])

    # Market price = 80 $/MWh (higher than generator cost, so generator is marginal)
    # Optimizer should decrease load by max_decrease (30 MW)
    system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            flexible_load_base_profiles={"flex_load": [100.0, 100.0, 100.0]},
            market_prices={"market1": [80.0, 80.0, 80.0]},
        ),
    )

    results = system.optimize()

    # Use the new flexible_loads API
    flex_dispatch = results.flexible_loads
    load_adjustment = flex_dispatch.load_adjustment
    actual_load = flex_dispatch.actual_load

    # Exact value check:
    # - voc (30) < marginal cost (50), so optimizer decreases load
    # - Decreasing load saves 50 - 30 = 20 $/MWh
    # - Maximum savings at max_decrease (30 MW)
    # - Expected: load_adjustment = -30.0 for all timesteps
    assert abs(load_adjustment.sum().item() - (-30.0 * 3)) < TOLERANCE

    # Check that adjustment is within bounds
    assert load_adjustment.min() >= -MAX_DECREASE, "Load decrease should not exceed max_decrease"
    assert load_adjustment.max() <= MAX_INCREASE, "Load increase should not exceed max_increase"

    # Check actual load: base (100) + adjustment (-30) = 70
    assert abs(actual_load.mean() - 70.0) < TOLERANCE


def test_flexible_load_optimization_increase() -> None:
    """Test that flexible load increases when value_of_consumption > marginal supply cost."""
    # Generator with low variable cost
    generator = Generator(
        name="gen1",
        nominal_power=200.0,
        variable_cost=10.0,
    )

    # Flexible load with value of consumption = 100 $/MWh
    # Marginal supply cost is 10 $/MWh (generator variable cost)
    # Since voc (100) > var_cost (10), optimizer should increase load
    flexible_load = FlexibleLoad(
        name="flex_load",
        max_increase=50.0,
        max_decrease=30.0,
        value_of_consumption=100.0,
    )

    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    portfolio = AssetPortfolio([generator, flexible_load])

    # Market price = 20 $/MWh (higher than generator cost, so generator is marginal)
    # Optimizer should increase load by max_increase (50 MW)
    system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            flexible_load_base_profiles={"flex_load": [100.0, 100.0, 100.0]},
            market_prices={"market1": [20.0, 20.0, 20.0]},
        ),
    )

    results = system.optimize()

    # Use the new flexible_loads API
    flex_dispatch = results.flexible_loads
    load_adjustment = flex_dispatch.load_adjustment
    actual_load = flex_dispatch.actual_load

    # Exact value check:
    # - voc (100) > marginal cost (10), so optimizer increases load
    # - Increasing load gains 100 - 10 = 90 $/MWh
    # - Maximum gain at max_increase (50 MW)
    # - Expected: load_adjustment = +50.0 for all timesteps
    assert abs(load_adjustment.sum().item() - (50.0 * 3)) < TOLERANCE

    # Check that adjustment is within bounds
    assert load_adjustment.min() >= -MAX_DECREASE, "Load decrease should not exceed max_decrease"
    assert load_adjustment.max() <= MAX_INCREASE, "Load increase should not exceed max_increase"

    # Check actual load: base (100) + adjustment (50) = 150
    assert abs(actual_load.mean() - 150.0) < TOLERANCE


def test_flexible_load_with_fixed_load() -> None:
    """Test system with both fixed and flexible loads."""
    generator = Generator(
        name="gen1",
        nominal_power=300.0,
        variable_cost=30.0,
    )

    fixed_load = FixedLoad(name="fixed_load")
    flexible_load = FlexibleLoad(
        name="flex_load",
        max_increase=40.0,
        max_decrease=20.0,
        value_of_consumption=50.0,
    )

    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)

    portfolio = AssetPortfolio([generator, fixed_load, flexible_load])

    # Market price = 20 $/MWh (below generator cost of 30 $/MWh)
    # Marginal supply cost = 30 $/MWh (generator is the marginal source)
    # value_of_consumption = 50 $/MWh > marginal cost (30), so optimizer should increase flexible load
    system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=2,
        scenarios=Scenario(
            fixed_load_profiles={"fixed_load": [100.0, 100.0]},
            flexible_load_base_profiles={"flex_load": [80.0, 80.0]},
            market_prices={"market1": [20.0, 20.0]},
        ),
    )

    results = system.optimize()

    # Use the new flexible_loads API
    flex_dispatch = results.flexible_loads
    load_adjustment = flex_dispatch.load_adjustment
    actual_load = flex_dispatch.actual_load

    # Exact value check:
    # - voc (50) > marginal cost (30), so optimizer increases load
    # - Increasing load gains 50 - 30 = 20 $/MWh
    # - Maximum gain at max_increase (40 MW)
    # - Expected: load_adjustment = +40.0 for all timesteps
    assert abs(load_adjustment.sum().item() - (40.0 * 2)) < TOLERANCE

    # Check actual load: base (80) + adjustment (40) = 120
    assert abs(actual_load.mean() - 120.0) < TOLERANCE

    # Check that power balance is satisfied
    # gen_power + market_buy - market_sell = fixed_load + flex_load_base + load_adjustment
    solution = results.to_dataset()
    gen_power = solution["generator_power"]
    market_buy = solution["market_buy_volume"]
    market_sell = solution["market_sell_volume"]

    for t in range(2):
        total_load = 100.0 + 80.0 + load_adjustment.iloc[t]
        gen_at_t = gen_power.isel(time=t).values
        market_buy_at_t = market_buy.isel(time=t).values
        market_sell_at_t = market_sell.isel(time=t).values
        supply = gen_at_t + market_buy_at_t - market_sell_at_t
        assert abs(supply - total_load) < TOLERANCE, f"Power balance not satisfied at time {t}"


def test_multiple_flexible_loads() -> None:
    """Test system with two flexible loads in one portfolio."""
    generator = Generator(
        name="gen1",
        nominal_power=300.0,
        variable_cost=40.0,
    )

    flex_load_1 = FlexibleLoad(
        name="flex_load_1",
        max_increase=30.0,
        max_decrease=20.0,
        value_of_consumption=60.0,
    )
    flex_load_2 = FlexibleLoad(
        name="flex_load_2",
        max_increase=25.0,
        max_decrease=15.0,
        value_of_consumption=20.0,
    )

    market = EnergyMarket(name="market1", max_trading_volume_per_step=1000.0)
    portfolio = AssetPortfolio([generator, flex_load_1, flex_load_2])

    system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=Scenario(
            flexible_load_base_profiles={
                "flex_load_1": [100.0, 100.0, 100.0],
                "flex_load_2": [80.0, 80.0, 80.0],
            },
            market_prices={"market1": [50.0, 50.0, 50.0]},
        ),
    )

    results = system.optimize()

    assert len(results.flexible_loads) == TWO_FLEXIBLE_LOADS
    assert "flex_load_1" in results.flexible_loads
    assert "flex_load_2" in results.flexible_loads

    flex_1_adj = results.flexible_loads["flex_load_1"].load_adjustment
    assert flex_1_adj.sum().item() > 0

    flex_2_adj = results.flexible_loads["flex_load_2"].load_adjustment
    assert flex_2_adj.sum().item() < 0


def test_flexible_load_with_storage() -> None:
    """Test flexible loads work with storage assets."""
    generator = Generator(
        name="gen1",
        nominal_power=150.0,
        variable_cost=50.0,
    )
    battery = Storage(
        name="battery",
        capacity=100.0,
        max_power=50.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.9,
        soc_start=0.5,
        soc_end=0.5,
    )
    flexible_load = FlexibleLoad(
        name="flex_load",
        max_increase=30.0,
        max_decrease=20.0,
        value_of_consumption=70.0,
    )

    market = EnergyMarket(name="market1", max_trading_volume_per_step=500.0)
    portfolio = AssetPortfolio([generator, battery, flexible_load])

    system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=4,
        scenarios=Scenario(
            flexible_load_base_profiles={"flex_load": [100.0, 100.0, 100.0, 100.0]},
            market_prices={"market1": [60.0, 60.0, 60.0, 60.0]},
        ),
    )

    results = system.optimize()

    flex_dispatch = results.flexible_loads
    assert flex_dispatch.load_adjustment.sum().item() > 0

    storage_dispatch = results.storages
    assert len(storage_dispatch.soc) > 0

    solution = results.to_dataset()
    gen_power = solution["generator_power"]
    storage_out = solution["storage_power_out"]
    storage_in = solution["storage_power_in"]
    market_buy = solution["market_buy_volume"]
    market_sell = solution["market_sell_volume"]

    for t in range(4):
        flex_base = 100.0
        flex_adj = flex_dispatch.load_adjustment.iloc[t]
        total_load = flex_base + flex_adj
        supply = (
            gen_power.isel(time=t).values
            + storage_out.isel(time=t).values
            - storage_in.isel(time=t).values
            + market_buy.isel(time=t).values
            - market_sell.isel(time=t).values
        )
        assert abs(supply - total_load) < TOLERANCE, f"Power balance not satisfied at time {t}"


def test_flexible_load_stochastic_scenarios() -> None:
    """Test flexible loads with two StochasticScenarios having different base profiles."""
    generator = Generator(
        name="gen1",
        nominal_power=200.0,
        variable_cost=30.0,
    )
    flexible_load = FlexibleLoad(
        name="flex_load",
        max_increase=40.0,
        max_decrease=25.0,
        value_of_consumption=50.0,
    )

    market = EnergyMarket(name="market1", max_trading_volume_per_step=500.0)
    portfolio = AssetPortfolio([generator, flexible_load])

    scenarios = [
        StochasticScenario(
            name="high_demand",
            probability=0.6,
            flexible_load_base_profiles={"flex_load": [120.0, 120.0, 120.0]},
            market_prices={"market1": [40.0, 40.0, 40.0]},
        ),
        StochasticScenario(
            name="low_demand",
            probability=0.4,
            flexible_load_base_profiles={"flex_load": [80.0, 80.0, 80.0]},
            market_prices={"market1": [40.0, 40.0, 40.0]},
        ),
    ]

    system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=3,
        scenarios=scenarios,
    )

    results = system.optimize()

    assert results.solver_status == "ok"
    assert results.termination_condition == "optimal"

    flex_dispatch = results.flexible_loads
    load_adjustment = flex_dispatch.load_adjustment

    assert len(load_adjustment) == SIX_ENTRIES

    assert load_adjustment.min() >= -MAX_DECREASE
    assert load_adjustment.max() <= MAX_INCREASE
