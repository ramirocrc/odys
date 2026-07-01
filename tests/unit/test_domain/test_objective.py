"""Tests for objective function configuration."""

import pytest
from pydantic import ValidationError

from odys.domain.objective import CVaRTerm, Objective, ProfitTerm

PROFIT_WEIGHT = 0.7
CVAR_WEIGHT = 0.3
CVAR_CONFIDENCE_LEVEL = 0.95


class TestProfitTerm:
    def test_requires_weight(self) -> None:
        with pytest.raises(ValidationError, match="Field required"):
            ProfitTerm()  # type: ignore[call-arg]

    @pytest.mark.parametrize("weight", [0.5, 1.0, 2.5])
    def test_accepts_custom_weight(self, weight: float) -> None:
        term = ProfitTerm(weight=weight)
        assert term.weight == weight

    @pytest.mark.parametrize("weight", [-1.0, 0.0])
    def test_accepts_non_positive_weight(self, weight: float) -> None:
        """`weight` carries no lower-bound constraint, so non-positive values are accepted.

        The issue this test file was written for asked for negative and zero
        weights to be rejected, but `ObjectiveTerm.weight` has no `Field`
        constraint on it in the source.
        """
        term = ProfitTerm(weight=weight)
        assert term.weight == weight

    def test_is_frozen(self) -> None:
        term = ProfitTerm(weight=1.0)
        frozen_field = "weight"
        with pytest.raises(ValidationError, match="Instance is frozen"):
            setattr(term, frozen_field, 2.0)

    def test_rejects_unknown_field(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            ProfitTerm.model_validate({"weight": 1.0, "bogus_field": 1})


class TestCVaRTerm:
    def test_requires_weight_and_confidence_level(self) -> None:
        with pytest.raises(ValidationError, match="Field required"):
            CVaRTerm()  # type: ignore[call-arg]

    def test_accepts_custom_weight_and_confidence_level(self) -> None:
        term = CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE_LEVEL)
        assert term.weight == CVAR_WEIGHT
        assert term.confidence_level == CVAR_CONFIDENCE_LEVEL

    @pytest.mark.parametrize("confidence_level", [0.01, 0.5, 0.99])
    def test_accepts_confidence_level_within_bounds(self, confidence_level: float) -> None:
        term = CVaRTerm(weight=1.0, confidence_level=confidence_level)
        assert term.confidence_level == confidence_level

    @pytest.mark.parametrize(
        ("confidence_level", "expected_match"),
        [
            (0.0, "Input should be greater than 0"),
            (1.0, "Input should be less than 1"),
        ],
    )
    def test_rejects_confidence_level_at_boundaries(self, confidence_level: float, expected_match: str) -> None:
        """`confidence_level` uses exclusive bounds (`gt=0, lt=1`), so 0 and 1 themselves are invalid."""
        with pytest.raises(ValidationError, match=expected_match):
            CVaRTerm(weight=1.0, confidence_level=confidence_level)

    @pytest.mark.parametrize(
        ("confidence_level", "expected_match"),
        [
            (-0.1, "Input should be greater than 0"),
            (1.1, "Input should be less than 1"),
        ],
    )
    def test_rejects_confidence_level_out_of_bounds(self, confidence_level: float, expected_match: str) -> None:
        with pytest.raises(ValidationError, match=expected_match):
            CVaRTerm(weight=1.0, confidence_level=confidence_level)


class TestObjective:
    def test_requires_profit(self) -> None:
        with pytest.raises(ValidationError, match="Field required"):
            Objective()  # type: ignore[call-arg]

    def test_profit_only_defaults_cvar_to_none(self) -> None:
        objective = Objective(profit=ProfitTerm(weight=1.0))
        assert objective.cvar is None

    def test_accepts_profit_and_cvar(self) -> None:
        objective = Objective(
            profit=ProfitTerm(weight=PROFIT_WEIGHT),
            cvar=CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE_LEVEL),
        )
        assert objective.profit.weight == PROFIT_WEIGHT
        assert objective.cvar is not None
        assert objective.cvar.weight == CVAR_WEIGHT
        assert objective.cvar.confidence_level == CVAR_CONFIDENCE_LEVEL

    @pytest.mark.parametrize(
        ("profit_weight", "cvar_weight"),
        [
            (1.0, 0.0),
            (0.5, 0.5),
            (0.2, 0.8),
        ],
    )
    def test_accepts_custom_weights_for_both_terms(self, profit_weight: float, cvar_weight: float) -> None:
        objective = Objective(
            profit=ProfitTerm(weight=profit_weight),
            cvar=CVaRTerm(weight=cvar_weight, confidence_level=CVAR_CONFIDENCE_LEVEL),
        )
        assert objective.profit.weight == profit_weight
        assert objective.cvar is not None
        assert objective.cvar.weight == cvar_weight
