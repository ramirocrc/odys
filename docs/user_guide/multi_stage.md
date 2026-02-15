# Multi-stage Optimization

!!! note "Coming soon"

    Multi-stage optimization is planned but not yet implemented. This page describes the concept for context.

## What is multi-stage optimization?

In [stochastic optimization](stochastic.md), you make decisions considering multiple scenarios, but all decisions are made at once (two-stage: decide now, then observe uncertainty).

Multi-stage optimization extends this to a sequence of decision points over time. At each stage, you observe new information and can adjust your decisions accordingly. This models real-world operations more closely -- for example, you might bid in the day-ahead market today, then adjust in the intraday market tomorrow once you have better forecasts.

## How it relates to `stage_fixed`

The `stage_fixed` parameter on `EnergyMarket` is a first step toward multi-stage behavior. Markets with `stage_fixed=True` represent earlier decision stages where you commit before uncertainty is resolved. Markets without it represent later stages where you can react to the realized scenario.

When full multi-stage support arrives, you'll be able to define an explicit sequence of stages, each with its own information set and decision variables.

## Stay tuned

Follow the [GitHub repository](https://github.com/ramirocrc/odys) for updates on this feature.
