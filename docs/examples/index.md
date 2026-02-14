# Examples

These examples walk through common odys use cases, from a basic single-scenario dispatch to stochastic optimization with multiple markets.

Each example is self-contained -- you can copy-paste it and run it directly.

| Example | What it shows |
|---|---|
| [Basic Dispatch](basic_dispatch.md) | Generators + battery meeting a fixed load |
| [Stochastic Scenarios](stochastic.md) | Multiple wind scenarios with batteries |
| [Stochastic Without Batteries](stochastic_no_batteries.md) | Stochastic dispatch using generators only |
| [Markets](markets.md) | Selling excess generation into electricity markets |
| [Markets + Stochastic](markets_stochastic.md) | Stochastic scenarios with stage-fixed market decisions |

## Running the examples

All examples are available in the [`examples/`](https://github.com/ramirocrc/odys/tree/main/examples) directory of the repository. To run one:

```bash
python examples/example1.py
```
