"""Integration tests: generators start from their initial state and reach their final state.

A single generator sells into a market. A price above its variable cost makes it want to run; a price of
zero makes it want to stop. Each test checks that the initial or final state overrides that incentive.
"""

from datetime import timedelta

import numpy as np
import pytest

from odys import (
    AssetPortfolio,
    Commitment,
    EnergyMarket,
    EnergySystem,
    Generator,
    GeneratorFinalState,
    GeneratorInitialState,
    OptimalDispatchResults,
    PriceProfile,
    Scenario,
)

NUMBER_OF_STEPS = 5
ONE_HOUR = timedelta(hours=1)
TWO_HOURS = timedelta(hours=2)
NOMINAL_POWER = 100.0
MIN_POWER = 20.0
VARIABLE_COST = 50.0
HIGH_PRICE = 100.0
HIGH_PRICES = [HIGH_PRICE] * NUMBER_OF_STEPS
ZERO_PRICES = [0.0] * NUMBER_OF_STEPS
RUNNING_POWER = 50.0
STARTUP_COST = 1_000.0
SHUTDOWN_COST = 300.0
RAMP = 10.0
MIN_TIME = timedelta(hours=3)
FINAL_POWER = 40.0
TOLERANCE = 1e-6

ALWAYS_ON = [1.0] * NUMBER_OF_STEPS
ALWAYS_OFF = [0.0] * NUMBER_OF_STEPS
ON_FOR_TWO_STEPS = [1.0, 1.0, 0.0, 0.0, 0.0]
ON_FOR_ONE_STEP = [1.0, 0.0, 0.0, 0.0, 0.0]
OFF_FOR_TWO_STEPS = [0.0, 0.0, 1.0, 1.0, 1.0]
OFF_AT_THE_LAST_STEP = [1.0, 1.0, 1.0, 1.0, 0.0]
RAMPED_UP_FROM_ZERO = [10.0, 20.0, 30.0, 40.0, 50.0]
RAMPED_DOWN_FROM_NOMINAL = [90.0, 80.0, 70.0, 60.0, 50.0]
OFF_UNTIL_FINAL_POWER = [0.0, 0.0, 0.0, 0.0, FINAL_POWER]
REVENUE_PER_STEP_AT_NOMINAL = (HIGH_PRICE - VARIABLE_COST) * NOMINAL_POWER

MARKET = EnergyMarket(name="market", max_trading_volume_per_step=1_000.0)


def _generator(commitment: Commitment | None = None, **parameters: float) -> Generator:
    return Generator.model_validate({
        "name": "gen",
        "nominal_power": NOMINAL_POWER,
        "variable_cost": VARIABLE_COST,
        "min_power": MIN_POWER,
        "commitment": commitment or Commitment(),
        **parameters,
    })


def _optimize(
    generator: Generator,
    prices: list[float],
    initial_state: GeneratorInitialState,
    final_conditions: tuple[GeneratorFinalState, ...] = (),
) -> OptimalDispatchResults:
    result = EnergySystem(
        portfolio=AssetPortfolio([generator]),
        markets=MARKET,
        timestep=ONE_HOUR,
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=Scenario(profiles=(PriceProfile(market=MARKET, values=prices),)),
        initial_conditions=(initial_state,),
        final_conditions=final_conditions,
    ).optimize()
    assert result.termination_condition == "optimal"
    return result


@pytest.mark.parametrize(
    ("initial_power", "startup_at_t0", "startup_cost_paid"),
    [(RUNNING_POWER, 0.0, 0.0), (0.0, 1.0, STARTUP_COST)],
    ids=["already_on", "off"],
)
def test_startup_cost_at_t0_is_paid_only_by_a_generator_that_was_off(
    initial_power: float,
    startup_at_t0: float,
    startup_cost_paid: float,
) -> None:
    generator = _generator(Commitment(startup_cost=STARTUP_COST))

    result = _optimize(generator, HIGH_PRICES, GeneratorInitialState(generator=generator, power=initial_power))

    np.testing.assert_allclose(result.generators.status.to_numpy(), ALWAYS_ON, atol=TOLERANCE)
    assert result.generators.startup.to_numpy()[0] == pytest.approx(startup_at_t0)
    expected_profit = NUMBER_OF_STEPS * REVENUE_PER_STEP_AT_NOMINAL - startup_cost_paid
    assert result.objective_value == pytest.approx(expected_profit)


