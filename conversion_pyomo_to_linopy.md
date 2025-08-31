The Transport Problem
Summary
The goal of the Transport Problem is to select the quantities of a homogeneous good that has several production plants and several punctiform markets as to minimise the transportation costs.

It is the default tutorial for the GAMS language, and GAMS equivalent code is inserted as single-dash comments. The original GAMS code needs slighly different ordering of the commands and it’s available at http://www.gams.com/mccarl/trnsport.gms. The Pyomo version of the tutorial can be found at https://nbviewer.org/github/Pyomo/PyomoGallery/blob/master/transport/transport.ipynb.

For comparison, the variable names have been kept the same, though they are not pythonic. The equivalent GAMS code is included at the top of each cell as comments, while the Pyomo-equivalent is stated as text comments below.

Problem Statement
The Transport Problem can be formulated mathematically as a linear programming problem using the following model.

Sets
= set of canning plants
= set of markets
Parameters
= capacity of plant
in cases,

= demand at market
in cases,

= distance in thousands of miles,

= freight in dollars per case per thousand miles
= transport cost in thousands of dollars per case

is obtained exougenously to the optimisation problem as
,

Variables
= shipment quantities in cases z = total transportation costs in thousands of dollars

Objective
Minimize the total cost of the shipments:

Constraints
Observe supply limit at plant i:
,

Satisfy demand at market j:
,

Non-negative transportation quantities
,

Linopy Formulation
Creation of the Model
In linopy, modeling is based on a central model object. While this object contains variables, constraints, expressions, and the objective function as attributes, it does not currently contain fixed data like sets and parameters. Thus, they have been defined separately. Since linopy is built heavily on xarray’s data structure, using xarray for that is convenient.

The first thing to do in the tutorial is to load the linopy and related libraries and create a new model object. We have little imagination here, and we call our model m. You can give it whatever name you want. However, if you give your model an other name, you also need to change all references to it throughout this tutorial.

# Import of linopy and related modules

import xarray as xr

import linopy

# Creation of a Model

m = linopy.Model()
Equivalent in Pyomo

from pyomo.environ import \*

model = ConcreteModel()
Set Definitions
Sets can be created as xarray.DataArrays, where they require data in any form that numpy.ndarray could work with but can be provided additional data such as the name of the array, the names of its dimensions, or coordinates. Coordinates enable accessing data based on labels and aligning data. Since we want the sets i and j to function as coordinates later on, we only specify the name of their dimension here. Due to xarray’s flexibility, we can also define our coordinates as usual dictionaries, where the keys correspond to the names of the dimensions:

## Define sets

# Sets

# i canning plants / seattle, san-diego /

# j markets / new-york, chicago, topeka / ;

i = {"Canning Plants": ["seattle", "san-diego"]}
j = {"Markets": ["new-york", "chicago", "topeka"]}
Equivalent in Pyomo

model.i = Set(initialize=['seattle','san-diego'], doc='Canning plans')
model.j = Set(initialize=['new-york','chicago', 'topeka'], doc='Markets')
Parameters
Parameter objects are created as xarray.DataArrays and do specify over which sets they are created using coordinates. Since we set up i and j properly before, e.g. the supply a will automatically contain the dimension "Canning Plants" with the labels "seattle" and "san-diego" and can be accessed accordingly. This also works for multi-dimensional data such as the distance in thousands of miles d, where the dimension names are inferred again from the coordinates’ dimension names. Note, though, that xarray would prefer explicit statements of the form coords = [(dimension_name, data), ... ].

For the scalar parameter f, we simply define an integer variable.

## Define parameters

# Parameters

# a(i) capacity of plant i in cases

# / seattle 350

# san-diego 600 /

# b(j) demand at market j in cases

# / new-york 325

# chicago 300

# topeka 275 / ;

# Table d(i,j) distance in thousands of miles

# new-york chicago topeka

# seattle 2.5 1.7 1.8

# san-diego 2.5 1.8 1.4 ;

# Scalar f freight in dollars per case per thousand miles /90/ ;

