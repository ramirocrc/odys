from datetime import timedelta

from optimes.energy_system.assets.generator import PowerGenerator
from optimes.energy_system.assets.portfolio import AssetPortfolio
from optimes.energy_system.assets.storage import Battery
from optimes.energy_system.energy_system_conditions import EnergySystem
from optimes.math_model.model_components.sets import EnergyModelSetName
from optimes.math_model.model_components.variables import EnergyModelVariableName
from optimes.math_model.optimizer import EnergySystemOptimizer
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
        capacity=100.0,
        efficiency_charging=1,
        efficiency_discharging=1,
        soc_initial=100.0,
        soc_terminal=50.0,
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)

    system_data = EnergySystem(
        portfolio=portfolio,
        demand_profile=[50, 75, 100, 125, 150],
        timestep=timedelta(minutes=30),
    )

    optimizer = EnergySystemOptimizer(system_data)
    logger.info(f"Solver Status: {optimizer.solving_status()}")
    logger.info(f"Termination Status: {optimizer.termination_condition()}")

    result = optimizer.optimize()

    logger.info(f"Solver Status: {optimizer.solving_status()}")
    logger.info(f"Termination Status: {optimizer.termination_condition()}")

    # Generators
    generator_power = optimizer.algebraic_model.get_var(EnergyModelVariableName.GENERATOR_POWER)
    time = optimizer.algebraic_model.get_set(EnergyModelSetName.TIME)
    generators = optimizer.algebraic_model.get_set(EnergyModelSetName.GENERATORS)
    batteries = optimizer.algebraic_model.get_set(EnergyModelSetName.BATTERIES)
    battery_charge = optimizer.algebraic_model.get_var(EnergyModelVariableName.BATTERY_CHARGE)
    battery_discharge = optimizer.algebraic_model.get_var(EnergyModelVariableName.BATTERY_DISCHARGE)
    battery_soc = optimizer.algebraic_model.get_var(EnergyModelVariableName.BATTERY_SOC)

    for t in time:
        for i in generators:
            logger.info(f"t={t}, gen={i}, power={generator_power[t, i].value:.2f} MW")
        # # Batteries
        for j in batteries:
            charge = battery_charge[t, j].value
            discharge = battery_discharge[t, j].value
            soc = battery_soc[t, j].value
            logger.info(f"t={t}, bat={j}, chg={charge:.2f}, dis={discharge:.2f}, soc={soc:.2f}")
