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
from optimes.energy_system_models.units import PowerUnit
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


def v(name: str, *indices: str | int) -> str:
    """Helper function to generate pyomo expression for an indexed variable.
    e.g. v('generator_power', 0  'gen1') will return:
    'var_generator_power[0,gen1]'

    """
    index_str = ",".join(str(index) for index in indices)
    return f"var_{name}[{index_str}]"


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
        name="batt1",
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
        power_unit=PowerUnit.MegaWatt,
    )


@pytest.fixture
def algebraic_model(energy_system_sample: ValidatedEnergySystem) -> AlgebraicModel:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    return model_builder.build()


@pytest.fixture(params=["generator1", "generator2"])
def generator(request) -> PowerGenerator:  # noqa: ANN001
    return request.getfixturevalue(request.param)


def test_constraint_power_balance(  # noqa: PLR0913
    algebraic_model: AlgebraicModel,
    demand_profile_sample: list[float],
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.POWER_BALANCE)
    for t in time_index:
        constraint_t = constraint[t]
        assert constraint_t.lb == demand_profile_sample[t] == constraint_t.ub

        body = constraint_t.body
        generators_power = f"{v('generator_power', t, generator1.name)} + {v('generator_power', t, generator2.name)}"
        battery_net_power = f"{v('battery_discharge', t, battery1.name)} - {v('battery_charge', t, battery1.name)}"
        expected_body = f"{generators_power} + {battery_net_power}"
        assert str(body) == expected_body


def test_constraint_generator_limit(
    algebraic_model: AlgebraicModel,
    generator: PowerGenerator,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.GENERATOR_LIMIT)
    i = generator.name
    for t in time_index:
        constraint_t_i = constraint[t, i]
        assert constraint_t_i.ub == generator.nominal_power
        # Lower bound is set by variable's domain (NonNegativeReals)
        assert constraint_t_i.lb is None
        expected_body = v("generator_power", t, i)
        assert str(constraint_t_i.body) == expected_body


def test_constraint_battery_charge_limit(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_CHARGE_LIMIT)
    j = battery1.name
    for t in time_index:
        constraint_t_j = constraint[t, j]
        assert constraint_t_j.ub == 0
        assert constraint_t_j.lb is None

        lhs = v("battery_charge", t, j)
        rhs = f"{battery1.max_power}*{v('battery_charge_mode', t, j)}"
        expected_body = f"{lhs} - {rhs}"
        assert str(constraint_t_j.body) == expected_body


def test_constraint_battery_discharge_limit(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_DISCHARGE_LIMIT)
    j = battery1.name
    for t in time_index:
        constraint_t_j = constraint[t, j]
        assert constraint_t_j.ub == 0
        assert constraint_t_j.lb is None
        # Lower bound defined by variable domain (NonNegativeReals)

        lhs = v("battery_discharge", t, j)
        rhs = f"{battery1.max_power}*(1 - {v('battery_charge_mode', t, j)})"
        expected_body = f"{lhs} - {rhs}"
        assert str(constraint_t_j.body) == expected_body


def test_constraint_battery_soc_dynamics(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    j = battery1.name
    constraint = algebraic_model.get_constraint(ConName.BATTERY_SOC_DYNAMICS)

    constraint_t0 = constraint[0, j]
    assert constraint_t0.ub == constraint_t0.lb == 0

    lhs = v("battery_soc", 0, j)

    soc_initial = battery1.soc_initial
    eff_ch = battery1.efficiency_charging
    eff_disch = battery1.efficiency_discharging
    rhs = f"({soc_initial} + {eff_ch}*{v('battery_charge', 0, j)} - {1 / eff_disch}*{v('battery_discharge', 0, j)})"
    expected_body = f"{lhs} - {rhs}"
    assert str(constraint_t0.body) == expected_body

    for t in time_index[1:]:
        constraint_t_j = constraint[t, j]
        assert constraint_t_j.ub == constraint_t_j.lb == 0

        body = constraint_t_j.body
        lhs = v("battery_soc", t, j)
        rhs = f"({v('battery_soc', t - 1, j)} + {eff_ch}*{v('battery_charge', t, j)} - {1 / eff_disch}*{v('battery_discharge', t, j)})"  # noqa: E501
        expected_body = f"{lhs} - {rhs}"
        assert str(body) == expected_body


def test_constraint_battery_soc_bounds(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_SOC_BOUNDS)
    j = battery1.name
    for t in time_index:  # 3 time periods
        constraint_t_j = constraint[t, j]
        assert constraint_t_j.ub == battery1.capacity
        assert constraint_t_j.lb is None

        expected_body = v("battery_soc", t, j)
        assert str(constraint_t_j.body) == expected_body


def test_constraint_battery_soc_terminal(
    algebraic_model: AlgebraicModel,
    battery1: Battery,
    time_index: list[int],
) -> None:
    constraint = algebraic_model.get_constraint(ConName.BATTERY_SOC_TERMINAL)
    j = battery1.name
    constraint_j = constraint[j]
    assert constraint_j.ub == battery1.soc_terminal
    assert constraint_j.lb == battery1.soc_terminal

    body = constraint_j.body
    expected_body = v("battery_soc", time_index[-1], j)
    assert str(body) == expected_body