a = xr.DataArray([350, 600], coords=i, name="capacity of plant i in cases")
b = xr.DataArray([325, 300, 275], coords=j, name="demand at market j in cases")

d = xr.DataArray(
[[2.5, 1.7, 1.8], [2.5, 1.8, 1.4]],
coords=i | j,
name="distance in thousands of miles",
)

f = 90 # Freight in dollars per case per thousand miles

# Access data using e.g.:

# a.loc[{"Canning Plants":"seattle"}]

# d.loc[{"Canning Plants":"seattle", "Markets":"new-york"}]

Equivalent in Pyomo

model.a = Param(model.i, initialize={'seattle':350,'san-diego':600}, doc='Capacity of plant i in cases')
model.b = Param(model.j, initialize={'new-york':325,'chicago':300,'topeka':275}, doc='Demand at market j in cases')

dtab = {
('seattle', 'new-york') : 2.5,
('seattle', 'chicago') : 1.7,
('seattle', 'topeka') : 1.8,
('san-diego','new-york') : 2.5,
('san-diego','chicago') : 1.8,
('san-diego','topeka') : 1.4,
}
model.d = Param(model.i, model.j, initialize=dtab, doc='Distance in thousands of miles')

model.f = Param(initialize=90, doc='Freight in dollars per case per thousand miles')
Working with xarrays enables us to get the resulting transport cost in thousands of dollars per case much simpler than in Pyomo:

# Parameter c(i,j) transport cost in thousands of dollars per case ;

# c(i,j) = f \* d(i,j) / 1000 ;

c = d \* f / 1000
c.name = "transport cost in thousands of dollars per case"
Equivalent in Pyomo

def c_init(model, i, j):
return model.f \* model.d[i,j] / 1000
model.c = Param(model.i, model.j, initialize=c_init, doc='Transport cost in thousands of dollar per case')
Variables
Variables are created as model attributes. They get can get lower or upper bounds, a name, and the coordinates (and inferred dimensions) for which they are defined.

Differently from GAMS, we do not need to define the variable that is on the left-hand side of the objective function.

## Define variables

# Variables

# x(i,j) shipment quantities in cases

# z total transportation costs in thousands of dollars ;

# Positive Variable x ;

x = m.add_variables(lower=0.0, coords=c.coords, name="Shipment quantities in cases")

# Inspect the variable by simply printing it:

# print(x)

Equivalent in Pyomo

model.x = Var(model.i, model.j, bounds=(0.0,None), doc='Shipment quantities in case')
Constraints
Constraints are also defined as model attributes. Before assigning them to the model, though, it is very useful to check that they take the form we desire. Here, we make use of xarray’s .sum() functionality, for which we can specify the dimensions that should be summed over:

x.sum(dim="Markets") <= a
Constraint (unassigned) [Canning Plants: 2]:

---

[seattle]: +1 Shipment quantities in cases[seattle, new-york] + 1 Shipment quantities in cases[seattle, chicago] + 1 Shipment quantities in cases[seattle, topeka] ≤ 350.0
[san-diego]: +1 Shipment quantities in cases[san-diego, new-york] + 1 Shipment quantities in cases[san-diego, chicago] + 1 Shipment quantities in cases[san-diego, topeka] ≤ 600.0
The output nicely confirms that this is indeed the constraint we want to implement, so we add it to the model:

## Define contraints

# supply(i) observe supply limit at plant i

# supply(i) .. sum (j, x(i,j)) =l= a(i)

# demand(j) satisfy demand at market j ;

# demand(j) .. sum(i, x(i,j)) =g= b(j);

con = x.sum(dim="Markets") <= a
con1 = m.add_constraints(con, name="Observe supply limit at plant i")

con = x.sum(dim="Canning Plants") >= b
con2 = m.add_constraints(con, name="Satisfy demand at market j")
Equivalent in Pyomo

def supply_rule(model, i):
return sum(model.x[i,j] for j in model.j) <= model.a[i]
model.supply = Constraint(model.i, rule=supply_rule, doc='Observe supply limit at plant i')

