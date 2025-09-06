import linopy

from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.parameters import BatteryParameters
from optimes._math_model.model_components.sets import EnergyModelDimension
from optimes._math_model.model_components.variables import ModelVariable


class BatteryConstraints:
    def __init__(self, linopy_model: linopy.Model, params: BatteryParameters) -> None:
        self.model = linopy_model
        self.params = params
        self.var_battery_soc = self.model.variables[ModelVariable.BATTERY_SOC.var_name]
        self.var_battery_charge = self.model.variables[ModelVariable.BATTERY_POWER_IN.var_name]
        self.var_battery_discharge = self.model.variables[ModelVariable.BATTERY_POWER_OUT.var_name]
        self.var_battery_net_power = self.model.variables[ModelVariable.BATTERY_POWER_NET.var_name]
        self.var_battery_charge_mode = self.model.variables[ModelVariable.BATTERY_CHARGE_MODE.var_name]

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
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
        constraint = self.var_battery_charge <= self.var_battery_charge_mode * self.params.batteries_max_power  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="battery_max_charge_constraint",
        )

    def _get_battery_max_discharge_constraint(self) -> ModelConstraint:
        # var_battery_discharge <= (1 - var_battery_mode) * param_battery_max_power # noqa: ERA001
        constraint = (
            self.var_battery_discharge + self.var_battery_charge_mode * self.params.batteries_max_power  # pyright: ignore reportOperatorIssue
            <= self.params.batteries_max_power
        )
        return ModelConstraint(
            constraint=constraint,
            name="battery_max_discharge_constraint",
        )

    def _get_battery_soc_dynamics_constraint(self) -> ModelConstraint:
        time_coords = self.var_battery_soc.coords[EnergyModelDimension.Time.value]
        constraint_expr = self.var_battery_soc - (
            self.var_battery_soc.shift(time=1)
            + self.params.batteries_efficiency_charging * self.var_battery_charge
            - 1 / self.params.batteries_efficiency_discharging * self.var_battery_discharge
        )

        constraint = constraint_expr.where(time_coords > time_coords[0]) == 0
        return ModelConstraint(
            constraint=constraint,
            name="battery_soc_dynamics_constraint",
        )

    def _get_battery_soc_start_constraint(self) -> ModelConstraint:
        t0 = self.var_battery_soc.coords[EnergyModelDimension.Time.value][0]

        soc_t0 = self.var_battery_soc.sel(time=t0)
        charge_t0 = self.var_battery_charge.sel(time=t0)
        discharge_t0 = self.var_battery_discharge.sel(time=t0)

        constraint_expr = (
            soc_t0
            - self.params.batteries_soc_start
            - self.params.batteries_efficiency_charging * charge_t0
            + 1 / self.params.batteries_efficiency_discharging * discharge_t0
        )

        constraint = constraint_expr == 0
        return ModelConstraint(
            constraint=constraint,
            name="battery_soc_start_constraint",
        )

    def _get_battery_soc_end_constraint(self) -> ModelConstraint:
        time_coords = self.var_battery_soc.coords[EnergyModelDimension.Time.value]
        constr_expression = self.var_battery_soc.loc[time_coords.values[-1]] - self.params.batteries_soc_end
        constraint = constr_expression == 0
        return ModelConstraint(
            constraint=constraint,
            name="battery_soc_end_constraint",
        )

    def _get_battery_soc_min_constriant(self) -> ModelConstraint:
        expression = self.var_battery_soc >= self.params.batteries_soc_min
        return ModelConstraint(
            constraint=expression,
            name="batter_soc_min_constraint",
        )

    def _get_battery_soc_max_constriant(self) -> ModelConstraint:
        expression = self.var_battery_soc <= self.params.batteries_soc_max
        return ModelConstraint(
            constraint=expression,
            name="batter_soc_max_constraint",
        )

    def _get_battery_capacity_constraint(self) -> ModelConstraint:
        constraint = self.var_battery_soc <= self.params.batteries_capacity
        return ModelConstraint(
            constraint=constraint,
            name="battery_capacity_constraint",
        )

    def _get_battery_net_power_constraint(self) -> ModelConstraint:
        constraint = self.var_battery_net_power == self.var_battery_charge - self.var_battery_discharge
        return ModelConstraint(
            constraint=constraint,
            name="battery_net_power_constraint",
        )
