# ADR 0001: Markets ownership

**Status:** accepted
**Date:** 2026-08-01
**Deciders:** maintainers (Phase 0 hygiene)

## Context

`EnergyMarket` is registered as an optimization asset type (`AssetRegistry.MARKET`) with
decision variables and constraints, but user configuration places markets on
`EnergySystem.markets`, not inside `AssetPortfolio`. Other assets live in the portfolio.

This split increases cognitive load and forces `EnergySystem` / parameter assembly to
treat markets as a special case.

## Decision

**Option B — MarketEnvironment sibling aggregate (documented status quo).**

Markets remain a first-class collection on `EnergySystem` (sibling of portfolio), not
portfolio members. Ubiquitous language: *portfolio = physical/operated assets;
markets = environment the system trades in*. The registry may still model markets
as dispatchable assets internally.

A structural rename to a dedicated `MarketEnvironment` type is optional later; no API
break in Phase 0.

## Consequences

### Positive

- Matches current public API; no breaking change
- Clear product language for docs and onboarding

### Negative

- Parameter assembly and builder keep a markets special path (entity source ≠ portfolio)

### Neutral

- Portfolio stays free of market entities

## Alternatives considered

1. **Option A — Markets in portfolio:** breaking API; blurs ownership vs environment
2. **Option C — Undocumented status quo:** rejected; must be intentional in ADRs