def demand_rule(model, j):
return sum(model.x[i,j] for i in model.i) >= model.b[j]
model.demand = Constraint(model.j, rule=demand_rule, doc='Satisfy demand at market j')
Objective and Solving
The definition of the objective is similar to those of the constraints, but the objective function is limited to a linopy.LinearExpression. While new expressions can be created, we can rely on existing functionality for the purposes of this tutorial. By defining an arithmetic operation with our linopy.Variable, a linopy.LinearExpression is automatically created. Linopy assumes only one objective function, so it automatically takes the full sum of that expression.

## Define Objective and solve

# cost define objective function

# cost .. z =e= sum((i,j), c(i,j)\*x(i,j)) ;

# Model transport /all/ ;

# Solve transport using lp minimizing z ;

obj = c \* x
m.add_objective(obj)
Equivalent in Pyomo

def objective_rule(model):
return sum(model.c[i,j]\*model.x[i,j] for i in model.i for j in model.j)
model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')
A range of solvers can be used for linopy. You can check which solvers are available using:

print(linopy.available_solvers)
['gurobi']
In the solve() function, you can specify a solver_name. The default solver, however, will be the first from the list we printed above.

# Solve the model

m.solve()
Restricted license - for non-production use only - expires 2025-11-24
Read LP format model from file /tmp/linopy-problem-ybapptbr.lp
Reading time = 0.00 seconds
obj: 5 rows, 6 columns, 12 nonzeros
Gurobi Optimizer version 11.0.2 build v11.0.2rc0 (linux64 - "Ubuntu 24.04 LTS")

CPU model: AMD EPYC 9R14, instruction set [SSE2|AVX|AVX2|AVX512]
Thread count: 2 physical cores, 2 logical processors, using up to 2 threads

Optimize a model with 5 rows, 6 columns and 12 nonzeros
Model fingerprint: 0xcf2a7643
Coefficient statistics:
Matrix range [1e+00, 1e+00]
Objective range [1e-01, 2e-01]
Bounds range [0e+00, 0e+00]
RHS range [3e+02, 6e+02]
Presolve time: 0.00s
Presolved: 5 rows, 6 columns, 12 nonzeros

Iteration Objective Primal Inf. Dual Inf. Time
0 0.0000000e+00 9.000000e+02 0.000000e+00 0s
4 1.5367500e+02 0.000000e+00 0.000000e+00 0s

Solved in 4 iterations and 0.00 seconds (0.00 work units)
Optimal objective 1.536750000e+02
('ok', 'optimal')
So the total costs are $153.675. We can also study the solutions for the variables added to the model:

## Display of the output

# Display x.l, x.m ;

# Display solution for variable x

x.solution
xarray.DataArray'solution'Canning Plants: 2Markets: 3

array([[50., 300.,   0.],
       [275.,   0., 275.]])

Coordinates:
Canning Plants
(Canning Plants)
<U9
'seattle' 'san-diego'

Markets
(Markets)
<U8
'new-york' 'chicago' 'topeka'

Indexes: (2)

Attributes: (0)
This way, we see that the lowest costs are obtained by sending 300 cases from the Seattle plant to the Chicago market, 325 cases from the San-Diego plant to the New-York market, and 275 cases from San-Diego to Topeka. Since the transportation costs between Seattle and New-York and San-Diego and New-York are equal, the model might also supply New-York with up to 50 cases from Seattle (which is limited to a production of 350 cases) and, consequently, as little as 275 cases from San-Diego.

Note that x.solution is an xarray.DataArray again, so we can call functions like to_dataframe() on it to retrieve a pandas.DataFrame, which then provides a convenient plot() function. Since all of this is happening in Python, there is no shortage of ways to visualize the solution.

Equivalent in Pyomo

The Pyomo version of this tutorial defines an auxiliary function to print the full solution to the variable x. Note also that glpk is the solver used in that tutorial, but you are free to choose a different solver.

def pyomo_postprocess(options=None, instance=None, results=None):
model.x.display()

from pyomo.opt import SolverFactory

opt = SolverFactory("glpk")
results = opt.solve(model)

# Sends results to stdout

results.write()
print("\nDisplaying Solution\n" + '-'\*60)
pyomo_postprocess(None, model, results)
