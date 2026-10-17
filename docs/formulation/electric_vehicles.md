---
icon: lucide/car
---

# Electric vehicles and chargers

<!-- Hook: What changes when the battery leaves? -->

<!-- Scope: what EVs add to the battery model (trips, driving, departure SoC) and the chargers that connect them. Added for every ElectricVehicle and Charger (chargers if and only if EVs). Each constraint: plain sentence, equation (logical then MILP form for binaries), read aloud, why it looks like this, good to know, facts line (Added · Binds · Name). -->

## Sets and indices

## Variables

<!-- Battery variables from Batteries; a_{c,e,s,t} ∈ {0, 1}. -->

## Electric vehicles

### EV-1 · Trips drain the battery {#ev-1}

<!-- The trip term in B-3 and B-4: E^trip_{e,t} / E_e, spread evenly over the trip's steps. -->

### EV-2 · No charging on the road {#ev-2}

<!-- ev_driving_constraint. Redundant (#145). -->

### EV-3 · Enough charge before every trip {#ev-3}

<!-- ev_min_soc_departure_constraint, end of the step before departure; t = 0 covered by validation. -->

## Chargers

### CH-1 · A charger serves one vehicle at a time {#ch-1}

<!-- charger_one_ev_per_charger_constraint. -->

### CH-2 · A vehicle uses one charger at a time {#ch-2}

<!-- charger_one_charger_per_ev_constraint. -->

### CH-3 · No plugging in while driving {#ch-3}

<!-- charger_no_assignment_while_driving_constraint. -->

### CH-4 · Power flows only through a charger, up to its rating {#ch-4}

<!-- charger_power_limit_constraint, on p^ch + p^dis; charger efficiency unused; ChargerDispatch.power excludes V2G (#142). -->

## Power balance contribution

## Objective contribution

## Where to find each symbol in odys

<!-- Visible table: Symbol | Attribute | Type (Parameter, Variable, Result) | Unit -->

<!-- Bridge: Last piece: demand that can bend. → [Flexible loads](flexible_loads.md) -->

---

Implemented in [`odys.optimization.formulations.electric_vehicle`](../developer/api/optimization/formulations/electric_vehicle.md) and [`odys.optimization.formulations.charging`](../developer/api/optimization/formulations/charging.md).
