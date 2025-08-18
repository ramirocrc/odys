# pyright: reportAttributeAccessIssue=none
import logging
from datetime import timedelta

import pytest

from optimes._math_model.algebraic_model import AlgebraicModel
from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes._math_model.model_components.constraints import EnergyModelConstraintName as ConName
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def generator1() -> PowerGenerator:
    return PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )


@pytest.fixture
def generator2() -> PowerGenerator:
    return PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )


@pytest.fixture
def battery1() -> Battery:
    return Battery(
        name="battery1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_initial=25.0,
        soc_terminal=50.0,
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    battery1: Battery,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(battery1)
    return portfolio


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [150, 200, 150]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def energy_system_sample(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
) -> ValidatedEnergySystem:
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        demand_profile=demand_profile_sample,
        timestep=timedelta(hours=1),
    )


@pytest.fixture
def algebraic_model(energy_system_sample: ValidatedEnergySystem) -> AlgebraicModel:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    return model_builder.build()


def test_constraint_power_balance(
    algebraic_model: AlgebraicModel,
    demand_profile_sample: list[float],
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.POWER_BALANCE)
    for t in time_index:
        upper_bound = constraint[t].ub
        lower_bound = constraint[t].lb
        assert lower_bound == demand_profile_sample[t] == upper_bound

        body = constraint[t].body
        generators_power = f"var_generator_power[{t},{generator1.name}] + var_generator_power[{t},{generator2.name}]"
        battery_net_power = f"var_battery_discharge[{t},{battery1.name}] - var_battery_charge[{t},{battery1.name}]"
        expected_body = f"{generators_power} + {battery_net_power}"
        assert str(body) == expected_body


def test_constraint_generator_limit(
    algebraic_model: AlgebraicModel,
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.GENERATOR_LIMIT)

    for t in time_index:
        gen1_constraint = constraint[t, generator1.name]
        assert gen1_constraint.ub == generator1.nominal_power
        # Lower bound is set by variable's domain (NonNegativeReals)
        assert gen1_constraint.lb is None
        body = gen1_constraint.body
        expected_body = f"var_generator_power[{t},{generator1.name}]"
        assert str(body) == expected_body

        gen2_constraint = constraint[t, generator2.name]
        assert gen2_constraint.ub == generator2.nominal_power
        # Lower bound is set by variable's domain (NonNegativeReals)
        assert gen2_constraint.lb is None
        body = gen2_constraint.body
        expected_body = f"var_generator_power[{t},{generator2.name}]"
        assert str(body) == expected_body


def test_constraint_battery_charge_limit(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_CHARGE_LIMIT)

    for t in time_index:
        battery_constraint = constraint[t, battery1.name]
        assert battery_constraint.ub == 0
        assert battery_constraint.lb is None

        body = battery_constraint.body
        lhs = f"var_battery_charge[{t},{battery1.name}]"
        rhs = f"{battery1.max_power}*var_battery_charge_mode[{t},{battery1.name}]"
        expected_body = f"{lhs} - {rhs}"
        assert str(body) == expected_body


def test_constraint_battery_discharge_limit(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_DISCHARGE_LIMIT)

    for t in time_index:
        battery_constraint = constraint[t, "battery1"]
        assert battery_constraint.ub == 0
        assert battery_constraint.lb is None
        # Lower bound defined by variable domain (NonNegativeReals)

        body = battery_constraint.body
        lhs = f"var_battery_discharge[{t},{battery1.name}]"
        rhs = f"{battery1.max_power}*(1 - var_battery_charge_mode[{t},{battery1.name}])"
        expected_body = f"{lhs} - {rhs}"
        assert str(body) == expected_body


def test_constraint_battery_soc_dynamics(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_SOC_DYNAMICS)

    # Test time period 0 (initial SOC)
    t0_constraint = constraint[0, battery1.name]
    assert t0_constraint.ub == 0
    assert t0_constraint.lb == 0

    body = t0_constraint.body
    lhs = f"var_battery_soc[0,{battery1.name}]"

    soc_initial = battery1.soc_initial
    eff_ch = battery1.efficiency_charging
    eff_disch = battery1.efficiency_discharging
    rhs = f"({soc_initial} + {eff_ch}*var_battery_charge[0,{battery1.name}] - {1 / eff_disch}*var_battery_discharge[0,{battery1.name}])"  # noqa: E501
    expected_body = f"{lhs} - {rhs}"
    assert str(body) == expected_body

    for t in time_index[1:]:
        t1_constraint = constraint[t, battery1.name]
        assert t1_constraint.ub == 0
        assert t1_constraint.lb == 0

        body = t1_constraint.body
        lhs = f"var_battery_soc[{t},{battery1.name}]"
        rhs = f"(var_battery_soc[{t - 1},{battery1.name}] + {eff_ch}*var_battery_charge[{t},{battery1.name}] - {1 / eff_disch}*var_battery_discharge[{t},{battery1.name}])"  # noqa: E501
        expected_body = f"{lhs} - {rhs}"
        assert str(body) == expected_body


def test_constraint_battery_soc_bounds(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_SOC_BOUNDS)

    for t in time_index:  # 3 time periods
        battery_constraint = constraint[t, battery1.name]
        assert battery_constraint.ub == battery1.capacity
        assert battery_constraint.lb is None

        body = battery_constraint.body
        expected_body = f"var_battery_soc[{t},{battery1.name}]"
        assert str(body) == expected_body


def test_constraint_battery_soc_terminal(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_SOC_TERMINAL)

    battery_constraint = constraint[battery1.name]
    assert battery_constraint.ub == battery1.soc_terminal
    assert battery_constraint.lb == battery1.soc_terminal

    body = battery_constraint.body
    expected_body = f"var_battery_soc[2,{battery1.name}]"
    assert str(body) == expected_body
