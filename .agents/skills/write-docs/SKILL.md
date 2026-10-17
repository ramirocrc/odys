---
name: write-docs
description: Voice, structure and page templates for the odys documentation (User Guide, Examples, Mathematical Formulation, landing page). Use whenever a page under docs/ is created or changed, including docs updates that come with a code change.
---

# Write the docs

Principles for writing and improving the Odys documentation. The voice is the same on every page: friendly, light and exact (§13).

## Checklist

- [ ] Find the page's place in the [information architecture](#information-architecture) and the question it answers (§2).
- [ ] Start from the matching template in [templates.md](templates.md): an asset or market page, or a formulation page.
- [ ] Write in the voice of §13. Explain every rule by what the optimizer would get away with without it (§11).
- [ ] Equations only in `docs/formulation/`, in the constraint rhythm of §4. User Guide pages link to the constraint instead.
- [ ] User Guide code runs in order and shows its exact output (§3). Reuse the running example's names.
- [ ] End with a bridge to the next page (§15), and cross-link where concepts appear (§17).
- [ ] Add new pages to the `nav` in `zensical.toml`.
- [ ] Run `just docs-build` (strict build, plus `tools/docs/check_user_guide.py`) before saying the page is done.

## 1. Make the Quickstart unbelievably good

This is the most important page. Someone should be able to install the package, copy 20-30 lines of code, see a useful result, and understand why it works -- within 5 minutes.

The quickstart lives on `index.md` as the "Quick example" section. The "Get started" button links to `user_guide/concepts/energy_system.md`, which expands on the same workflow.

The smallest example that makes someone think "now I get it" is not a toy. It is a realistic dispatch problem with a generator, a load, and a visible result:

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, FixedLoad, LoadProfile, Scenario

generator = Generator(name="gen", nominal_power=100.0, variable_cost=50.0)
load = FixedLoad(name="demand")

portfolio = AssetPortfolio([generator, load])

energy_system = EnergySystem(
    portfolio=portfolio,
    scenarios=Scenario(profiles=(LoadProfile(load=load, values=[60, 90, 40, 70]),)),
    timestep=timedelta(hours=1),
    number_of_steps=4,
)

