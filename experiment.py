import pyomo.environ as pyo

from optimes.assets.generator import PowerGenerator
from optimes.assets.portfolio import AssetPortfolio
from optimes.assets.storage import Battery
from optimes.math_model.builder import MathModelBuilder
from optimes.system.load import LoadProfile
from optimes.utils.logging import get_logger

logger = get_logger(__name__)
if __name__ == "__main__":
    generator_1 = PowerGenerator(
        id=1,
        nominal_power=100.0,
        variable_cost=20.0,
    )
    generator_2 = PowerGenerator(
        id=2,
        nominal_power=150.0,
        variable_cost=25.0,
    )
    battery_1 = Battery(
        id=3,
        max_power=50.0,
        capacity=200.0,
        efficiency_charging=0.95,
        efficiency_discharding=0.95,
        soc_start=100.0,
        soc_end=50.0,
    )
    load_profile = LoadProfile(
        profile=[50, 75, 100, 125, 150],
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)

    model = MathModelBuilder(
        portfolio=portfolio,
        load_profile=load_profile,
    ).build_model()

    solver = pyo.SolverFactory("highs")

    result = solver.solve(model, tee=True)
    logger.info(result.solver.termination_condition)

    total_cost = pyo.value(model.total_variable_cost)  # Print the total variable cost of the solution
    logger.info(f"Total Variable Cost: {total_cost:.2f} €")

    # Generators
    for t in model.time:
        for i in model.generators:
            logger.info(f"t={t}, gen={i}, power={model.generator_power[t, i].value:.2f} MW")
    # Batteries
    for t in model.time:
        for j in model.batteries:
            charge = model.battery_charge[t, j].value
            discharge = model.battery_discharge[t, j].value
            soc = model.battery_soc[t, j].value
            logger.info(f"t={t}, bat={j}, chg={charge:.2f}, dis={discharge:.2f}, soc={soc:.2f}")

    model.display()  # Display the model for debugging purposes
