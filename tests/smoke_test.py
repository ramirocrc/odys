from datetime import timedelta

from odys.domain.entities.commitment import Commitment
from odys.domain.entities.generator import Generator

generator_1 = Generator(
    name="gen1",
    nominal_power=100.0,
    variable_cost=20.0,
    ramp_down=100,
    commitment=Commitment(min_up_time=timedelta(hours=1)),
)
print("success")  # noqa: T201
