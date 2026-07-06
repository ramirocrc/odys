# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-05

### Added

- CVaR (Conditional Value at Risk) support for stochastic optimization
- Lower bound validation (`ge=0`) on `ObjectiveTerm.weight`

### Changed

- Restructured codebase into layered architecture
- Refactored results API
- Refactored objective definition
- Added `slots` and pydantic `frozen` configuration to data models
- Improved docstrings across market, load, scenario, and objective classes
- Migrated documentation from MkDocs to Zensical
- Fixed storage timedelta constraints

### Removed

- Removed load results from results API

## [0.1.2] - 2025-01-01

### Added

- Multi-stage optimization
- Energy market integration with buy/sell/both trade directions

### Changed

- Improved validation error messages

## [0.1.1] - 2024-12-01

### Added

- Stochastic optimization with multiple scenarios
- Storage (battery) assets with charge/discharge constraints
- Available capacity profiles for generators

## [0.1.0] - 2024-11-01

### Added

- Initial release
- Energy system modeling with generators, loads, and storage
- MILP optimization using HiGHS solver
- Pydantic-based input validation
- Basic examples and documentation
