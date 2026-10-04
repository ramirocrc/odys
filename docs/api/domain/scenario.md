---
icon: lucide/file-text
---

# `odys.domain.scenario`

Scenarios for deterministic and stochastic optimization. A `Scenario` holds the typed profiles of one possible future, with a name and a probability. `ScenarioSet` holds the scenarios of one problem and checks that their probabilities sum to 1 and their names are unique; `EnergySystem` builds it from the scenarios you pass.

See [Scenario](../../user_guide/scenario.md) and [Stochastic Optimization](../../user_guide/stochastic.md) in the User Guide.

::: odys.domain.scenario
