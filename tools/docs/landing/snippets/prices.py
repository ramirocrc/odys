"""Day-ahead price data used by the landing page hero snippets.

Twelve equally likely price scenarios for one day at hourly resolution, built
from a typical day-ahead price shape with seeded variations in the solar dip
and the evening peak.

``forecast`` is a single point forecast: one plausible day from the set, as a
forecaster would deliver it. It is deliberately not the scenario mean (or
median): expected profit is linear in prices, so optimizing against the mean
gives exactly the stochastic schedule and the hero tabs would look identical.
"""

import numpy as np

_BASE_SHAPE = np.array(
    [48, 44, 41, 39, 40, 46, 62, 80, 86, 74, 58, 44, 36, 34, 40, 54, 76, 98, 108, 96, 80, 66, 58, 52],
    dtype=float,
)
_SOLAR_HOURS = slice(10, 16)
_PEAK_HOURS = slice(16, 22)
_NUMBER_OF_SCENARIOS = 12
_SEED = 11


def _build_price_scenarios() -> list[list[float]]:
    rng = np.random.default_rng(_SEED)
    scenarios = []
    for _ in range(_NUMBER_OF_SCENARIOS):
        prices = _BASE_SHAPE.copy()
        prices[_SOLAR_HOURS] *= rng.uniform(0.55, 1.3)
        prices[_PEAK_HOURS] *= rng.uniform(0.7, 1.35)
        prices += rng.uniform(-8, 8) + rng.uniform(-4.5, 4.5, size=prices.size)
        scenarios.append([round(float(p), 2) for p in np.maximum(prices, 4.0)])
    return scenarios


_FORECAST_SCENARIO = 1

price_scenarios = _build_price_scenarios()
forecast = list(price_scenarios[_FORECAST_SCENARIO])
