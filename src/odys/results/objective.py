"""Objective and scenario result types."""


class ObjectiveResult:
    """Objective function results (expected profit, CVaR)."""

    __slots__ = ("_cvar", "_expected_profit", "_var_threshold")

    def __init__(self, expected_profit: float, cvar: float | None = None, var_threshold: float | None = None) -> None:
        """Initialize objective result."""
        self._expected_profit = expected_profit
        self._cvar = cvar
        self._var_threshold = var_threshold

    @property
    def expected_profit(self) -> float:
        """Expected profit across all scenarios."""
        return self._expected_profit

    @property
    def cvar(self) -> float | None:
        """CVaR value (conditional value at risk)."""
        return self._cvar

    @property
    def var_threshold(self) -> float | None:
        """VaR threshold (eta)."""
        return self._var_threshold


class ScenarioResult:
    """Per-scenario results (profit, dispatch)."""

    __slots__ = (
        "_generator_dispatch",
        "_market_revenue",
        "_name",
        "_profit",
        "_storage_dispatch",
    )

    def __init__(
        self,
        name: str,
        profit: float,
        generator_dispatch: dict,
        storage_dispatch: dict,
        market_revenue: dict,
    ) -> None:
        """Initialize scenario result."""
        self._name = name
        self._profit = profit
        self._generator_dispatch = generator_dispatch
        self._storage_dispatch = storage_dispatch
        self._market_revenue = market_revenue

    @property
    def name(self) -> str:
        """Scenario name."""
        return self._name

    @property
    def profit(self) -> float:
        """Total profit for this scenario."""
        return self._profit

    def generator(self, asset_name: str) -> object:
        """Generator dispatch for a specific asset."""
        return self._generator_dispatch[asset_name]

    def storage(self, asset_name: str) -> object:
        """Storage dispatch for a specific asset."""
        return self._storage_dispatch[asset_name]

    def market(self, market_name: str) -> float:
        """Market revenue for a specific market."""
        return self._market_revenue[market_name]
