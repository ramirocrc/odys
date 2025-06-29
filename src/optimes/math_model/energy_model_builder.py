# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportOperatorIssue=false

import pyomo.environ as pyo

from optimes.assets.portfolio import AssetPortfolio
from optimes.math_model.energy_model import (
    EnergyModel,
    EnergyModelConstraint,
    EnergyModelObjective,
    EnergyModelSet,
    EnergyModelVariable,
)
from optimes.system.load import LoadProfile


class EnergyModelBuilder:
    def __init__(self, portfolio: AssetPortfolio, load_profile: LoadProfile) -> None:
        self._portfolio = portfolio
        self._load_profile = load_profile
        self._model = EnergyModel()

    def build(self) -> EnergyModel:
        self._add_model_sets()
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()

        return self._model

    def _add_model_sets(self) -> None:
        time_indices = list(range(len(self._load_profile.profile)))
        generator_indices = list(range(len(self._portfolio.generators)))
        battery_indices = list(range(len(self._portfolio.batteries)))

        self._model.add_set(EnergyModelSet.TIME, pyo.Set(initialize=time_indices))
        self._model.add_set(EnergyModelSet.GENERATORS, pyo.Set(initialize=generator_indices))
        self._model.add_set(EnergyModelSet.BATTERIES, pyo.Set(initialize=battery_indices))

    def _add_model_variables(self) -> None:
        self._add_power_generator_variables()
        self._add_battery_variables()

    def _add_power_generator_variables(self) -> None:
        self._model.add_variable(
            EnergyModelVariable.GENERATOR_POWER,
            pyo.Var(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.GENERATORS),
                domain=pyo.NonNegativeReals,
            ),
        )

    def _add_battery_variables(self) -> None:
        self._model.add_variable(
            EnergyModelVariable.BATTERY_CHARGE,
            pyo.Var(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                domain=pyo.NonNegativeReals,
                name=EnergyModelVariable.BATTERY_CHARGE.value,
            ),
        )
        self._model.add_variable(
            EnergyModelVariable.BATTERY_DISCHARGE,
            pyo.Var(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                domain=pyo.NonNegativeReals,
                name=EnergyModelVariable.BATTERY_DISCHARGE.value,
            ),
        )
        self._model.add_variable(
            EnergyModelVariable.BATTERY_SOC,
            pyo.Var(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                domain=pyo.NonNegativeReals,
                name=EnergyModelVariable.BATTERY_SOC.value,
            ),
        )
        self._model.add_variable(
            EnergyModelVariable.BATTERY_CHARGE_MODE,
            pyo.Var(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                within=pyo.Binary,
            ),
        )

    def _add_model_constraints(self) -> None:
        self._add_power_balance_constraint()
        self._add_power_generator_constraints()
        self._add_model_battery_constraints()

    def _add_power_balance_constraint(self) -> None:
        self._model.add_constraint(
            EnergyModelConstraint.POWER_BALANCE,
            pyo.Constraint(self._model.get_set(EnergyModelSet.TIME), rule=self.power_balance_rule),
        )

    def _add_power_generator_constraints(self) -> None:
        self._model.add_constraint(
            EnergyModelConstraint.GENERATOR_LIMIT,
            pyo.Constraint(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.GENERATORS),
                rule=self.generator_limit_rule,
            ),
        )

    def _add_model_battery_constraints(self) -> None:
        self._model.add_constraint(
            EnergyModelConstraint.BATTERY_CHARGE_LIMIT,
            pyo.Constraint(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                rule=self.battery_charge_limit_rule,
            ),
        )
        self._model.add_constraint(
            EnergyModelConstraint.BATTERY_DISCHARGE_LIMIT,
            pyo.Constraint(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                rule=self.battery_discharge_limit_rule,
            ),
        )
        self._model.add_constraint(
            EnergyModelConstraint.BATTERY_SOC_DYNAMICS,
            pyo.Constraint(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                rule=self.battery_soc_dynamics_rule,
            ),
        )
        self._model.add_constraint(
            EnergyModelConstraint.BATTERY_SOC_BOUNDS,
            pyo.Constraint(
                self._model.get_set(EnergyModelSet.TIME),
                self._model.get_set(EnergyModelSet.BATTERIES),
                rule=self.battery_soc_bounds_rule,
            ),
        )
        self._model.add_constraint(
            EnergyModelConstraint.BATTERY_SOC_TERMINAL,
            pyo.Constraint(
                self._model.get_set(EnergyModelSet.BATTERIES),
                rule=self.battery_soc_terminal_rule,
            ),
        )

    def _add_model_objective(self) -> None:
        self._model.add_objective(
            EnergyModelObjective.TOTAL_VARIABLE_COST,
            pyo.Objective(rule=self.objective_operational_cost, sense=pyo.minimize),
        )

    def power_balance_rule(self, m: EnergyModel, t: int):  # noqa: ANN201
        generator_power = m.get_variable(EnergyModelVariable.GENERATOR_POWER)
        battery_discharge = m.get_variable(EnergyModelVariable.BATTERY_DISCHARGE)
        battery_charge = m.get_variable(EnergyModelVariable.BATTERY_CHARGE)

        generation_total = sum(generator_power[t, i] for i in m.get_set(EnergyModelSet.GENERATORS))
        discharge_total = sum(battery_discharge[t, j] for j in m.get_set(EnergyModelSet.BATTERIES))
        charge_total = sum(battery_charge[t, j] for j in m.get_set(EnergyModelSet.BATTERIES))
        return generation_total + discharge_total == self._load_profile.profile[t] + charge_total

    def generator_limit_rule(self, m: EnergyModel, t: int, i: int):  # noqa: ANN201
        generator_power = m.get_variable(EnergyModelVariable.GENERATOR_POWER)

        return generator_power[t, i] <= self._portfolio.generators[i].nominal_power

    def battery_charge_limit_rule(self, m: EnergyModel, t: int, j: int):  # noqa: ANN201
        battery_charge = m.get_variable(EnergyModelVariable.BATTERY_CHARGE)
        battery_charge_mode = m.get_variable(EnergyModelVariable.BATTERY_CHARGE_MODE)

        max_power = self._portfolio.batteries[j].max_power
        return battery_charge[t, j] <= max_power * battery_charge_mode[t, j]

    def battery_discharge_limit_rule(self, m: EnergyModel, t: int, j: int):  # noqa: ANN201
        battery_discharge = m.get_variable(EnergyModelVariable.BATTERY_DISCHARGE)
        battery_charge_mode = m.get_variable(EnergyModelVariable.BATTERY_CHARGE_MODE)

        max_power = self._portfolio.batteries[j].max_power
        return battery_discharge[t, j] <= max_power * (1 - battery_charge_mode[t, j])

    def battery_soc_dynamics_rule(self, m: EnergyModel, t: int, j: int):  # noqa: ANN201
        battery_soc = m.get_variable(EnergyModelVariable.BATTERY_SOC)
        battery_charge = m.get_variable(EnergyModelVariable.BATTERY_CHARGE)
        battery_discharge = m.get_variable(EnergyModelVariable.BATTERY_DISCHARGE)

        battery = self._portfolio.batteries[j]
        previous_soc = battery.soc_start if t == 0 else battery_soc[t - 1, j]

        return (
            battery_soc[t, j]
            == previous_soc
            + battery_charge[t, j] * battery.efficiency_charging
            - battery_discharge[t, j] / battery.efficiency_discharding
        )

    def battery_soc_bounds_rule(self, m: EnergyModel, t: int, j: int):  # noqa: ANN201
        battery_soc = m.get_variable(EnergyModelVariable.BATTERY_SOC)
        return pyo.inequality(0, battery_soc[t, j], self._portfolio.batteries[j].capacity)

    def battery_soc_terminal_rule(self, m: EnergyModel, j: int):  # noqa: ANN201
        battery_soc = m.get_variable(EnergyModelVariable.BATTERY_SOC)
        if self._portfolio.batteries[j].soc_end is None:
            return pyo.Constraint.Skip
        return battery_soc[len(m.get_set(EnergyModelSet.TIME)) - 1, j] == self._portfolio.batteries[j].soc_end

    def objective_operational_cost(self, m: EnergyModel):  # noqa: ANN201
        generator_power = m.get_variable(EnergyModelVariable.GENERATOR_POWER)

        return sum(
            generator_power[t, i] * self._portfolio.generators[i].variable_cost
            for t in m.get_set(EnergyModelSet.TIME)
            for i in m.get_set(EnergyModelSet.GENERATORS)
        )
