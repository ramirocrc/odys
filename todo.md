# Documentation

- [ ] Create documentation page
- [ ] Add user manual
- [ ] Add examples

# Input validation

- [ ] Add pydantic validators to single assets
- [ ] Add pydantic validators to AssetPortfolio
- [ ] Validate inputs in EnergyModel (e.g. load can be met by generation at all times)

# Test

- [ ] Test pydantic validators (check that they raise errors for invalid inputs)
- [ ] Test constraints
- [ ] Add tests for EnergyModel
  - [ ] Test for invalid inputs
  - [ ] Perform optimization with different inputs (e.g. only battery, only generation, combined) and validate optimal results

# Optimization

- [ ] Remove solver from EnergyModel
- [ ] Create optimization results class
- [ ] Create table with optimization results
- [ ] Assess if Pandas DataFrame is useful for optimization results
- [ ] Handle infeasible problems
- [ ] Provide detailed information on infeasible problems

# Model extension

- [ ] Evaluate other uses cases (e.g. optimze bids based on day-ahead price forecast)
- [ ] Add additional parameteres for assets (e.g. generator min_up_time, battery degradation_cost)
- [ ] Support for other assets (e.g. wind, hydro, solar pv)
