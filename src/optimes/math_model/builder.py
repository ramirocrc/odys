import pyomo.environ as pyo

from optimes.assets.portfolio import AssetPortfolio
from optimes.system.load import LoadProfile


class EnergyModel(pyo.ConcreteModel):
    """
    Wrapper around Pyomo ConcreteModel that holds all Sets, Vars, Constraints, and the Objective.
    Does not store portfolio or load_profile internally—just the optimization elements.
    """

    time: pyo.Set
    generators: pyo.Set
    batteries: pyo.Set

    generator_power: pyo.Var
    battery_charge: pyo.Var
    battery_discharge: pyo.Var
    battery_soc: pyo.Var
    battery_charge_mode: pyo.Var

    power_balance: pyo.Constraint
    generator_limit: pyo.Constraint
    battery_charge_limit: pyo.Constraint
    battery_discharge_limit: pyo.Constraint
    battery_soc_dynamics: pyo.Constraint
    battery_soc_bounds: pyo.Constraint
    battery_soc_terminal: pyo.Constraint

    total_variable_cost: pyo.Objective


class MathModelBuilder:
    def __init__(self, portfolio: AssetPortfolio, load_profile: LoadProfile) -> None:
        self._portfolio = portfolio
        self._load_profile = load_profile

    def build_model(self) -> EnergyModel:
        # === Model ===
        model = EnergyModel()
        # === Sets ===
        time_indices = list(range(len(self._load_profile.profile)))
        generator_indices = list(range(len(self._portfolio.generators)))
        battery_indices = list(range(len(self._portfolio.batteries)))

        model.time = pyo.Set(initialize=time_indices)
        model.generators = pyo.Set(initialize=generator_indices)
        model.batteries = pyo.Set(initialize=battery_indices)

        # === Variables ===
        model.generator_power = pyo.Var(model.time, model.generators, domain=pyo.NonNegativeReals)
        model.battery_charge = pyo.Var(model.time, model.batteries, domain=pyo.NonNegativeReals)
        model.battery_discharge = pyo.Var(model.time, model.batteries, domain=pyo.NonNegativeReals)
        model.battery_soc = pyo.Var(model.time, model.batteries, domain=pyo.NonNegativeReals)
        model.battery_charge_mode = pyo.Var(model.time, model.batteries, within=pyo.Binary)

        # === Constraints ===
        model.power_balance = pyo.Constraint(model.time, rule=self.power_balance_rule)
        model.generator_limit = pyo.Constraint(model.time, model.generators, rule=self.generator_limit_rule)
        model.battery_charge_limit = pyo.Constraint(model.time, model.batteries, rule=self.battery_charge_limit_rule)
        model.battery_discharge_limit = pyo.Constraint(
            model.time,
            model.batteries,
            rule=self.battery_discharge_limit_rule,
        )
        model.battery_soc_dynamics = pyo.Constraint(model.time, model.batteries, rule=self.battery_soc_dynamics_rule)
        model.battery_soc_bounds = pyo.Constraint(model.time, model.batteries, rule=self.battery_soc_bounds_rule)
        model.battery_soc_terminal = pyo.Constraint(model.batteries, rule=self.battery_soc_terminal_rule)

        # === Objective ===
        model.total_variable_cost = pyo.Objective(rule=self.objective_operational_cost, sense=pyo.minimize)

        return model

    def power_balance_rule(self, m: pyo.ConcreteModel, t: int) -> pyo.Expression:
        generation_total = sum(m.generator_power[t, i] for i in m.generators)
        discharge_total = sum(m.battery_discharge[t, j] for j in m.batteries)
        charge_total = sum(m.battery_charge[t, j] for j in m.batteries)
        return generation_total + discharge_total == self._load_profile.profile[t] + charge_total

    def generator_limit_rule(self, m: pyo.ConcreteModel, t: int, i: int) -> pyo.Expression:
        return m.generator_power[t, i] <= self._portfolio.generators[i].nominal_power

    def battery_charge_limit_rule(self, m: pyo.ConcreteModel, t: int, j: int) -> pyo.Expression:
        max_power = self._portfolio.batteries[j].max_power
        return m.battery_charge[t, j] <= max_power * m.battery_charge_mode[t, j]

    def battery_discharge_limit_rule(self, m: pyo.ConcreteModel, t: int, j: int) -> pyo.Expression:
        max_power = self._portfolio.batteries[j].max_power
        return m.battery_discharge[t, j] <= max_power * (1 - m.battery_charge_mode[t, j])

    def battery_soc_dynamics_rule(self, m: pyo.ConcreteModel, t: int, j: int) -> pyo.Expression:
        battery = self._portfolio.batteries[j]
        previous_soc = battery.soc_start if t == 0 else m.battery_soc[t - 1, j]

        return (
            m.battery_soc[t, j]
            == previous_soc
            + battery.efficiency_charging * m.battery_charge[t, j]
            - (1 / battery.efficiency_discharding) * m.battery_discharge[t, j]
        )

    def battery_soc_bounds_rule(self, m: pyo.ConcreteModel, t: int, j: int) -> pyo.Expression:
        return pyo.inequality(0, m.battery_soc[t, j], self._portfolio.batteries[j].capacity)

    def battery_soc_terminal_rule(self, m: pyo.ConcreteModel, j: int) -> pyo.Expression:
        if self._portfolio.batteries[j].soc_end is None:
            return pyo.Constraint.Skip
        return m.battery_soc[len(m.time) - 1, j] == self._portfolio.batteries[j].soc_end

    def objective_operational_cost(self, m: pyo.ConcreteModel) -> pyo.Expression:
        return sum(
            m.generator_power[t, i] * self._portfolio.generators[i].variable_cost for t in m.time for i in m.generators
        )