result = energy_system.optimize()
print(result.generators.power)
```

## 2. Tell a story instead of listing features

Follow the user's journey. Each page answers the next question a user naturally has:

1. What is this and how do I install it? (`index.md`)
2. How do I set up my first system? (`user_guide/concepts/`)
3. What assets can I model? (`user_guide/assets/`)
4. Where can I buy and sell energy? (`user_guide/markets/`)
5. What does the optimizer maximize, and how do I read the results? (`user_guide/optimization/`)
6. What if the future is uncertain? (`user_guide/optimization/stochastic.md`)
7. Can I see a full worked example? (`examples/`)
8. What exactly does odys solve, and why that way? (`formulation/`)

Think in terms of "What is the user wondering now?" not "What feature should I describe?"

The same holds inside each section. Every page opens with the question it answers, in everyday words, before any code or symbol, and ends with the question it leaves open (see §15).

## 3. Every page should have runnable examples

Every page contains executable code. Not pseudocode. Real code. The code blocks of a page run in order, from its first block, without names from other pages. A block that shows output is followed by a `text` block with exactly what it prints. `just docs-build` runs `tools/docs/check_user_guide.py`, which executes every User Guide page and fails on an error or an output that differs (column spacing and the sign of zero aside). Avoid ties: when several dispatches are equally optimal, the solver may print another one, so change the data until the optimum is unique, and round what you print.

The User Guide builds on one running example, described on `user_guide/index.md`: reuse its names and numbers (`ccgt`, `wind`, `factory`, `process`, `bess`, `day_ahead`) rather than inventing a new system on each page.

Pattern:

1. Here is the problem.
2. Here is the solution.
3. Here is the output.
4. Here is what changed.

Someone can almost learn by scrolling.

The exception is the Mathematical Formulation section (`formulation/`): it describes the model, so its pages have no code and no running example. `check_user_guide.py` runs only `user_guide/`.

## 4. Anchor every equation in words

Odys is a mathematical library. Equations are a first-class part of the documentation, not something to hide, but they always come with words around them.

Equations live only in the Mathematical Formulation section (`docs/formulation/`), written once, on the page of the model part that owns them. User Guide pages carry no `$$` math: they explain the behaviour in words and link to the constraint ("The output can change by at most `ramp_up` per step; see [G-7](../../formulation/generators.md#g-7).").

On formulation pages, every constraint follows the same rhythm (see the formulation page template in [templates.md](templates.md)):

1. A heading that says what happens: `G-7 · Output changes gradually`, not `G-7 · Ramp limits`.
2. One plain sentence on what it enforces.
3. The equation. With a binary, the logical form first, then the big-M form with the value of M.
4. The equation read aloud, in one everyday sentence.
5. Why it looks like this: what the optimizer would get away with without it (§11).
6. Good to know, when there is something: limitations and redundancy.
7. A facts line: `Added: … · Binds: … · Name: <linopy name>`.

Instead of:

> The following constraint can optionally be applied to limit the generator output...

Write:

> **G-4 · Output fits the available capacity.** A generator never produces more than the scenario lets it.
>
> $$p_{g,s,t} \le A_{g,s,t}$$
>
> Read aloud: at every step, output stays below what the wind, the sun or the fuel supply allows.

Keep it short. People skim, and examples and equations beat paragraphs, but the few words around an equation are what make it readable.

## 5. One concept per section

Within a page, each `##` heading covers one idea. Across the site, each page has a clear focus.

A page like `assets/generator.md` covers:

- Basic usage (one concept)
- Ramp limits (one concept)
- Minimum up and down time (one concept)
- Startup and shutdown cost (one concept)
- Results (one concept)
- How it's modelled (one concept: links to the formulation)

Each section is self-contained. A reader can jump to "Ramp constraints" without reading the rest.

## 6. Progressive disclosure

Beginners see:

```python
gen = Generator(name="gen", nominal_power=100.0, variable_cost=50.0)
```

Intermediate users learn:

```python
gen = Generator(
    name="gen",
    nominal_power=100.0,
    variable_cost=50.0,
    ramp_up=50.0,
    min_up_time=timedelta(hours=4),
)
```

Advanced users discover:

```python
gen = Generator(
    name="gen",
    nominal_power=100.0,
    variable_cost=50.0,
    ramp_up=50.0,
    min_up_time=timedelta(hours=4),
    startup_cost=500.0,
    min_power=20.0,
)
```

The docs never overwhelm. Complexity appears only when needed.

## 7. Have an opinion

Don't say "there are many ways." Say "use this." Then later: "if you need something more advanced..."

Opinionated documentation reduces cognitive load. For example:

> Use a single `Scenario` for deterministic problems. When you need to account for uncertainty, pass several scenarios, each with a `probability`.

## 8. Make examples realistic

Bad:

```python
x = Foo()
```

Good:

```python
solar = Generator(name="solar_pv", nominal_power=150.0, variable_cost=0.0)
load = FixedLoad(name="load")
scenario = Scenario(
    profiles=(
        AvailableCapacityProfile(generator=solar, values=[0, 30, 60, 80, 100, 80, 60, 30, 0]),
        LoadProfile(load=load, values=9 * [70]),
    ),
)
```

Someone working in energy optimization immediately recognizes the problem.

## 9. Use diagrams

Mermaid diagrams clarify system structure and data flow. Use them for:

**Asset topology** (as in `basic_dispatch.md`):

```mermaid
flowchart LR
    Solar(["Solar PV<br/>150 MW"]) --> Bus(["Bus"])
    CCGT(["CCGT<br/>100 MW"]) --> Bus
    Bus --> Load(["Load<br/>70 MW"])
```

