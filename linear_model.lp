min

obj:

+20 var_generator_power(0,generator_1)#0
+25 var_generator_power(0,generator_2)#1
+20 var_generator_power(1,generator_1)#2
+25 var_generator_power(1,generator_2)#3
+20 var_generator_power(2,generator_1)#4
+25 var_generator_power(2,generator_2)#5
+20 var_generator_power(3,generator_1)#6
+25 var_generator_power(3,generator_2)#7
+20 var_generator_power(4,generator_1)#8
+25 var_generator_power(4,generator_2)#9


s.t.

const_power_balance(0)#0:
+1 var_generator_power(0,generator_1)#0
+1 var_generator_power(0,generator_2)#1
-1 var_battery_charge(0,battery_1)#10
+1 var_battery_discharge(0,battery_1)#15
= +50

const_power_balance(1)#1:
+1 var_generator_power(1,generator_1)#2
+1 var_generator_power(1,generator_2)#3
-1 var_battery_charge(1,battery_1)#11
+1 var_battery_discharge(1,battery_1)#16
= +75

const_power_balance(2)#2:
+1 var_generator_power(2,generator_1)#4
+1 var_generator_power(2,generator_2)#5
-1 var_battery_charge(2,battery_1)#12
+1 var_battery_discharge(2,battery_1)#17
= +100

const_power_balance(3)#3:
+1 var_generator_power(3,generator_1)#6
+1 var_generator_power(3,generator_2)#7
-1 var_battery_charge(3,battery_1)#13
+1 var_battery_discharge(3,battery_1)#18
= +125

const_power_balance(4)#4:
+1 var_generator_power(4,generator_1)#8
+1 var_generator_power(4,generator_2)#9
-1 var_battery_charge(4,battery_1)#14
+1 var_battery_discharge(4,battery_1)#19
= +150
const_generator_limit(0,generator_1)#5:
+1 var_generator_power(0,generator_1)#0
<= +100

const_generator_limit(0,generator_2)#6:
+1 var_generator_power(0,generator_2)#1
<= +150

const_generator_limit(1,generator_1)#7:
+1 var_generator_power(1,generator_1)#2
<= +100

const_generator_limit(1,generator_2)#8:
+1 var_generator_power(1,generator_2)#3
<= +150

const_generator_limit(2,generator_1)#9:
+1 var_generator_power(2,generator_1)#4
<= +100

const_generator_limit(2,generator_2)#10:
+1 var_generator_power(2,generator_2)#5
<= +150

const_generator_limit(3,generator_1)#11:
+1 var_generator_power(3,generator_1)#6
<= +100

const_generator_limit(3,generator_2)#12:
+1 var_generator_power(3,generator_2)#7
<= +150

const_generator_limit(4,generator_1)#13:
+1 var_generator_power(4,generator_1)#8
<= +100

const_generator_limit(4,generator_2)#14:
+1 var_generator_power(4,generator_2)#9
<= +150
const_battery_charge_limit(0,battery_1)#15:
+1 var_battery_charge(0,battery_1)#10
-200 var_battery_charge_mode(0,battery_1)#25
<= -0

const_battery_charge_limit(1,battery_1)#16:
+1 var_battery_charge(1,battery_1)#11
-200 var_battery_charge_mode(1,battery_1)#26
<= -0

const_battery_charge_limit(2,battery_1)#17:
+1 var_battery_charge(2,battery_1)#12
-200 var_battery_charge_mode(2,battery_1)#27
<= -0

const_battery_charge_limit(3,battery_1)#18:
+1 var_battery_charge(3,battery_1)#13
-200 var_battery_charge_mode(3,battery_1)#28
<= -0

const_battery_charge_limit(4,battery_1)#19:
+1 var_battery_charge(4,battery_1)#14
-200 var_battery_charge_mode(4,battery_1)#29
<= -0
const_battery_discharge_limit(0,battery_1)#20:
+1 var_battery_discharge(0,battery_1)#15
+200 var_battery_charge_mode(0,battery_1)#25
<= +200

const_battery_discharge_limit(1,battery_1)#21:
+1 var_battery_discharge(1,battery_1)#16
+200 var_battery_charge_mode(1,battery_1)#26
<= +200

const_battery_discharge_limit(2,battery_1)#22:
+1 var_battery_discharge(2,battery_1)#17
+200 var_battery_charge_mode(2,battery_1)#27
<= +200

