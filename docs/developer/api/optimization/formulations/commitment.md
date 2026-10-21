---
icon: lucide/power
---

# `odys.optimization.formulations.commitment`

The shared on/off model of generators and flexible loads (`CommitmentFormulation`), a reusable part both formulations compose: the status, start-up and shut-down indicators, and the minimum up and down times. Variable and constraint names carry the entity dimension as a prefix.

The constraints are written out on the [Generators](../../../../formulation/generators.md#g-5) formulation page, and their flexible-load use in [FL-2](../../../../formulation/flexible_loads.md#fl-2).

See also [Commitment](../../domain/entities/commitment.md) for the domain model and [entity_arrays](../../parameters/entity_arrays.md) for the parameter arrays.

::: odys.optimization.formulations.commitment