**Optimization workflow**:

```
Assets --> AssetPortfolio --> EnergySystem --> optimize() --> Results
```

**Object relationships**:

```
EnergySystem
 ├── AssetPortfolio
 │    ├── Generator
 │    ├── StationaryStorage
 │    ├── ElectricVehicle
 │    ├── Charger
 │    ├── FixedLoad
 │    └── FlexibleLoad
 ├── Scenario | Scenario[] (with probabilities)
 ├── initial_conditions / final_conditions (optional)
 └── EnergyMarket[] (optional)
```

Good diagrams replace pages of text.

## 10. Separate tutorials from reference

This is the Diataxis framework applied to Odys:

| Section       | Purpose                                 | Location                                            |
| ------------- | --------------------------------------- | --------------------------------------------------- |
| User Guide    | Teach concepts and walk through the API | `user_guide/`                                       |
| Examples      | Solve a specific problem end-to-end     | `examples/`                                         |
| API Reference | Exact signatures, types, and defaults   | `developer/api/`                                    |
| Mathematical Formulation | The exact model and why it looks that way | `formulation/`                          |

Don't mix them. A user guide page teaches. An API page documents. An example page solves.

## 11. Explain the rationale

Don't just explain what. Explain why.

Instead of:

> The storage model uses binary charging mode variables.

Explain:

> A binary variable stops the battery from charging and discharging at the same time. Every round trip loses energy, so when prices go negative, the optimizer would otherwise do both at once on purpose, burning energy to get paid for it.

The easiest way to explain a rule is to say what the optimizer would get away with without it.

## 12. The user guide is primary; the API reference is secondary

The user guide teaches the workflow with runnable examples. The API reference (`developer/api/`) provides exact signatures for when the user needs details.

Most users should never need to read the API reference to use Odys. The user guide should be self-sufficient.

## 13. Voice: friendly, light, exact

Write like you're pair programming with the reader. This applies to every page: User Guide, Examples and Mathematical Formulation.

Instead of:

> The `EnergySystem` class encapsulates the optimization workflow...

Write:

> Let's set up our first energy system.
>
> Now let's optimize it.
>
> Notice how the solver uses solar first because it's free?

Rules:

- Address the reader as "you". Treat the optimizer as a character: "the optimizer would happily…".
- Short sentences, one idea per paragraph.
- Say each symbol or field in words the first time it appears on a page.
- Use small concrete numbers when they help: "a battery that is 90 % efficient loses 0.1 MWh of every MWh it stores".
- Keep the tone light and warm, and the content exact: no jokes inside the math, and never trade precision for tone.
- No paper vocabulary: "hence", "w.l.o.g.", "it follows that", "we denote", "respectively", "the reader".

The landing page and README are the exception: outside the hero they stay plain and factual (§14).

## 14. Explain why Odys exists

The landing page should answer:

- What problem does Odys solve?
- What alternatives exist?
- Why is Odys different?
- Who is it for?
- Who is it not for?

Users appreciate honesty about scope and trade-offs.

Odys is a free, open-source tool for a technical audience. Outside the hero, write the landing page and README in a plain, factual register: say what Odys is and does, not what it promises. No audience personas.

## 15. End every page with the next step

Every page links forward. The reader never wonders where to go next. End with a bridge: one sentence that names the question the reader will have now, and links to the page that answers it. A bare "See X" is not enough.

Examples:

- End of `assets/generator.md`: "Next, see how [FixedLoad](fixed_load.md) defines the demand your system must serve."
- End of `concepts/scenario.md`: "See [Initial and final conditions](initial_and_final_conditions.md) to set where each asset starts and ends a run."
- End of an example: "This example used deterministic scenarios. The [CVaR Market Risk](../examples/cvar_market_risk.md) example adds risk-aware optimization."
- End of `formulation/generators.md`: "Power made now is used now, unless you can store it. See [Batteries](batteries.md)."

