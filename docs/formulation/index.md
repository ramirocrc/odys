---
icon: lucide/sigma
---

# Mathematical formulation

<!-- Hook: What does odys actually solve? Open in everyday words: you own a few assets, you can trade on a few markets, and you don't know exactly what tomorrow brings. What should each asset do at every step? -->

<!-- Scope: what this section is (the exact MILP odys builds), who it is for (modelers auditing assumptions and interpreting results), how to read it (Overview first, Notation & conventions as reference, then one page per model part). -->

## The problem in one picture

<!-- Assets and markets around a single bus; the arrows are the power balance terms. -->

## How to read this section

<!-- A short tour paragraph following the storyline: notation, scenarios, objective, power balance, then each asset. One link per page. -->

## Problem class and size

<!-- MILP, maximized. Binaries with counts in |S|, |T| and the asset sets: generator u, y^start, y^stop (fixed exactly by u); battery mode z; market trade mode (#140); charger assignment a. CVaR adds only continuous variables. -->

## What odys assumes (and what it doesn't)

<!-- One bullet per assumption, each linking to the constraint that implements it (see formulation-design.md, "Modelling assumptions"). -->

## Checked before solving

<!-- Properties that hold because EnergySystem rejects inputs, with the validator that enforces each (see formulation-design.md). -->

## The whole model on one screen

<!-- max (objective) s.t. (PB-1), (M-…), (NA-1), (G-…), (B-…), (EV-…), (CH-…), (FL-…), (CV-1), x ∈ X. Every reference links to its anchor. -->

<!-- Bridge: Before the equations, a few words on how we write them. → [Notation and conventions](notation.md) -->
