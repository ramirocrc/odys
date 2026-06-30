"""Tests for scenario definitions and stochastic scenario validation."""

import pytest
from pydantic import ValidationError

from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import (
    Scenario,
    StochasticScenario,
    validate_sequence_of_stochastic_scenarios,
)

LOAD_PROFILE = [80.0, 120.0, 90.0]
MARKET_PRICES = [10.0, 20.0, 30.0]
CAPACITY_PROFILE = [100.0, 100.0, 100.0]


class TestScenario:
    def test_defaults_to_no_profiles(self) -> None:
        scenario = Scenario()
        assert scenario.available_capacity_profiles is None
        assert scenario.load_profiles is None
        assert scenario.market_prices is None

    def test_accepts_all_profiles(self) -> None:
        scenario = Scenario(
            available_capacity_profiles={"gen1": CAPACITY_PROFILE},
            load_profiles={"load1": LOAD_PROFILE},
            market_prices={"market1": MARKET_PRICES},
        )
        assert scenario.available_capacity_profiles == {"gen1": CAPACITY_PROFILE}
        assert scenario.load_profiles == {"load1": LOAD_PROFILE}
        assert scenario.market_prices == {"market1": MARKET_PRICES}

    def test_is_frozen(self) -> None:
        scenario = Scenario()
        frozen_field = "load_profiles"
        with pytest.raises(ValidationError, match="Instance is frozen"):
            setattr(scenario, frozen_field, {"load1": LOAD_PROFILE})

    def test_rejects_unknown_field(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            Scenario.model_validate({"bogus_field": 1})


class TestStochasticScenario:
    def test_inherits_scenario_profiles(self) -> None:
        scenario = StochasticScenario(
            name="s1",
            probability=1.0,
            load_profiles={"load1": LOAD_PROFILE},
        )
        assert scenario.name == "s1"
        assert scenario.probability == 1.0
        assert scenario.load_profiles == {"load1": LOAD_PROFILE}

    @pytest.mark.parametrize("probability", [0.0, 0.5, 1.0])
    def test_accepts_probability_within_bounds(self, probability: float) -> None:
        scenario = StochasticScenario(name="s1", probability=probability)
        assert scenario.probability == probability

    @pytest.mark.parametrize(
        ("probability", "expected_match"),
        [
            (-0.1, "Input should be greater than or equal to 0"),
            (1.1, "Input should be less than or equal to 1"),
        ],
    )
    def test_rejects_probability_out_of_bounds(self, probability: float, expected_match: str) -> None:
        with pytest.raises(ValidationError, match=expected_match):
            StochasticScenario(name="s1", probability=probability)


class TestValidateSequenceOfStochasticScenarios:
    def test_single_scenario_with_probability_one(self) -> None:
        scenarios = (StochasticScenario(name="s1", probability=1.0),)
        validate_sequence_of_stochastic_scenarios(scenarios)

    def test_multiple_scenarios_summing_to_one(self) -> None:
        scenarios = (
            StochasticScenario(name="s1", probability=0.5),
            StochasticScenario(name="s2", probability=0.3),
            StochasticScenario(name="s3", probability=0.2),
        )
        validate_sequence_of_stochastic_scenarios(scenarios)

    def test_empty_sequence_raises(self) -> None:
        with pytest.raises(OdysValidationError, match=r"got sum = 0 instead"):
            validate_sequence_of_stochastic_scenarios(())

    @pytest.mark.parametrize(
        ("probabilities", "expected_sum"),
        [
            ((0.3, 0.3), 0.6),
            ((0.6, 0.6), 1.2),
        ],
    )
    def test_probabilities_not_summing_to_one_raises(
        self,
        probabilities: tuple[float, float],
        expected_sum: float,
    ) -> None:
        scenarios = tuple(
            StochasticScenario(name=f"s{i}", probability=probability) for i, probability in enumerate(probabilities)
        )
        with pytest.raises(OdysValidationError, match=rf"got sum = {expected_sum} instead"):
            validate_sequence_of_stochastic_scenarios(scenarios)

    def test_duplicate_names_raise_even_when_probabilities_sum_to_one(self) -> None:
        scenarios = (
            StochasticScenario(name="dup", probability=0.5),
            StochasticScenario(name="dup", probability=0.5),
        )
        with pytest.raises(OdysValidationError, match="must have a unique name"):
            validate_sequence_of_stochastic_scenarios(scenarios)

    def test_sum_check_runs_before_duplicate_name_check(self) -> None:
        """When both checks would fail, the probability-sum error is the one raised."""
        scenarios = (
            StochasticScenario(name="dup", probability=0.3),
            StochasticScenario(name="dup", probability=0.3),
        )
        with pytest.raises(OdysValidationError, match=r"got sum = 0\.6 instead"):
            validate_sequence_of_stochastic_scenarios(scenarios)
