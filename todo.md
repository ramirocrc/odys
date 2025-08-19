# Documentation

- [x] Create documentation page
- [ ] Add user manual
- [ ] Add examples

# Input validation

- [x] Add pydantic validators to single assets
- [x] Add pydantic validators to AssetPortfolio
- [x] Validate inputs in ValidatedEnergySystem (e.g. load can be met by generation at all times)

# Test

- [x] Test pydantic validators (check that they raise errors for invalid inputs)
- [x] Test constraints
- [x] Add tests for ValidatedEnergySystem and EnergySystem
  - [x] Test for invalid inputs
  - [x] Perform optimization with different inputs (e.g. only battery, only generation, combined) and validate optimal results

# Optimization

- [x] Remove solver from EnergySystem
- [x] Create optimization results class
- [x] Once result output is defined, we should make EnergySystem.algebraic_model private (don't give access to algebraic_model to user)
- [x] Create table with optimization results
- [x] Assess if Pandas DataFrame is useful for optimization results
- [ ] Handle infeasible problems
- [ ] Provide detailed information on infeasible problems

# Model extension

- [ ] Review time step implementation
  - [ ] Review power balance
  - [ ] Review ValidatedEnergySystem.\_validate_inputs
- [ ] Add "GridConnection" asset
- [ ] Evaluate other uses cases (e.g. optimze bids based on day-ahead price forecast)
- [ ] Add additional parameteres for assets (e.g. generator min_up_time, battery degradation_cost)
- [ ] Support for other assets (e.g. wind, hydro, solar pv)
- [ ] Implement cusomt Exceptions

# Codebase refactoring

- [x] Move Scenario specific configuration (e.g. battery soc_initial soc_terminal to EnergySystem class)
- [ ] Check how other libraries implement logging
