import pyomo.environ as pyo
from pydantic import BaseModel


class EnergyAsset(BaseModel):
    id: int


class PowerGenerator(EnergyAsset):
    nominal_power: float  # Max capacity [MW]
    variable_cost: float  # [€/MWh]


class Battery(EnergyAsset):
    capacity: float  # Energy capacity [MWh]
    max_power: float  # Max charge/discharge power [MW]
    efficiency: float  # Charge efficiency [0-1]
    soc_start: float  # Initial SoC [MWh]


class AssetPortfolio:
    def __init__(self, assets: list[EnergyAsset] | None = None) -> None:
        self._assets = assets if assets else []

    @property
    def assets(self) -> list[EnergyAsset]:
        return self._assets

    def add_asset(self, asset: EnergyAsset) -> None:
        self._assets.append(asset)

    @property
    def generators(self) -> list[PowerGenerator]:
        return [g for g in self._assets if isinstance(g, PowerGenerator)]

    @property
    def batteries(self) -> list[Battery]:
        return [b for b in self.assets if isinstance(b, Battery)]


class LoadProfile(BaseModel):
    profile: list[float]


class MathModelBuilder:
    def __init__(self, portfolio: AssetPortfolio, load_profile: LoadProfile) -> None:
        self._portfolio = portfolio
        self._load_profile = load_profile

    def build_model(self) -> pyo.ConcreteModel:
        # === Model ===
        model = pyo.ConcreteModel()

        # === Sets ===
        time_indeces = list(range(len(self._load_profile.profile)))
        generator_indeces = list(range(len(self._portfolio.generators)))
        battery_indeces = list(range(len(self._portfolio.batteries)))

        model.time = pyo.Set(initialize=time_indeces)
        model.generators = pyo.Set(initialize=generator_indeces)
        model.batteries = pyo.Set(initialize=battery_indeces)

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
        model.battery_charge_limit = pyo.Constraint(model.time, model.batteries, rule=self.battery_discharge_limit_rule)
        model.battery_soc_dynamics = pyo.Constraint(model.time, model.batteries, rule=self.battery_soc_dynamics_rule)
        model.battery_soc_bounds = pyo.Constraint(model.time, model.batteries, rule=self.battery_soc_bounds_rule)

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
            == previous_soc + battery.efficiency * m.battery_charge[t, j] - (1 / battery.efficiency) * m.battery_discharge[t, j]
        )

    def battery_soc_bounds_rule(self, m: pyo.ConcreteModel, t: int, j: int) -> pyo.Expression:
        return pyo.inequality(0, m.battery_soc[t, j], self._portfolio.batteries[j].capacity)

    def objective_operational_cost(self, m: pyo.ConcreteModel) -> pyo.Expression:
        return sum(m.generator_power[t, i] * self._portfolio.generators[i].variable_cost for t in m.time for i in m.generators)
