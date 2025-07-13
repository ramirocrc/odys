from datetime import timedelta

from optimes.assets.generator import PowerGenerator
from optimes.assets.portfolio import AssetPortfolio
from optimes.assets.storage import Battery
from optimes.math_model.energy_model import EnergyModel, EnergyModelSetName, EnergyModelVariableName
from optimes.system.load import LoadProfile
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
        max_power=50.0,
        capacity=200.0,
        efficiency_charging=1,
        efficiency_discharging=1,
        soc_initial=100.0,
        soc_terminal=50.0,
    )
    load_profile = LoadProfile(
        profile=[50, 75, 100, 125, 150],
        timedelta=timedelta(hours=1),
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)

    model = EnergyModel(
        portfolio=portfolio,
        load_profile=load_profile,
    )
    logger.info(f"Solver Status: {model.solving_status()}")
    logger.info(f"Termination Status: {model.termination_condition()}")

    result = model.optimize()

    logger.info(f"Solver Status: {model.solving_status()}")
    logger.info(f"Termination Status: {model.termination_condition()}")

    # Generators
    generator_power = model.get_pyomo_component(EnergyModelVariableName.GENERATOR_POWER)
    time = model.get_pyomo_component(EnergyModelSetName.TIME)
    generators = model.get_pyomo_component(EnergyModelSetName.GENERATORS)
    batteries = model.get_pyomo_component(EnergyModelSetName.BATTERIES)
    battery_charge = model.get_pyomo_component(EnergyModelVariableName.BATTERY_CHARGE)
    battery_discharge = model.get_pyomo_component(EnergyModelVariableName.BATTERY_DISCHARGE)
    battery_soc = model.get_pyomo_component(EnergyModelVariableName.BATTERY_SOC)

    for t in time:
        for i in generators:
            logger.info(f"t={t}, gen={i}, power={generator_power[t, i].value:.2f} MW")
        # # Batteries
        for j in batteries:
            charge = battery_charge[t, j].value
            discharge = battery_discharge[t, j].value
            soc = battery_soc[t, j].value
            logger.info(f"t={t}, bat={j}, chg={charge:.2f}, dis={discharge:.2f}, soc={soc:.2f}")
