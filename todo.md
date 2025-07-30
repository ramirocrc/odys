# Documentation

- [ ] Create documentation page
- [ ] Add user manual
- [ ] Add examples

# Input validation

- [x] Add pydantic validators to single assets
- [x] Add pydantic validators to AssetPortfolio
- [x] Validate inputs in EnergyModel (e.g. load can be met by generation at all times)

# Test

- [ ] Test pydantic validators (check that they raise errors for invalid inputs)
- [ ] Test constraints
- [ ] Add tests for EnergyModel
  - [ ] Test for invalid inputs
  - [ ] Perform optimization with different inputs (e.g. only battery, only generation, combined) and validate optimal results

# Optimization

- [ ] Remove solver from EnergyModel
- [ ] Create optimization results class
- [ ] Once result output is defined, we should make EnergyModelOptimizer.algebraic_model private (don't give access to algebraic_model to user)
- [ ] Create table with optimization results
- [ ] Assess if Pandas DataFrame is useful for optimization results
- [ ] Handle infeasible problems
- [ ] Provide detailed information on infeasible problems

# Model extension

- [ ] Review time step implementation
  - [ ] Review power balance
  - [ ] Review EnergyModel.\_validate_input
- [ ] Evaluate other uses cases (e.g. optimze bids based on day-ahead price forecast)
- [ ] Add additional parameteres for assets (e.g. generator min_up_time, battery degradation_cost)
- [ ] Support for other assets (e.g. wind, hydro, solar pv)
- [ ] Implement cusomt Exceptions

# Codebase refactoring

- [ ] Move Scenario specific configuration (e.g. battery soc_initial soc_terminal to EnergySystem class)
