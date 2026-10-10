"""Tests for objective function configuration."""

import pytest
from pydantic import ValidationError

from odys.domain.exceptions import OdysValidationError
from odys.domain.objective import CVaRTerm, Objective, ObjectiveTerm, ProfitTerm

PROFIT_WEIGHT = 0.7
CVAR_WEIGHT = 0.3
CVAR_CONFIDENCE_LEVEL = 0.95


class _WeightedProfitTerm(ProfitTerm):
    """A profit term subclass, to check that duplicates are counted by type, subclasses included."""


class TestProfitTerm:
    def test_requires_weight(self) -> None:
        with pytest.raises(ValidationError, match="Field required"):
            ProfitTerm.model_validate({})

    @pytest.mark.parametrize("weight", [0.5, 1.0, 2.5])
    def test_accepts_custom_weight(self, weight: float) -> None:
        term = ProfitTerm(weight=weight)
        assert term.weight == weight

    def test_accepts_zero_weight(self) -> None:
        """A weight of exactly 0 is accepted (ge=0 is inclusive)."""
        term = ProfitTerm(weight=0.0)
        assert term.weight == 0.0

    def test_rejects_negative_weight(self) -> None:
        """A negative weight is rejected: `weight` has a lower bound of 0."""
        with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
            ProfitTerm(weight=-1.0)

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
            CVaRTerm.model_validate({})

    def test_accepts_custom_weight_and_confidence_level(self) -> None:
        term = CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE_LEVEL)
        assert term.weight == CVAR_WEIGHT
        assert term.confidence_level == CVAR_CONFIDENCE_LEVEL

    def test_rejects_negative_weight(self) -> None:
        """`weight` is inherited from `ObjectiveTerm`; confirm the ge=0 bound applies here too."""
        with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
            CVaRTerm(weight=-1.0, confidence_level=CVAR_CONFIDENCE_LEVEL)

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
    def test_defaults_to_expected_profit_with_unit_weight(self) -> None:
        objective = Objective()
        assert objective.terms == (ProfitTerm(weight=1.0),)
        assert objective.term_of(CVaRTerm) is None

    def test_accepts_profit_and_cvar(self) -> None:
        profit = ProfitTerm(weight=PROFIT_WEIGHT)
        cvar = CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE_LEVEL)
        objective = Objective(terms=(profit, cvar))
        assert objective.term_of(ProfitTerm) == profit
        assert objective.term_of(CVaRTerm) == cvar

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
            terms=(
                ProfitTerm(weight=profit_weight),
                CVaRTerm(weight=cvar_weight, confidence_level=CVAR_CONFIDENCE_LEVEL),
            ),
        )
        profit = objective.term_of(ProfitTerm)
        cvar = objective.term_of(CVaRTerm)
        assert profit is not None
        assert profit.weight == profit_weight
        assert cvar is not None
        assert cvar.weight == cvar_weight

    def test_accepts_terms_in_any_order(self) -> None:
        cvar = CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE_LEVEL)
        objective = Objective(terms=(cvar, ProfitTerm(weight=PROFIT_WEIGHT)))
        assert objective.term_of(CVaRTerm) == cvar

    def test_requires_a_profit_term(self) -> None:
        with pytest.raises(OdysValidationError, match="Objective must include a ProfitTerm"):
            Objective(terms=(CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE_LEVEL),))

    def test_rejects_empty_terms(self) -> None:
        with pytest.raises(OdysValidationError, match="Objective must include a ProfitTerm"):
            Objective(terms=())

    @pytest.mark.parametrize(
        ("terms", "duplicated"),
        [
            ((ProfitTerm(weight=1.0), ProfitTerm(weight=PROFIT_WEIGHT)), "ProfitTerm"),
            (
                (
                    ProfitTerm(weight=1.0),
                    CVaRTerm(weight=CVAR_WEIGHT, confidence_level=CVAR_CONFIDENCE_LEVEL),
                    CVaRTerm(weight=CVAR_WEIGHT, confidence_level=0.5),
                ),
                "CVaRTerm",
            ),
        ],
        ids=["profit", "cvar"],
    )
    def test_rejects_more_than_one_term_of_a_type(
        self,
        terms: tuple[ProfitTerm | CVaRTerm, ...],
        duplicated: str,
    ) -> None:
        with pytest.raises(OdysValidationError, match=rf"more than one term of type: \['{duplicated}'\]"):
            Objective(terms=terms)

    def test_rejects_term_with_unknown_field(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            Objective.model_validate({"terms": ({"weight": 1.0, "bogus_field": 1},)})

    def test_rejects_a_bare_objective_term(self) -> None:
        with pytest.raises(ValidationError, match="terms"):
            Objective.model_validate({"terms": (ObjectiveTerm(weight=1.0),)})

    def test_rejects_a_subclass_alongside_its_base_term(self) -> None:
        with pytest.raises(OdysValidationError, match=r"more than one term of type: \['ProfitTerm'\]"):
            Objective(terms=(ProfitTerm(weight=1.0), _WeightedProfitTerm(weight=PROFIT_WEIGHT)))

    def test_is_frozen(self) -> None:
        objective = Objective()
        frozen_field = "terms"
        with pytest.raises(ValidationError, match="Instance is frozen"):
            setattr(objective, frozen_field, ())

    def test_rejects_unknown_field(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            Objective.model_validate({"profit": {"weight": 1.0}})

    def test_round_trips_through_model_dump(self) -> None:
        objective = Objective(
            terms=(ProfitTerm(weight=PROFIT_WEIGHT), CVaRTerm(weight=CVAR_WEIGHT, confidence_level=0.5)),
        )
        assert Objective.model_validate(objective.model_dump()) == objective
