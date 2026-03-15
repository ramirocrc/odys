from odys.energy_system_models.assets.generator import Generator

generator_1 = Generator(
    name="gen1",
    nominal_power=100.0,
    variable_cost=20.0,
    min_up_time=1,
    ramp_down=100,
)
print("success")  # noqa: T201
