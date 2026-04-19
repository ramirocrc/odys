"""Frozen snapshot of solved model data for result extraction."""

from collections.abc import Hashable
from types import MappingProxyType

import pandas as pd
import xarray as xr
from linopy.constants import SolverStatus, TerminationCondition

from odys.domain.exceptions import OdysNoResultsError, OdysSolverError
from odys.domain.objective import CVaRTerm
from odys.optimization.model.sets import ModelDimension
from odys.optimization.model.variables import ModelVariable
from odys.results.dispatch import GeneratorDispatch, LoadDispatch, MarketDispatch, StorageDispatch


class SolvedModelData:
    """Frozen snapshot of data extracted from a solved EnergyMILPModel.

    Captures only what OptimizationResults needs, allowing the full
    linopy model to be garbage-collected after solving.
    """

    def __init__(  # noqa: PLR0913
        self,
        solver_status: SolverStatus,
        termination_condition: TerminationCondition,
        solution: xr.Dataset,
        variable_names: frozenset[Hashable],
        *,
        has_generators: bool,
        has_storages: bool,
        has_markets: bool,
        has_loads: bool,
        cvar_term: CVaRTerm | None,
        scenario_probabilities: pd.Series | None,
        load_profiles: xr.DataArray | None,
    ) -> None:
        """Initialize SolvedModelData."""
        self._solver_status = solver_status
        self._termination_condition = termination_condition
        if "scenario" in solution.coords and len(solution.coords["scenario"]) == 1:
            solution = solution.squeeze("scenario", drop=True)
        self._solution = solution
        self._variable_names = variable_names
        self._has_generators = has_generators
        self._has_storages = has_storages
        self._has_markets = has_markets
        self._has_loads = has_loads
        self._cvar_term = cvar_term
        self._scenario_probabilities = scenario_probabilities
        self._load_profiles = load_profiles

    @property
    def solver_status(self) -> str:
        """Get the solver status."""
        return self._solver_status.value

    @property
    def termination_condition(self) -> str:
        """Get the termination condition."""
        return self._termination_condition.value

    @property
    def solution(self) -> xr.Dataset:
        """Get the raw solution dataset."""
        self._validate_terminated_successfully()
        return self._solution

    def _validate_terminated_successfully(self) -> None:
        if self._solver_status != SolverStatus.ok:
            msg = f"No solution available. Optimization Termination Condition: {self._termination_condition}."
            raise OdysSolverError(msg)

    @property
    def generators(self) -> MappingProxyType[str, GeneratorDispatch]:
        """Get generator dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_generators:
            msg = "This model does not contain generator results"
            raise OdysNoResultsError(msg)

        result: dict[str, GeneratorDispatch] = {}
        sol = self._solution
        for generator_name in sol.coords[ModelDimension.Generators].to_numpy():
            result[generator_name] = GeneratorDispatch(
                power=sol[ModelVariable.GENERATOR_POWER.var_name].sel(generator=generator_name, drop=True),
                status=sol[ModelVariable.GENERATOR_STATUS.var_name].sel(generator=generator_name, drop=True),
                startup=sol[ModelVariable.GENERATOR_STARTUP.var_name].sel(generator=generator_name, drop=True),
                shutdown=sol[ModelVariable.GENERATOR_SHUTDOWN.var_name].sel(generator=generator_name, drop=True),
            )
        return MappingProxyType(result)

    @property
    def storages(self) -> MappingProxyType[str, StorageDispatch]:
        """Get storage dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_storages:
            msg = "This model does not contain storage results"
            raise OdysNoResultsError(msg)

        result: dict[str, StorageDispatch] = {}
        sol = self._solution
        for storage_name in sol.coords[ModelDimension.Storages].to_numpy():
            result[storage_name] = StorageDispatch(
                net_power=sol[ModelVariable.STORAGE_POWER_NET.var_name].sel(storage=storage_name, drop=True),
                soc=sol[ModelVariable.STORAGE_SOC.var_name].sel(storage=storage_name, drop=True),
                charge_mode=sol[ModelVariable.STORAGE_CHARGE_MODE.var_name].sel(storage=storage_name, drop=True),
            )
        return MappingProxyType(result)

    @property
    def loads(self) -> MappingProxyType[str, LoadDispatch]:
        """Get load dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_loads:
            msg = "This model does not contain load results"
            raise OdysNoResultsError(msg)

        result: dict[str, LoadDispatch] = {}
        for load_name in self._load_profiles.coords[ModelDimension.Loads].to_numpy():
            result[load_name] = LoadDispatch(load=self._load_profiles.sel(load=load_name))
        return MappingProxyType(result)

    @property
    def markets(self) -> MappingProxyType[str, MarketDispatch]:
        """Get market dispatch results."""
        self._validate_terminated_successfully()
        if not self._has_markets:
            msg = "This model does not contain market results"
            raise OdysNoResultsError(msg)

        result: dict[str, MarketDispatch] = {}
        sol = self._solution
        for market_name in sol.coords[ModelDimension.Markets].to_numpy():
            result[market_name] = MarketDispatch(
                sell_volume=sol[ModelVariable.MARKET_SELL.var_name].sel(market=market_name, drop=True),
                buy_volume=sol[ModelVariable.MARKET_BUY.var_name].sel(market=market_name, drop=True),
            )
        return MappingProxyType(result)
