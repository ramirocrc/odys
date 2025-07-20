from datetime import timedelta

from optimes.assets.generator import PowerGenerator
from optimes.assets.portfolio import AssetPortfolio
from optimes.assets.storage import Battery
from optimes.math_model.energy_model import EnergyModel
from optimes.math_model.pyomo_components.sets import EnergyModelSetName
from optimes.math_model.pyomo_components.variables import EnergyModelVariableName
from optimes.system.scenario import ScenarioConditions
from optimes.utils.logging import get_logger

logger = get_logger(__name__)
if __name__ == "__main__":
    generator_1 = PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )
    generator_2 = PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )
    battery_1 = Battery(
        name="battery1",
        max_power=200.0,
        capacity=200.0,
        efficiency_charging=1,
        efficiency_discharging=1,
        soc_initial=100.0,
        soc_terminal=0.0,
    )
    load_profile = ScenarioConditions(
        demand_profile=[50, 75, 100, 125, 450],
        timestep=timedelta(minutes=30),
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)

    model = EnergyModel(
        portfolio=portfolio,
        scenario=load_profile,
    )
    logger.info(f"Solver Status: {model.solving_status()}")
    logger.info(f"Termination Status: {model.termination_condition()}")

    result = model.optimize()

    logger.info(f"Solver Status: {model.solving_status()}")
    logger.info(f"Termination Status: {model.termination_condition()}")

    # Generators
    generator_power = model[EnergyModelVariableName.GENERATOR_POWER]
    time = model[EnergyModelSetName.TIME]
    generators = model[EnergyModelSetName.GENERATORS]
    batteries = model[EnergyModelSetName.BATTERIES]
    battery_charge = model[EnergyModelVariableName.BATTERY_CHARGE]
    battery_discharge = model[EnergyModelVariableName.BATTERY_DISCHARGE]
    battery_soc = model[EnergyModelVariableName.BATTERY_SOC]

    for t in time:
        for i in generators:
            logger.info(f"t={t}, gen={i}, power={generator_power[t, i].value:.2f} MW")
        # # Batteries
        for j in batteries:
            charge = battery_charge[t, j].value
            discharge = battery_discharge[t, j].value
            soc = battery_soc[t, j].value
            logger.info(f"t={t}, bat={j}, chg={charge:.2f}, dis={discharge:.2f}, soc={soc:.2f}")
