from odys._math_model.milp_model import EnergyMILPModel
from odys._math_model.model_components.constraints.model_constraint import ModelConstraint
from odys._math_model.model_components.sets import ModelDimension


class BatteryConstraints:
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        self.model = milp_model
        self.params = milp_model.parameters.batteries

    def _validate_battery_parameters_exist(self) -> None:
        if self.params is None:
            msg = "No battery parameters specified."
            raise ValueError(msg)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        if self.params is None:
            return ()
        return (
            self._get_battery_max_charge_constraint(),
            self._get_battery_max_discharge_constraint(),
            self._get_battery_soc_dynamics_constraint(),
            self._get_battery_soc_start_constraint(),
            self._get_battery_soc_end_constraint(),
            self._get_battery_soc_min_constriant(),
            self._get_battery_soc_max_constriant(),
            self._get_battery_capacity_constraint(),
            self._get_battery_net_power_constraint(),
        )

    def _get_battery_max_charge_constraint(self) -> ModelConstraint:
        # var_battery_discharge <= (1 - var_battery_mode) * param_battery_max_power # noqa: ERA001
        constraint = self.model.battery_power_in <= self.model.battery_charge_mode * self.params.max_power  # ty: ignore # pyrefly: ignore
        return ModelConstraint(
            constraint=constraint,
            name="battery_max_charge_constraint",
        )

    def _get_battery_max_discharge_constraint(self) -> ModelConstraint:
        # var_battery_discharge <= (1 - var_battery_mode) * param_battery_max_power # noqa: ERA001
        self._validate_battery_parameters_exist()
        constraint = (
            self.model.battery_power_out + self.model.battery_charge_mode * self.params.max_power  # ty: ignore # pyrefly: ignore
            <= self.params.max_power  # ty: ignore # pyrefly: ignore
        )
        return ModelConstraint(
            constraint=constraint,
            name="battery_max_discharge_constraint",
        )

    def _get_battery_soc_dynamics_constraint(self) -> ModelConstraint:
        self._validate_battery_parameters_exist()
        time_coords = self.model.battery_soc.coords[ModelDimension.Time.value]
        constraint_expr = self.model.battery_soc - (
            self.model.battery_soc.shift(time=1)
            + self.params.efficiency_charging * self.model.battery_power_in / self.params.capacity  # ty: ignore # pyrefly: ignore
            - 1 / self.params.efficiency_discharging * self.model.battery_power_out / self.params.capacity  # ty: ignore # pyrefly: ignore
        )

        constraint = constraint_expr.where(time_coords > time_coords[0]) == 0
        return ModelConstraint(
            constraint=constraint,
            name="battery_soc_dynamics_constraint",
        )

    def _get_battery_soc_start_constraint(self) -> ModelConstraint:
        self._validate_battery_parameters_exist()
        t0 = self.model.battery_soc.coords[ModelDimension.Time.value][0]

        soc_t0 = self.model.battery_soc.sel(time=t0)
        charge_t0 = self.model.battery_power_in.sel(time=t0)
        discharge_t0 = self.model.battery_power_out.sel(time=t0)

        constraint_expr = (
            soc_t0
            - self.params.soc_start  # ty: ignore # pyrefly: ignore
            - self.params.efficiency_charging * charge_t0 / self.params.capacity  # ty: ignore # pyrefly: ignore
            + 1 / self.params.efficiency_discharging * discharge_t0 / self.params.capacity  # ty: ignore # pyrefly: ignore
        )

        constraint = constraint_expr == 0
        return ModelConstraint(
            constraint=constraint,
            name="battery_soc_start_constraint",
        )

    def _get_battery_soc_end_constraint(self) -> ModelConstraint:
        self._validate_battery_parameters_exist()
        time_coords = self.model.battery_soc.coords[ModelDimension.Time.value]
        last_time = time_coords.values[-1]
        constr_expression = self.model.battery_soc.sel(time=last_time) - self.params.soc_end  # ty: ignore # pyrefly: ignore
        constraint = constr_expression == 0
        return ModelConstraint(
            constraint=constraint,
            name="battery_soc_end_constraint",
        )

    def _get_battery_soc_min_constriant(self) -> ModelConstraint:
        self._validate_battery_parameters_exist()
        expression = self.model.battery_soc >= self.params.soc_min  # ty: ignore # pyrefly: ignore
        return ModelConstraint(
            constraint=expression,
            name="batter_soc_min_constraint",
        )

    def _get_battery_soc_max_constriant(self) -> ModelConstraint:
        self._validate_battery_parameters_exist()
        expression = self.model.battery_soc <= self.params.soc_max  # ty: ignore # pyrefly: ignore
        return ModelConstraint(
            constraint=expression,
            name="batter_soc_max_constraint",
        )

    def _get_battery_capacity_constraint(self) -> ModelConstraint:
        self._validate_battery_parameters_exist()
        constraint = self.model.battery_soc <= 1  # pyrefly: ignore
        return ModelConstraint(
            constraint=constraint,
            name="battery_capacity_constraint",
        )

    def _get_battery_net_power_constraint(self) -> ModelConstraint:
        self._validate_battery_parameters_exist()
        constraint = self.model.battery_power_net == self.model.battery_power_in - self.model.battery_power_out
        return ModelConstraint(
            constraint=constraint,
            name="battery_net_power_constraint",
        )