def test_generator_that_was_on_pays_the_shutdown_cost_when_it_stops_at_t0() -> None:
    generator = _generator(Commitment(shutdown_cost=SHUTDOWN_COST))

    result = _optimize(generator, ZERO_PRICES, GeneratorInitialState(generator=generator, power=RUNNING_POWER))

    np.testing.assert_allclose(result.generators.status.to_numpy(), ALWAYS_OFF, atol=TOLERANCE)
    assert result.generators.shutdown.to_numpy()[0] == pytest.approx(1.0)
    assert result.objective_value == pytest.approx(-SHUTDOWN_COST)


def test_ramp_up_limit_applies_from_the_initial_power_at_t0() -> None:
    generator = _generator(min_power=0.0, ramp_up=RAMP)

    result = _optimize(generator, HIGH_PRICES, GeneratorInitialState(generator=generator, power=0.0))

    np.testing.assert_allclose(result.generators.power.to_numpy(), RAMPED_UP_FROM_ZERO, atol=TOLERANCE)


def test_ramp_down_limit_applies_from_the_initial_power_at_t0() -> None:
    generator = _generator(min_power=0.0, ramp_down=RAMP)

    result = _optimize(generator, ZERO_PRICES, GeneratorInitialState(generator=generator, power=NOMINAL_POWER))

    np.testing.assert_allclose(result.generators.power.to_numpy(), RAMPED_DOWN_FROM_NOMINAL, atol=TOLERANCE)


@pytest.mark.parametrize(
    ("time_in_state", "expected_status"),
    [(ONE_HOUR, ON_FOR_TWO_STEPS), (TWO_HOURS, ON_FOR_ONE_STEP), (MIN_TIME, ALWAYS_OFF)],
    ids=["one_of_three_hours_on", "two_of_three_hours_on", "min_up_time_met"],
)
def test_generator_on_for_less_than_its_min_up_time_stays_on_until_it_is_reached(
    time_in_state: timedelta,
    expected_status: list[float],
) -> None:
    """Running loses money at zero prices, so the generator stops as soon as its minimum up time allows."""
    generator = _generator(Commitment(min_up_time=MIN_TIME))
    initial_state = GeneratorInitialState(generator=generator, power=RUNNING_POWER, time_in_state=time_in_state)

    result = _optimize(generator, ZERO_PRICES, initial_state)

    np.testing.assert_allclose(result.generators.status.to_numpy(), expected_status, atol=TOLERANCE)


@pytest.mark.parametrize(
    ("time_in_state", "expected_status"),
    [(ONE_HOUR, OFF_FOR_TWO_STEPS), (MIN_TIME, ALWAYS_ON)],
    ids=["one_of_three_hours_off", "min_down_time_met"],
)
def test_generator_off_for_less_than_its_min_down_time_stays_off_until_it_is_reached(
    time_in_state: timedelta,
    expected_status: list[float],
) -> None:
    """Running earns money at high prices, so the generator starts as soon as its minimum down time allows."""
    generator = _generator(Commitment(min_down_time=MIN_TIME))
    initial_state = GeneratorInitialState(generator=generator, power=0.0, time_in_state=time_in_state)

    result = _optimize(generator, HIGH_PRICES, initial_state)

    np.testing.assert_allclose(result.generators.status.to_numpy(), expected_status, atol=TOLERANCE)


def test_generator_on_without_time_in_state_for_its_min_down_time_can_stop_at_t0() -> None:
    """The time in state is only needed for the minimum time of the state the generator starts in."""
    generator = _generator(Commitment(min_down_time=MIN_TIME))

    result = _optimize(generator, ZERO_PRICES, GeneratorInitialState(generator=generator, power=RUNNING_POWER))

    np.testing.assert_allclose(result.generators.status.to_numpy(), ALWAYS_OFF, atol=TOLERANCE)


@pytest.mark.parametrize("min_power", [MIN_POWER, 0.0], ids=["with_min_power", "without_min_power"])
def test_final_power_of_zero_turns_the_generator_off_at_the_last_step(min_power: float) -> None:
    generator = _generator(min_power=min_power)

    result = _optimize(
        generator,
        HIGH_PRICES,
        GeneratorInitialState(generator=generator, power=0.0),
        (GeneratorFinalState(generator=generator, power=0.0),),
    )

    np.testing.assert_allclose(result.generators.status.to_numpy(), OFF_AT_THE_LAST_STEP, atol=TOLERANCE)


def test_final_power_is_reached_at_the_last_step_against_the_price_incentive() -> None:
    generator = _generator()

    result = _optimize(
        generator,
        ZERO_PRICES,
        GeneratorInitialState(generator=generator, power=0.0),
        (GeneratorFinalState(generator=generator, power=FINAL_POWER),),
    )

    np.testing.assert_allclose(result.generators.power.to_numpy(), OFF_UNTIL_FINAL_POWER, atol=TOLERANCE)
