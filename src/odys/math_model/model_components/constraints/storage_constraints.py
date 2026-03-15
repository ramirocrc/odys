"""Storage-related constraints for the optimization model."""

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint
from odys.math_model.model_components.sets import ModelDimension


class StorageConstraints:
    """Builds constraints for storage charge/discharge, SOC dynamics, and power limits."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model containing storage variables and parameters."""
        self.model = milp_model
        self.params = milp_model.parameters.storages

    def _validate_storage_parameters_exist(self) -> None:
        if self.params is None:
            msg = "No storage parameters specified."
            raise ValueError(msg)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        """Return all storage constraints, or an empty tuple if no storages exist."""
        if self.params is None:
            return ()
        return (
            self._get_storage_max_charge_constraint(),
            self._get_storage_max_discharge_constraint(),
            self._get_storage_soc_dynamics_constraint(),
            self._get_storage_soc_start_constraint(),
            self._get_storage_soc_end_constraint(),
            self._get_storage_soc_min_constraint(),
            self._get_storage_soc_max_constraint(),
            self._get_storage_capacity_constraint(),
            self._get_storage_net_power_constraint(),
        )

    def _get_storage_max_charge_constraint(self) -> ModelConstraint:
        constraint = self.model.storage_power_in <= self.model.storage_charge_mode * self.params.max_power  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        return ModelConstraint(
            constraint=constraint,
            name="storage_max_charge_constraint",
        )

    def _get_storage_max_discharge_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        constraint = (
            self.model.storage_power_out + self.model.storage_charge_mode * self.params.max_power  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
            <= self.params.max_power  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        )
        return ModelConstraint(
            constraint=constraint,
            name="storage_max_discharge_constraint",
        )

    def _get_storage_soc_dynamics_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        time_coords = self.model.storage_soc.coords[ModelDimension.Time.value]
        constraint_expr = self.model.storage_soc - (
            self.model.storage_soc.shift(time=1)
            + self.params.efficiency_charging * self.model.storage_power_in / self.params.capacity  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
            - 1 / self.params.efficiency_discharging * self.model.storage_power_out / self.params.capacity  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        )

        constraint = constraint_expr.where(time_coords > time_coords[0]) == 0
        return ModelConstraint(
            constraint=constraint,
            name="storage_soc_dynamics_constraint",
        )

    def _get_storage_soc_start_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        t0 = self.model.storage_soc.coords[ModelDimension.Time.value][0]

        soc_t0 = self.model.storage_soc.sel(time=t0)
        charge_t0 = self.model.storage_power_in.sel(time=t0)
        discharge_t0 = self.model.storage_power_out.sel(time=t0)

        constraint_expr = (
            soc_t0
            - self.params.soc_start  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
            - self.params.efficiency_charging * charge_t0 / self.params.capacity  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
            + 1 / self.params.efficiency_discharging * discharge_t0 / self.params.capacity  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        )

        constraint = constraint_expr == 0
        return ModelConstraint(
            constraint=constraint,
            name="storage_soc_start_constraint",
        )

    def _get_storage_soc_end_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        time_coords = self.model.storage_soc.coords[ModelDimension.Time.value]
        last_time = time_coords.values[-1]
        constr_expression = self.model.storage_soc.sel(time=last_time) - self.params.soc_end  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        constraint = constr_expression == 0
        return ModelConstraint(
            constraint=constraint,
            name="storage_soc_end_constraint",
        )

    def _get_storage_soc_min_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        expression = self.model.storage_soc >= self.params.soc_min  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        return ModelConstraint(
            constraint=expression,
            name="storage_soc_min_constraint",
        )

    def _get_storage_soc_max_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        expression = self.model.storage_soc <= self.params.soc_max  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        return ModelConstraint(
            constraint=expression,
            name="storage_soc_max_constraint",
        )

    def _get_storage_capacity_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        constraint = self.model.storage_soc <= 1  # pyrefly: ignore
        return ModelConstraint(
            constraint=constraint,
            name="storage_capacity_constraint",
        )

    def _get_storage_net_power_constraint(self) -> ModelConstraint:
        self._validate_storage_parameters_exist()
        constraint = self.model.storage_power_net == self.model.storage_power_in - self.model.storage_power_out
        return ModelConstraint(
            constraint=constraint,
            name="storage_net_power_constraint",
        )
