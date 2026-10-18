---
icon: lucide/scale
---

# `odys.optimization.power_balance`

The power balance: at every scenario and step, the power injected into the bus adds up to zero. Every entity type contributes its `Formulation.power_injection()`; charging returns none, since the EV formulation already counts the charging power.

The balance is written out as [PB-1](../../../formulation/power_balance.md#pb-1) on the Power balance formulation page.

::: odys.optimization.power_balance
