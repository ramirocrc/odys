"""Unit tests for generator system contributions."""

from datetime import timedelta

import pytest
from linopy.testing import assert_linequal

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.model.contributions.generator import (
    generator_power_balance_terms,
    generator_profit_terms,
)
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.optimization.model.model_builder import build_model
from odys.optimization.model.sets import ModelDimension

TIMESTEP = timedelta(hours=1)
N_STEPS = 3


@pytest.fixture
def generator() -> Generator:
    return Generator(name="gen1", nominal_power=100.0, variable_cost=20.0, startup_cost=50.0)


@pytest.fixture
def milp_model(generator: Generator) -> EnergyMILPModel:
    load = FixedLoad(name="load1")
    system = EnergySystem(
        portfolio=AssetPortfolio(assets=[generator, load]),
        timestep=TIMESTEP,
        number_of_steps=N_STEPS,
        scenarios=Scenario(fixed_load_profiles={"load1": [10.0] * N_STEPS}),
    )
    return build_model(system.build_parameters())


def test_generator_power_balance_terms_match_sum(milp_model: EnergyMILPModel) -> None:
    term = generator_power_balance_terms(milp_model, milp_model.parameters)
    expected = milp_model.vars.generator_power.sum(ModelDimension.Generators)
    assert_linequal(term, expected)


def test_generator_profit_terms_match_legacy_formula(milp_model: EnergyMILPModel) -> None:
    term = generator_profit_terms(milp_model, milp_model.parameters)
    expected = -(
        milp_model.vars.generator_power * milp_model.parameters.generators.variable_cost
        + milp_model.vars.generator_startup * milp_model.parameters.generators.startup_cost
        + milp_model.vars.generator_shutdown * milp_model.parameters.generators.shutdown_cost
    ).sum([ModelDimension.Time, ModelDimension.Generators])
    assert_linequal(term, expected)