## 16. Visual consistency

Every asset and market page follows the same template, in this order:

1. Frontmatter with icon
2. Title
3. Short introduction (1-2 paragraphs)
4. Basic usage (runnable code)
5. Fields table, always with the columns Field | Type | Required | Default | Description
6. Feature sections, one concept each, with prose and code only. Each links to its constraints on the formulation page (`../../formulation/generators.md#g-7`).
7. Profiles (the `Scenario` time series the asset takes, if any)
8. Results (how to read the output)
9. How it's modelled: one or two sentences and links to the asset's formulation page and constraints
10. Next step bridge

Concept and optimization pages use a lighter version: introduction, usage, details, how it's modelled (if any), next steps. Skip a section only when it does not apply.

Formulation pages follow their own template (see [templates.md](templates.md)).

Readers quickly learn the pattern.

## 17. Cross-link aggressively

Pages are not read in isolation. Link to related pages wherever a concept is introduced:

- "The profile references a [Generator](../assets/generator.md) of your portfolio."
- "See [Stochastic optimization](../optimization/stochastic.md) for more details."
- "Market prices are specified in the [Scenario](../concepts/scenario.md), not on the market object."

Internal links are the connective tissue of the documentation.

## 18. Use documentation-driven development

If documenting something is awkward, the API may be awkward too.

A useful test: could I explain this API to someone in three lines of code?

If not, the API itself may need refinement.

## Information architecture

```
docs/
├── index.md                  # Landing page + quickstart
│
├── user_guide/               # Tutorials and concept pages
│   ├── index.md              # Overview: object diagram and reading order
│   ├── concepts/
│   │   ├── energy_system.md  # Main entry point
│   │   ├── asset_portfolio.md
│   │   ├── scenario.md       # Scenarios and profiles
│   │   ├── initial_and_final_conditions.md
│   │   └── power_balance.md  # The constraint that ties assets and markets together
│   ├── assets/               # One page per asset, all with the same template
│   │   ├── generator.md
│   │   ├── fixed_load.md
│   │   ├── flexible_load.md
│   │   ├── stationary_storage.md
│   │   ├── battery.md        # Battery physics shared by storage and EVs
│   │   ├── electric_vehicle.md
│   │   └── charger.md
│   ├── markets/
│   │   └── energy_market.md
│   └── optimization/
│       ├── objective.md      # Profit and CVaR
│       ├── results.md        # Reading results
│       ├── stochastic.md     # Stochastic optimization
│       └── solvers.md        # Solver choice and options
│
├── formulation/              # Mathematical Formulation: the exact MILP, one page per model part
│   ├── index.md              # Overview: problem size, assumptions, compact model
│   ├── notation.md           # Notation and conventions
│   ├── scenarios.md
│   ├── non_anticipativity.md
│   ├── objective.md
│   ├── power_balance.md
│   ├── markets.md
│   ├── generators.md
│   ├── batteries.md          # Shared by stationary storage and EVs
│   ├── electric_vehicles.md  # EVs and chargers
│   └── flexible_loads.md
│
├── examples/                 # End-to-end worked examples
│   ├── index.md
│   ├── basic_dispatch.md
│   ├── battery_dispatch.md
│   ├── flexible_load_market.md
│   ├── market_arbitrage.md
│   ├── cvar_market_risk.md
│   └── ev_fleet_optimization.md
│
└── developer/                # Developer Reference
    ├── index.md              # Overview and package layers
    ├── data_model.md         # Class diagrams (checked by tests/test_architecture_docs.py)
    ├── sequences.md          # optimize() sequence diagram
    └── api/                  # API reference, one page per module (mkdocstrings)
```

## Page templates

The asset page template and the formulation page template are in [templates.md](templates.md). Copy the matching one when you start a new page.
