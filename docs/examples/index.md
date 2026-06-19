---
icon: lucide/flask-conical
---

# Examples

These examples walk through common Odys use cases, from a basic dispatch
problem to risk-aware market participation.

Each example is self-contained -- you can copy-paste it and run it directly.

| Example | What it shows |
|---|---|
| [Basic Dispatch](basic_dispatch.md) | Cheapest generation meeting a fixed load |
| [Battery Dispatch](battery_dispatch.md) | Using storage to shift solar output over time |
| [Market Arbitrage](market_arbitrage.md) | Choosing between self-generation and market purchases |
| [CVaR Market Risk](cvar_market_risk.md) | Risk-aware market allocation under uncertainty |

## Running the examples

All examples are available in the [`examples/`](https://github.com/ramirocrc/odys/tree/main/examples) directory of the repository. To run one:

```bash
python examples/basic_dispatch.py
python examples/battery_dispatch.py
python examples/market_arbitrage.py
python examples/cvar_market_risk.py
```
