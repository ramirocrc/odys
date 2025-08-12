import logging
from datetime import timedelta

import pytest

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes._math_model.model_components.parameters import EnergyModelParameterName
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def asset_portfolio_sample() -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(
        PowerGenerator(
            name="gen1",
            nominal_power=100.0,
            variable_cost=20.0,
        ),
    )
    portfolio.add_asset(
        PowerGenerator(
            name="gen2",
            nominal_power=150.0,
            variable_cost=25.0,
        ),
    )
    portfolio.add_asset(
        Battery(
            name="battery1",
            max_power=200.0,
            capacity=100.0,
            efficiency_charging=1,
            efficiency_discharging=1,
            soc_initial=100.0,
            soc_terminal=50.0,
        ),
    )
    return portfolio


@pytest.fixture
def energy_system_sample(asset_portfolio_sample: AssetPortfolio) -> ValidatedEnergySystem:
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        demand_profile=[150, 200, 150],
        timestep=timedelta(hours=1),
    )


def test_model_build_components(energy_system_sample: ValidatedEnergySystem) -> None:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    algebraic_model = model_builder.build()
    pyomo_model = algebraic_model.pyomo_model
    # Sets
    assert hasattr(pyomo_model, "time")
    assert hasattr(pyomo_model, "generators")
    assert hasattr(pyomo_model, "batteries")

    # Parameters
    assert hasattr(pyomo_model, "param_generator_nominal_power")
    assert hasattr(pyomo_model, "param_generator_variable_cost")
    assert hasattr(pyomo_model, "param_battery_max_power")
    assert hasattr(pyomo_model, "param_battery_capacity")
    assert hasattr(pyomo_model, "param_demand")
    assert hasattr(pyomo_model, "param_scenario_timestep")

    # Variables
    assert hasattr(pyomo_model, "var_generator_power")
    assert hasattr(pyomo_model, "var_battery_charge")
    assert hasattr(pyomo_model, "var_battery_discharge")
    assert hasattr(pyomo_model, "var_battery_soc")
    assert hasattr(pyomo_model, "var_battery_charge_mode")

    # Constraints
    assert hasattr(pyomo_model, "const_power_balance")
    assert hasattr(pyomo_model, "const_generator_limit")
    assert hasattr(pyomo_model, "const_battery_charge_limit")
    assert hasattr(pyomo_model, "const_battery_discharge_limit")
    assert hasattr(pyomo_model, "const_battery_soc_dynamics")
    assert hasattr(pyomo_model, "const_battery_soc_bounds")
    assert hasattr(pyomo_model, "const_battery_soc_terminal")

    # Objective
    assert hasattr(pyomo_model, "obj_minimize_operational_cost")


@pytest.mark.parametrize(
    ("param_name", "expected_index_value_pairs"),
    [
        (EnergyModelParameterName.BATTERY_CAPACITY, {"battery1": 100.0}),
        (EnergyModelParameterName.BATTERY_EFFICIENCY_CHARGE, {"battery1": 1.0}),
        (EnergyModelParameterName.BATTERY_EFFICIENCY_DISCHARGE, {"battery1": 1.0}),
        (EnergyModelParameterName.BATTERY_MAX_POWER, {"battery1": 200.0}),
        (EnergyModelParameterName.BATTERY_SOC_INITIAL, {"battery1": 100.0}),
        (EnergyModelParameterName.BATTERY_SOC_TERMINAL, {"battery1": 50.0}),
        (EnergyModelParameterName.DEMAND, {0: 150.0, 1: 200.0, 2: 150.0}),
        (EnergyModelParameterName.GENERATOR_NOMINAL_POWER, {"gen1": 100.0, "gen2": 150.0}),
        (EnergyModelParameterName.GENERATOR_VARIABLE_COST, {"gen1": 20.0, "gen2": 25.0}),
        (EnergyModelParameterName.SCENARIO_TIMESTEP, {None: timedelta(hours=1)}),
    ],
)
def test_set_and_parameter_values(
    energy_system_sample: ValidatedEnergySystem,
    param_name: EnergyModelParameterName,
    expected_index_value_pairs: dict[str, float | str],
) -> None:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    algebraic_model = model_builder.build()

    index_value_pairs = algebraic_model.get_param(param_name).extract_values()
    assert index_value_pairs == expected_index_value_pairs, (
        f"Expected {expected_index_value_pairs}, but got {index_value_pairs}"
    )


def test_model_already_built(energy_system_sample: ValidatedEnergySystem) -> None:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    model_builder.build()
    with pytest.raises(AttributeError, match="Model has already been built."):
        model_builder.build()


def test_only_generators() -> None:
    pass


def test_only_batteries() -> None:
    pass
