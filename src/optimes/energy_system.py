"""Model optimizer for energy system optimization.

This module provides the EnergySystemOptimizer class for solving
energy system optimization problems.
"""

from collections.abc import Mapping, Sequence
from datetime import timedelta

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.scenarios import Scenario
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem
from optimes.optimization.optimization_results import OptimizationResults
from optimes.solvers.highs_solver import optimize_algebraic_model
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergySystem:
    """Energy system configuration and optimization orchestrator.

    This class provides a high-level interface for configuring and optimizing
    energy systems. It handles system validation, model building, and
    optimization execution through external solvers.
    """

    def __init__(  # noqa: PLR0913
        self,
        portfolio: AssetPortfolio,
        demand_profile: Sequence[float],
        timestep: timedelta,
        power_unit: str,
        available_capacity_profiles: Mapping[str, Sequence[float]] | None = None,
        scenarios: Sequence[Scenario] | None = None,
    ) -> None:
        """Initialize the energy system configuration and optimizer.

        Args:
            portfolio: The portfolio of energy assets (generators, batteries, etc.).
            demand_profile: Sequence of power demand values for each time period.
            timestep: Duration of each time period.
            power_unit: Unit used for power quantities ('W', 'kW', or 'MW').
            available_capacity_profiles: Optional dict mapping generator names to
            scenarios: Sequence of scenarios. Probabilities must add up to 1.
                their available capacity profiles over time.

        """
        self._validated_model = ValidatedEnergySystem(
            portfolio=portfolio,
            demand_profile=demand_profile,
            timestep=timestep,
            power_unit=power_unit,  # pyright: ignore reportArgumentType
            available_capacity_profiles=available_capacity_profiles,
            scenarios=scenarios,
        )

    def optimize(
        self,
    ) -> OptimizationResults:
        """Optimize the energy system.

        This method solves the pre-built algebraic model using HiGHS solver.
        The model is built during optimization from the energy system configuration.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        model_builder = EnergyAlgebraicModelBuilder(
            energy_system_parameters=self._validated_model.parameters,
        )
        linopy_model = model_builder.build()
        return optimize_algebraic_model(linopy_model)