const_battery_discharge_limit(3,battery_1)#23:
+1 var_battery_discharge(3,battery_1)#18
+200 var_battery_charge_mode(3,battery_1)#28
<= +200

const_battery_discharge_limit(4,battery_1)#24:
+1 var_battery_discharge(4,battery_1)#19
+200 var_battery_charge_mode(4,battery_1)#29
<= +200
const_battery_soc_dynamics(1,battery_1)#26:
-1 var_battery_charge(1,battery_1)#11
+1 var_battery_discharge(1,battery_1)#16
-1 var_battery_soc(0,battery_1)#20
+1 var_battery_soc(1,battery_1)#21
= -0

const_battery_soc_dynamics(2,battery_1)#27:
-1 var_battery_charge(2,battery_1)#12
+1 var_battery_discharge(2,battery_1)#17
-1 var_battery_soc(1,battery_1)#21
+1 var_battery_soc(2,battery_1)#22
= -0

const_battery_soc_dynamics(3,battery_1)#28:
-1 var_battery_charge(3,battery_1)#13
+1 var_battery_discharge(3,battery_1)#18
-1 var_battery_soc(2,battery_1)#22
+1 var_battery_soc(3,battery_1)#23
= -0

const_battery_soc_dynamics(4,battery_1)#29:
-1 var_battery_charge(4,battery_1)#14
+1 var_battery_discharge(4,battery_1)#19
-1 var_battery_soc(3,battery_1)#23
+1 var_battery_soc(4,battery_1)#24
= -0
const_battery_soc_start(battery_1)#30:
-1 var_battery_charge(0,battery_1)#10
+1 var_battery_discharge(0,battery_1)#15
+1 var_battery_soc(0,battery_1)#20
= +100
const_battery_soc_bounds(0,battery_1)#31:
+1 var_battery_soc(0,battery_1)#20
<= +100

const_battery_soc_bounds(1,battery_1)#32:
+1 var_battery_soc(1,battery_1)#21
<= +100

const_battery_soc_bounds(2,battery_1)#33:
+1 var_battery_soc(2,battery_1)#22
<= +100

const_battery_soc_bounds(3,battery_1)#34:
+1 var_battery_soc(3,battery_1)#23
<= +100

const_battery_soc_bounds(4,battery_1)#35:
+1 var_battery_soc(4,battery_1)#24
<= +100
const_battery_soc_end(battery_1)#36:
+1 var_battery_soc(4,battery_1)#24
= +50


bounds

+0 <= var_generator_power(0,generator_1)#0 <= +inf
+0 <= var_generator_power(0,generator_2)#1 <= +inf
+0 <= var_generator_power(1,generator_1)#2 <= +inf
+0 <= var_generator_power(1,generator_2)#3 <= +inf
+0 <= var_generator_power(2,generator_1)#4 <= +inf
+0 <= var_generator_power(2,generator_2)#5 <= +inf
+0 <= var_generator_power(3,generator_1)#6 <= +inf
+0 <= var_generator_power(3,generator_2)#7 <= +inf
+0 <= var_generator_power(4,generator_1)#8 <= +inf
+0 <= var_generator_power(4,generator_2)#9 <= +inf
+0 <= var_battery_charge(0,battery_1)#10 <= +inf
+0 <= var_battery_charge(1,battery_1)#11 <= +inf
+0 <= var_battery_charge(2,battery_1)#12 <= +inf
+0 <= var_battery_charge(3,battery_1)#13 <= +inf
+0 <= var_battery_charge(4,battery_1)#14 <= +inf
+0 <= var_battery_discharge(0,battery_1)#15 <= +inf
+0 <= var_battery_discharge(1,battery_1)#16 <= +inf
+0 <= var_battery_discharge(2,battery_1)#17 <= +inf
+0 <= var_battery_discharge(3,battery_1)#18 <= +inf
+0 <= var_battery_discharge(4,battery_1)#19 <= +inf
+0 <= var_battery_soc(0,battery_1)#20 <= +inf
+0 <= var_battery_soc(1,battery_1)#21 <= +inf
+0 <= var_battery_soc(2,battery_1)#22 <= +inf
+0 <= var_battery_soc(3,battery_1)#23 <= +inf
+0 <= var_battery_soc(4,battery_1)#24 <= +inf


binary

var_battery_charge_mode(0,battery_1)#25
var_battery_charge_mode(1,battery_1)#26
var_battery_charge_mode(2,battery_1)#27
var_battery_charge_mode(3,battery_1)#28
var_battery_charge_mode(4,battery_1)#29
end
