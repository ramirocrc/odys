\ File written by HiGHS .lp file handler
max
 obj: -20 generator_power(deterministic_scenario,0,generator_1)#0 -25 generator_power(deterministic_scenario,0,generator_2)#1 -20 generator_power(deterministic_scenario,1,generator_1)#2 -25 generator_power(deterministic_scenario,1,generator_2)#3 -20 generator_power(deterministic_scenario,2,generator_1)#4 -25 generator_power(deterministic_scenario,2,generator_2)#5 -20 generator_power(deterministic_scenario,3,generator_1)#6 -25 generator_power(deterministic_scenario,3,generator_2)#7 -20 generator_power(deterministic_scenario,4,generator_1)#8 -25
 generator_power(deterministic_scenario,4,generator_2)#9
st
 generator_max_power_constraint(deterministic_scenario,0,generator_1)#0: +1 generator_power(deterministic_scenario,0,generator_1)#0 -100 generator_status(deterministic_scenario,0,generator_1)#10 <= -0
 generator_max_power_constraint(deterministic_scenario,0,generator_2)#1: +1 generator_power(deterministic_scenario,0,generator_2)#1 -150 generator_status(deterministic_scenario,0,generator_2)#11 <= -0
 generator_max_power_constraint(deterministic_scenario,1,generator_1)#2: +1 generator_power(deterministic_scenario,1,generator_1)#2 -100 generator_status(deterministic_scenario,1,generator_1)#12 <= -0
 generator_max_power_constraint(deterministic_scenario,1,generator_2)#3: +1 generator_power(deterministic_scenario,1,generator_2)#3 -150 generator_status(deterministic_scenario,1,generator_2)#13 <= -0
 generator_max_power_constraint(deterministic_scenario,2,generator_1)#4: +1 generator_power(deterministic_scenario,2,generator_1)#4 -100 generator_status(deterministic_scenario,2,generator_1)#14 <= -0
 generator_max_power_constraint(deterministic_scenario,2,generator_2)#5: +1 generator_power(deterministic_scenario,2,generator_2)#5 -150 generator_status(deterministic_scenario,2,generator_2)#15 <= -0
 generator_max_power_constraint(deterministic_scenario,3,generator_1)#6: +1 generator_power(deterministic_scenario,3,generator_1)#6 -100 generator_status(deterministic_scenario,3,generator_1)#16 <= -0
 generator_max_power_constraint(deterministic_scenario,3,generator_2)#7: +1 generator_power(deterministic_scenario,3,generator_2)#7 -150 generator_status(deterministic_scenario,3,generator_2)#17 <= -0
 generator_max_power_constraint(deterministic_scenario,4,generator_1)#8: +1 generator_power(deterministic_scenario,4,generator_1)#8 -100 generator_status(deterministic_scenario,4,generator_1)#18 <= -0
 generator_max_power_constraint(deterministic_scenario,4,generator_2)#9: +1 generator_power(deterministic_scenario,4,generator_2)#9 -150 generator_status(deterministic_scenario,4,generator_2)#19 <= -0
 generator_status_constraint(deterministic_scenario,0,generator_1)#10: +1 generator_power(deterministic_scenario,0,generator_1)#0 -0.001 generator_status(deterministic_scenario,0,generator_1)#10 >= -0
 generator_status_constraint(deterministic_scenario,0,generator_2)#11: +1 generator_power(deterministic_scenario,0,generator_2)#1 -0.0015 generator_status(deterministic_scenario,0,generator_2)#11 >= -0
 generator_status_constraint(deterministic_scenario,1,generator_1)#12: +1 generator_power(deterministic_scenario,1,generator_1)#2 -0.001 generator_status(deterministic_scenario,1,generator_1)#12 >= -0
 generator_status_constraint(deterministic_scenario,1,generator_2)#13: +1 generator_power(deterministic_scenario,1,generator_2)#3 -0.0015 generator_status(deterministic_scenario,1,generator_2)#13 >= -0
 generator_status_constraint(deterministic_scenario,2,generator_1)#14: +1 generator_power(deterministic_scenario,2,generator_1)#4 -0.001 generator_status(deterministic_scenario,2,generator_1)#14 >= -0
 generator_status_constraint(deterministic_scenario,2,generator_2)#15: +1 generator_power(deterministic_scenario,2,generator_2)#5 -0.0015 generator_status(deterministic_scenario,2,generator_2)#15 >= -0
 generator_status_constraint(deterministic_scenario,3,generator_1)#16: +1 generator_power(deterministic_scenario,3,generator_1)#6 -0.001 generator_status(deterministic_scenario,3,generator_1)#16 >= -0
 generator_status_constraint(deterministic_scenario,3,generator_2)#17: +1 generator_power(deterministic_scenario,3,generator_2)#7 -0.0015 generator_status(deterministic_scenario,3,generator_2)#17 >= -0
 generator_status_constraint(deterministic_scenario,4,generator_1)#18: +1 generator_power(deterministic_scenario,4,generator_1)#8 -0.001 generator_status(deterministic_scenario,4,generator_1)#18 >= -0
 generator_status_constraint(deterministic_scenario,4,generator_2)#19: +1 generator_power(deterministic_scenario,4,generator_2)#9 -0.0015 generator_status(deterministic_scenario,4,generator_2)#19 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,0,generator_1)#20: -1 generator_status(deterministic_scenario,0,generator_1)#10 +1 generator_startup(deterministic_scenario,0,generator_1)#20 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,0,generator_2)#21: -1 generator_status(deterministic_scenario,0,generator_2)#11 +1 generator_startup(deterministic_scenario,0,generator_2)#21 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,1,generator_1)#22: +1 generator_status(deterministic_scenario,0,generator_1)#10 -1 generator_status(deterministic_scenario,1,generator_1)#12 +1 generator_startup(deterministic_scenario,1,generator_1)#22 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,1,generator_2)#23: +1 generator_status(deterministic_scenario,0,generator_2)#11 -1 generator_status(deterministic_scenario,1,generator_2)#13 +1 generator_startup(deterministic_scenario,1,generator_2)#23 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,2,generator_1)#24: +1 generator_status(deterministic_scenario,1,generator_1)#12 -1 generator_status(deterministic_scenario,2,generator_1)#14 +1 generator_startup(deterministic_scenario,2,generator_1)#24 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,2,generator_2)#25: +1 generator_status(deterministic_scenario,1,generator_2)#13 -1 generator_status(deterministic_scenario,2,generator_2)#15 +1 generator_startup(deterministic_scenario,2,generator_2)#25 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,3,generator_1)#26: +1 generator_status(deterministic_scenario,2,generator_1)#14 -1 generator_status(deterministic_scenario,3,generator_1)#16 +1 generator_startup(deterministic_scenario,3,generator_1)#26 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,3,generator_2)#27: +1 generator_status(deterministic_scenario,2,generator_2)#15 -1 generator_status(deterministic_scenario,3,generator_2)#17 +1 generator_startup(deterministic_scenario,3,generator_2)#27 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,4,generator_1)#28: +1 generator_status(deterministic_scenario,3,generator_1)#16 -1 generator_status(deterministic_scenario,4,generator_1)#18 +1 generator_startup(deterministic_scenario,4,generator_1)#28 >= -0
 generator_startup_lower_bound_constraint(deterministic_scenario,4,generator_2)#29: +1 generator_status(deterministic_scenario,3,generator_2)#17 -1 generator_status(deterministic_scenario,4,generator_2)#19 +1 generator_startup(deterministic_scenario,4,generator_2)#29 >= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,0,generator_1)#30: -1 generator_status(deterministic_scenario,0,generator_1)#10 +1 generator_startup(deterministic_scenario,0,generator_1)#20 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,0,generator_2)#31: -1 generator_status(deterministic_scenario,0,generator_2)#11 +1 generator_startup(deterministic_scenario,0,generator_2)#21 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,1,generator_1)#32: -1 generator_status(deterministic_scenario,1,generator_1)#12 +1 generator_startup(deterministic_scenario,1,generator_1)#22 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,1,generator_2)#33: -1 generator_status(deterministic_scenario,1,generator_2)#13 +1 generator_startup(deterministic_scenario,1,generator_2)#23 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,2,generator_1)#34: -1 generator_status(deterministic_scenario,2,generator_1)#14 +1 generator_startup(deterministic_scenario,2,generator_1)#24 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,2,generator_2)#35: -1 generator_status(deterministic_scenario,2,generator_2)#15 +1 generator_startup(deterministic_scenario,2,generator_2)#25 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,3,generator_1)#36: -1 generator_status(deterministic_scenario,3,generator_1)#16 +1 generator_startup(deterministic_scenario,3,generator_1)#26 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,3,generator_2)#37: -1 generator_status(deterministic_scenario,3,generator_2)#17 +1 generator_startup(deterministic_scenario,3,generator_2)#27 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,4,generator_1)#38: -1 generator_status(deterministic_scenario,4,generator_1)#18 +1 generator_startup(deterministic_scenario,4,generator_1)#28 <= -0
 generator_startup_upper_bound_1_constraint(deterministic_scenario,4,generator_2)#39: -1 generator_status(deterministic_scenario,4,generator_2)#19 +1 generator_startup(deterministic_scenario,4,generator_2)#29 <= -0
 generator_startup_upper_bound_2_constraint(deterministic_scenario,0,generator_1)#40: +1 generator_startup(deterministic_scenario,0,generator_1)#20 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,0,generator_2)#41: +1 generator_startup(deterministic_scenario,0,generator_2)#21 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,1,generator_1)#42: +1 generator_status(deterministic_scenario,0,generator_1)#10 +1 generator_startup(deterministic_scenario,1,generator_1)#22 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,1,generator_2)#43: +1 generator_status(deterministic_scenario,0,generator_2)#11 +1 generator_startup(deterministic_scenario,1,generator_2)#23 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,2,generator_1)#44: +1 generator_status(deterministic_scenario,1,generator_1)#12 +1 generator_startup(deterministic_scenario,2,generator_1)#24 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,2,generator_2)#45: +1 generator_status(deterministic_scenario,1,generator_2)#13 +1 generator_startup(deterministic_scenario,2,generator_2)#25 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,3,generator_1)#46: +1 generator_status(deterministic_scenario,2,generator_1)#14 +1 generator_startup(deterministic_scenario,3,generator_1)#26 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,3,generator_2)#47: +1 generator_status(deterministic_scenario,2,generator_2)#15 +1 generator_startup(deterministic_scenario,3,generator_2)#27 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,4,generator_1)#48: +1 generator_status(deterministic_scenario,3,generator_1)#16 +1 generator_startup(deterministic_scenario,4,generator_1)#28 <= +1
 generator_startup_upper_bound_2_constraint(deterministic_scenario,4,generator_2)#49: +1 generator_status(deterministic_scenario,3,generator_2)#17 +1 generator_startup(deterministic_scenario,4,generator_2)#29 <= +1
 generator_shutdown_lower_bound_constraint(deterministic_scenario,0,generator_1)#50: +1 generator_status(deterministic_scenario,0,generator_1)#10 +1 generator_shutdown(deterministic_scenario,0,generator_1)#30 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,0,generator_2)#51: +1 generator_status(deterministic_scenario,0,generator_2)#11 +1 generator_shutdown(deterministic_scenario,0,generator_2)#31 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,1,generator_1)#52: -1 generator_status(deterministic_scenario,0,generator_1)#10 +1 generator_status(deterministic_scenario,1,generator_1)#12 +1 generator_shutdown(deterministic_scenario,1,generator_1)#32 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,1,generator_2)#53: -1 generator_status(deterministic_scenario,0,generator_2)#11 +1 generator_status(deterministic_scenario,1,generator_2)#13 +1 generator_shutdown(deterministic_scenario,1,generator_2)#33 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,2,generator_1)#54: -1 generator_status(deterministic_scenario,1,generator_1)#12 +1 generator_status(deterministic_scenario,2,generator_1)#14 +1 generator_shutdown(deterministic_scenario,2,generator_1)#34 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,2,generator_2)#55: -1 generator_status(deterministic_scenario,1,generator_2)#13 +1 generator_status(deterministic_scenario,2,generator_2)#15 +1 generator_shutdown(deterministic_scenario,2,generator_2)#35 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,3,generator_1)#56: -1 generator_status(deterministic_scenario,2,generator_1)#14 +1 generator_status(deterministic_scenario,3,generator_1)#16 +1 generator_shutdown(deterministic_scenario,3,generator_1)#36 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,3,generator_2)#57: -1 generator_status(deterministic_scenario,2,generator_2)#15 +1 generator_status(deterministic_scenario,3,generator_2)#17 +1 generator_shutdown(deterministic_scenario,3,generator_2)#37 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,4,generator_1)#58: -1 generator_status(deterministic_scenario,3,generator_1)#16 +1 generator_status(deterministic_scenario,4,generator_1)#18 +1 generator_shutdown(deterministic_scenario,4,generator_1)#38 >= -0
 generator_shutdown_lower_bound_constraint(deterministic_scenario,4,generator_2)#59: -1 generator_status(deterministic_scenario,3,generator_2)#17 +1 generator_status(deterministic_scenario,4,generator_2)#19 +1 generator_shutdown(deterministic_scenario,4,generator_2)#39 >= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,0,generator_1)#60: +1 generator_shutdown(deterministic_scenario,0,generator_1)#30 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,0,generator_2)#61: +1 generator_shutdown(deterministic_scenario,0,generator_2)#31 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,1,generator_1)#62: -1 generator_status(deterministic_scenario,0,generator_1)#10 +1 generator_shutdown(deterministic_scenario,1,generator_1)#32 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,1,generator_2)#63: -1 generator_status(deterministic_scenario,0,generator_2)#11 +1 generator_shutdown(deterministic_scenario,1,generator_2)#33 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,2,generator_1)#64: -1 generator_status(deterministic_scenario,1,generator_1)#12 +1 generator_shutdown(deterministic_scenario,2,generator_1)#34 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,2,generator_2)#65: -1 generator_status(deterministic_scenario,1,generator_2)#13 +1 generator_shutdown(deterministic_scenario,2,generator_2)#35 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,3,generator_1)#66: -1 generator_status(deterministic_scenario,2,generator_1)#14 +1 generator_shutdown(deterministic_scenario,3,generator_1)#36 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,3,generator_2)#67: -1 generator_status(deterministic_scenario,2,generator_2)#15 +1 generator_shutdown(deterministic_scenario,3,generator_2)#37 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,4,generator_1)#68: -1 generator_status(deterministic_scenario,3,generator_1)#16 +1 generator_shutdown(deterministic_scenario,4,generator_1)#38 <= -0
 generator_shutdown_upper_bound_1_constraint(deterministic_scenario,4,generator_2)#69: -1 generator_status(deterministic_scenario,3,generator_2)#17 +1 generator_shutdown(deterministic_scenario,4,generator_2)#39 <= -0
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,0,generator_1)#70: +1 generator_status(deterministic_scenario,0,generator_1)#10 +1 generator_shutdown(deterministic_scenario,0,generator_1)#30 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,0,generator_2)#71: +1 generator_status(deterministic_scenario,0,generator_2)#11 +1 generator_shutdown(deterministic_scenario,0,generator_2)#31 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,1,generator_1)#72: +1 generator_status(deterministic_scenario,1,generator_1)#12 +1 generator_shutdown(deterministic_scenario,1,generator_1)#32 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,1,generator_2)#73: +1 generator_status(deterministic_scenario,1,generator_2)#13 +1 generator_shutdown(deterministic_scenario,1,generator_2)#33 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,2,generator_1)#74: +1 generator_status(deterministic_scenario,2,generator_1)#14 +1 generator_shutdown(deterministic_scenario,2,generator_1)#34 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,2,generator_2)#75: +1 generator_status(deterministic_scenario,2,generator_2)#15 +1 generator_shutdown(deterministic_scenario,2,generator_2)#35 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,3,generator_1)#76: +1 generator_status(deterministic_scenario,3,generator_1)#16 +1 generator_shutdown(deterministic_scenario,3,generator_1)#36 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,3,generator_2)#77: +1 generator_status(deterministic_scenario,3,generator_2)#17 +1 generator_shutdown(deterministic_scenario,3,generator_2)#37 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,4,generator_1)#78: +1 generator_status(deterministic_scenario,4,generator_1)#18 +1 generator_shutdown(deterministic_scenario,4,generator_1)#38 <= +1
 generator_shutdown_upper_bound_2_constraint(deterministic_scenario,4,generator_2)#79: +1 generator_status(deterministic_scenario,4,generator_2)#19 +1 generator_shutdown(deterministic_scenario,4,generator_2)#39 <= +1
 generator_min_uptime_generator_1_constraint(deterministic_scenario,0)#80: +1 generator_status(deterministic_scenario,0,generator_1)#10 -1 generator_shutdown(deterministic_scenario,1,generator_1)#32 >= -0
 generator_min_uptime_generator_1_constraint(deterministic_scenario,1)#81: +1 generator_status(deterministic_scenario,1,generator_1)#12 -1 generator_shutdown(deterministic_scenario,2,generator_1)#34 >= -0
 generator_min_uptime_generator_1_constraint(deterministic_scenario,2)#82: +1 generator_status(deterministic_scenario,2,generator_1)#14 -1 generator_shutdown(deterministic_scenario,3,generator_1)#36 >= -0
 generator_min_uptime_generator_1_constraint(deterministic_scenario,3)#83: +1 generator_status(deterministic_scenario,3,generator_1)#16 -1 generator_shutdown(deterministic_scenario,4,generator_1)#38 >= -0
 generator_min_uptime_generator_1_constraint(deterministic_scenario,4)#84: +1 generator_status(deterministic_scenario,4,generator_1)#18 >= -0
 generator_min_uptime_generator_2_constraint(deterministic_scenario,0)#85: +1 generator_status(deterministic_scenario,0,generator_2)#11 -1 generator_shutdown(deterministic_scenario,1,generator_2)#33 >= -0
 generator_min_uptime_generator_2_constraint(deterministic_scenario,1)#86: +1 generator_status(deterministic_scenario,1,generator_2)#13 -1 generator_shutdown(deterministic_scenario,2,generator_2)#35 >= -0
 generator_min_uptime_generator_2_constraint(deterministic_scenario,2)#87: +1 generator_status(deterministic_scenario,2,generator_2)#15 -1 generator_shutdown(deterministic_scenario,3,generator_2)#37 >= -0
 generator_min_uptime_generator_2_constraint(deterministic_scenario,3)#88: +1 generator_status(deterministic_scenario,3,generator_2)#17 -1 generator_shutdown(deterministic_scenario,4,generator_2)#39 >= -0
 generator_min_uptime_generator_2_constraint(deterministic_scenario,4)#89: +1 generator_status(deterministic_scenario,4,generator_2)#19 >= -0
 generator_min_power_constraint(deterministic_scenario,0,generator_1)#90: +1 generator_power(deterministic_scenario,0,generator_1)#0 >= -0
 generator_min_power_constraint(deterministic_scenario,0,generator_2)#91: +1 generator_power(deterministic_scenario,0,generator_2)#1 >= -0
 generator_min_power_constraint(deterministic_scenario,1,generator_1)#92: +1 generator_power(deterministic_scenario,1,generator_1)#2 >= -0
 generator_min_power_constraint(deterministic_scenario,1,generator_2)#93: +1 generator_power(deterministic_scenario,1,generator_2)#3 >= -0
 generator_min_power_constraint(deterministic_scenario,2,generator_1)#94: +1 generator_power(deterministic_scenario,2,generator_1)#4 >= -0
 generator_min_power_constraint(deterministic_scenario,2,generator_2)#95: +1 generator_power(deterministic_scenario,2,generator_2)#5 >= -0
 generator_min_power_constraint(deterministic_scenario,3,generator_1)#96: +1 generator_power(deterministic_scenario,3,generator_1)#6 >= -0
 generator_min_power_constraint(deterministic_scenario,3,generator_2)#97: +1 generator_power(deterministic_scenario,3,generator_2)#7 >= -0
 generator_min_power_constraint(deterministic_scenario,4,generator_1)#98: +1 generator_power(deterministic_scenario,4,generator_1)#8 >= -0
 generator_min_power_constraint(deterministic_scenario,4,generator_2)#99: +1 generator_power(deterministic_scenario,4,generator_2)#9 >= -0
 generator_max_ramp_up_constraint(deterministic_scenario,0,generator_1)#100: +1 generator_power(deterministic_scenario,0,generator_1)#0 <= +100
 generator_max_ramp_up_constraint(deterministic_scenario,0,generator_2)#101: +1 generator_power(deterministic_scenario,0,generator_2)#1 <= +150
 generator_max_ramp_up_constraint(deterministic_scenario,1,generator_1)#102: -1 generator_power(deterministic_scenario,0,generator_1)#0 +1 generator_power(deterministic_scenario,1,generator_1)#2 <= +100
 generator_max_ramp_up_constraint(deterministic_scenario,1,generator_2)#103: -1 generator_power(deterministic_scenario,0,generator_2)#1 +1 generator_power(deterministic_scenario,1,generator_2)#3 <= +150
 generator_max_ramp_up_constraint(deterministic_scenario,2,generator_1)#104: -1 generator_power(deterministic_scenario,1,generator_1)#2 +1 generator_power(deterministic_scenario,2,generator_1)#4 <= +100
 generator_max_ramp_up_constraint(deterministic_scenario,2,generator_2)#105: -1 generator_power(deterministic_scenario,1,generator_2)#3 +1 generator_power(deterministic_scenario,2,generator_2)#5 <= +150
 generator_max_ramp_up_constraint(deterministic_scenario,3,generator_1)#106: -1 generator_power(deterministic_scenario,2,generator_1)#4 +1 generator_power(deterministic_scenario,3,generator_1)#6 <= +100
 generator_max_ramp_up_constraint(deterministic_scenario,3,generator_2)#107: -1 generator_power(deterministic_scenario,2,generator_2)#5 +1 generator_power(deterministic_scenario,3,generator_2)#7 <= +150
 generator_max_ramp_up_constraint(deterministic_scenario,4,generator_1)#108: -1 generator_power(deterministic_scenario,3,generator_1)#6 +1 generator_power(deterministic_scenario,4,generator_1)#8 <= +100
 generator_max_ramp_up_constraint(deterministic_scenario,4,generator_2)#109: -1 generator_power(deterministic_scenario,3,generator_2)#7 +1 generator_power(deterministic_scenario,4,generator_2)#9 <= +150
 generator_max_ramp_down_constraint(deterministic_scenario,0,generator_1)#110: -1 generator_power(deterministic_scenario,0,generator_1)#0 <= +100
 generator_max_ramp_down_constraint(deterministic_scenario,0,generator_2)#111: -1 generator_power(deterministic_scenario,0,generator_2)#1 <= +150
 generator_max_ramp_down_constraint(deterministic_scenario,1,generator_1)#112: +1 generator_power(deterministic_scenario,0,generator_1)#0 -1 generator_power(deterministic_scenario,1,generator_1)#2 <= +100
 generator_max_ramp_down_constraint(deterministic_scenario,1,generator_2)#113: +1 generator_power(deterministic_scenario,0,generator_2)#1 -1 generator_power(deterministic_scenario,1,generator_2)#3 <= +150
 generator_max_ramp_down_constraint(deterministic_scenario,2,generator_1)#114: +1 generator_power(deterministic_scenario,1,generator_1)#2 -1 generator_power(deterministic_scenario,2,generator_1)#4 <= +100
 generator_max_ramp_down_constraint(deterministic_scenario,2,generator_2)#115: +1 generator_power(deterministic_scenario,1,generator_2)#3 -1 generator_power(deterministic_scenario,2,generator_2)#5 <= +150
 generator_max_ramp_down_constraint(deterministic_scenario,3,generator_1)#116: +1 generator_power(deterministic_scenario,2,generator_1)#4 -1 generator_power(deterministic_scenario,3,generator_1)#6 <= +100
 generator_max_ramp_down_constraint(deterministic_scenario,3,generator_2)#117: +1 generator_power(deterministic_scenario,2,generator_2)#5 -1 generator_power(deterministic_scenario,3,generator_2)#7 <= +150
 generator_max_ramp_down_constraint(deterministic_scenario,4,generator_1)#118: +1 generator_power(deterministic_scenario,3,generator_1)#6 -1 generator_power(deterministic_scenario,4,generator_1)#8 <= +100
 generator_max_ramp_down_constraint(deterministic_scenario,4,generator_2)#119: +1 generator_power(deterministic_scenario,3,generator_2)#7 -1 generator_power(deterministic_scenario,4,generator_2)#9 <= +150
 battery_max_charge_constraint(deterministic_scenario,0,battery_1)#120: +1 battery_power_in(deterministic_scenario,0,battery_1)#40 -200 battery_charge_mode(deterministic_scenario,0,battery_1)#60 <= -0
 battery_max_charge_constraint(deterministic_scenario,1,battery_1)#121: +1 battery_power_in(deterministic_scenario,1,battery_1)#41 -200 battery_charge_mode(deterministic_scenario,1,battery_1)#61 <= -0
 battery_max_charge_constraint(deterministic_scenario,2,battery_1)#122: +1 battery_power_in(deterministic_scenario,2,battery_1)#42 -200 battery_charge_mode(deterministic_scenario,2,battery_1)#62 <= -0
 battery_max_charge_constraint(deterministic_scenario,3,battery_1)#123: +1 battery_power_in(deterministic_scenario,3,battery_1)#43 -200 battery_charge_mode(deterministic_scenario,3,battery_1)#63 <= -0
 battery_max_charge_constraint(deterministic_scenario,4,battery_1)#124: +1 battery_power_in(deterministic_scenario,4,battery_1)#44 -200 battery_charge_mode(deterministic_scenario,4,battery_1)#64 <= -0
 battery_max_discharge_constraint(deterministic_scenario,0,battery_1)#125: +1 battery_power_out(deterministic_scenario,0,battery_1)#50 +200 battery_charge_mode(deterministic_scenario,0,battery_1)#60 <= +200
 battery_max_discharge_constraint(deterministic_scenario,1,battery_1)#126: +1 battery_power_out(deterministic_scenario,1,battery_1)#51 +200 battery_charge_mode(deterministic_scenario,1,battery_1)#61 <= +200
 battery_max_discharge_constraint(deterministic_scenario,2,battery_1)#127: +1 battery_power_out(deterministic_scenario,2,battery_1)#52 +200 battery_charge_mode(deterministic_scenario,2,battery_1)#62 <= +200
 battery_max_discharge_constraint(deterministic_scenario,3,battery_1)#128: +1 battery_power_out(deterministic_scenario,3,battery_1)#53 +200 battery_charge_mode(deterministic_scenario,3,battery_1)#63 <= +200
 battery_max_discharge_constraint(deterministic_scenario,4,battery_1)#129: +1 battery_power_out(deterministic_scenario,4,battery_1)#54 +200 battery_charge_mode(deterministic_scenario,4,battery_1)#64 <= +200
 battery_soc_dynamics_constraint(deterministic_scenario,1,battery_1)#131: -1 battery_power_in(deterministic_scenario,1,battery_1)#41 +1 battery_power_out(deterministic_scenario,1,battery_1)#51 -1 battery_soc(deterministic_scenario,0,battery_1)#55 +1 battery_soc(deterministic_scenario,1,battery_1)#56 = -0
 battery_soc_dynamics_constraint(deterministic_scenario,2,battery_1)#132: -1 battery_power_in(deterministic_scenario,2,battery_1)#42 +1 battery_power_out(deterministic_scenario,2,battery_1)#52 -1 battery_soc(deterministic_scenario,1,battery_1)#56 +1 battery_soc(deterministic_scenario,2,battery_1)#57 = -0
 battery_soc_dynamics_constraint(deterministic_scenario,3,battery_1)#133: -1 battery_power_in(deterministic_scenario,3,battery_1)#43 +1 battery_power_out(deterministic_scenario,3,battery_1)#53 -1 battery_soc(deterministic_scenario,2,battery_1)#57 +1 battery_soc(deterministic_scenario,3,battery_1)#58 = -0
 battery_soc_dynamics_constraint(deterministic_scenario,4,battery_1)#134: -1 battery_power_in(deterministic_scenario,4,battery_1)#44 +1 battery_power_out(deterministic_scenario,4,battery_1)#54 -1 battery_soc(deterministic_scenario,3,battery_1)#58 +1 battery_soc(deterministic_scenario,4,battery_1)#59 = -0
 battery_soc_start_constraint(deterministic_scenario,battery_1)#135: -1 battery_power_in(deterministic_scenario,0,battery_1)#40 +1 battery_power_out(deterministic_scenario,0,battery_1)#50 +1 battery_soc(deterministic_scenario,0,battery_1)#55 = +100
 battery_soc_end_constraint(deterministic_scenario,battery_1)#136: +1 battery_soc(deterministic_scenario,4,battery_1)#59 = +50
 batter_soc_min_constraint(deterministic_scenario,0,battery_1)#137: +1 battery_soc(deterministic_scenario,0,battery_1)#55 >= -0
 batter_soc_min_constraint(deterministic_scenario,1,battery_1)#138: +1 battery_soc(deterministic_scenario,1,battery_1)#56 >= -0
 batter_soc_min_constraint(deterministic_scenario,2,battery_1)#139: +1 battery_soc(deterministic_scenario,2,battery_1)#57 >= -0
 batter_soc_min_constraint(deterministic_scenario,3,battery_1)#140: +1 battery_soc(deterministic_scenario,3,battery_1)#58 >= -0
 batter_soc_min_constraint(deterministic_scenario,4,battery_1)#141: +1 battery_soc(deterministic_scenario,4,battery_1)#59 >= -0
 batter_soc_max_constraint(deterministic_scenario,0,battery_1)#142: +1 battery_soc(deterministic_scenario,0,battery_1)#55 <= +100
 batter_soc_max_constraint(deterministic_scenario,1,battery_1)#143: +1 battery_soc(deterministic_scenario,1,battery_1)#56 <= +100
 batter_soc_max_constraint(deterministic_scenario,2,battery_1)#144: +1 battery_soc(deterministic_scenario,2,battery_1)#57 <= +100
 batter_soc_max_constraint(deterministic_scenario,3,battery_1)#145: +1 battery_soc(deterministic_scenario,3,battery_1)#58 <= +100
 batter_soc_max_constraint(deterministic_scenario,4,battery_1)#146: +1 battery_soc(deterministic_scenario,4,battery_1)#59 <= +100
 battery_capacity_constraint(deterministic_scenario,0,battery_1)#147: +1 battery_soc(deterministic_scenario,0,battery_1)#55 <= +100
 battery_capacity_constraint(deterministic_scenario,1,battery_1)#148: +1 battery_soc(deterministic_scenario,1,battery_1)#56 <= +100
 battery_capacity_constraint(deterministic_scenario,2,battery_1)#149: +1 battery_soc(deterministic_scenario,2,battery_1)#57 <= +100
 battery_capacity_constraint(deterministic_scenario,3,battery_1)#150: +1 battery_soc(deterministic_scenario,3,battery_1)#58 <= +100
 battery_capacity_constraint(deterministic_scenario,4,battery_1)#151: +1 battery_soc(deterministic_scenario,4,battery_1)#59 <= +100
 battery_net_power_constraint(deterministic_scenario,0,battery_1)#152: -1 battery_power_in(deterministic_scenario,0,battery_1)#40 +1 battery_net_power(deterministic_scenario,0,battery_1)#45 +1 battery_power_out(deterministic_scenario,0,battery_1)#50 = -0
 battery_net_power_constraint(deterministic_scenario,1,battery_1)#153: -1 battery_power_in(deterministic_scenario,1,battery_1)#41 +1 battery_net_power(deterministic_scenario,1,battery_1)#46 +1 battery_power_out(deterministic_scenario,1,battery_1)#51 = -0
 battery_net_power_constraint(deterministic_scenario,2,battery_1)#154: -1 battery_power_in(deterministic_scenario,2,battery_1)#42 +1 battery_net_power(deterministic_scenario,2,battery_1)#47 +1 battery_power_out(deterministic_scenario,2,battery_1)#52 = -0
 battery_net_power_constraint(deterministic_scenario,3,battery_1)#155: -1 battery_power_in(deterministic_scenario,3,battery_1)#43 +1 battery_net_power(deterministic_scenario,3,battery_1)#48 +1 battery_power_out(deterministic_scenario,3,battery_1)#53 = -0
 battery_net_power_constraint(deterministic_scenario,4,battery_1)#156: -1 battery_power_in(deterministic_scenario,4,battery_1)#44 +1 battery_net_power(deterministic_scenario,4,battery_1)#49 +1 battery_power_out(deterministic_scenario,4,battery_1)#54 = -0
 power_balance_constraint(deterministic_scenario,0,load_1)#157: +1 generator_power(deterministic_scenario,0,generator_1)#0 +1 generator_power(deterministic_scenario,0,generator_2)#1 -1 battery_power_in(deterministic_scenario,0,battery_1)#40 +1 battery_power_out(deterministic_scenario,0,battery_1)#50 = +50
 power_balance_constraint(deterministic_scenario,1,load_1)#158: +1 generator_power(deterministic_scenario,1,generator_1)#2 +1 generator_power(deterministic_scenario,1,generator_2)#3 -1 battery_power_in(deterministic_scenario,1,battery_1)#41 +1 battery_power_out(deterministic_scenario,1,battery_1)#51 = +75
 power_balance_constraint(deterministic_scenario,2,load_1)#159: +1 generator_power(deterministic_scenario,2,generator_1)#4 +1 generator_power(deterministic_scenario,2,generator_2)#5 -1 battery_power_in(deterministic_scenario,2,battery_1)#42 +1 battery_power_out(deterministic_scenario,2,battery_1)#52 = +100
 power_balance_constraint(deterministic_scenario,3,load_1)#160: +1 generator_power(deterministic_scenario,3,generator_1)#6 +1 generator_power(deterministic_scenario,3,generator_2)#7 -1 battery_power_in(deterministic_scenario,3,battery_1)#43 +1 battery_power_out(deterministic_scenario,3,battery_1)#53 = +125
 power_balance_constraint(deterministic_scenario,4,load_1)#161: +1 generator_power(deterministic_scenario,4,generator_1)#8 +1 generator_power(deterministic_scenario,4,generator_2)#9 -1 battery_power_in(deterministic_scenario,4,battery_1)#44 +1 battery_power_out(deterministic_scenario,4,battery_1)#54 = +150
bounds
 generator_status(deterministic_scenario,0,generator_1)#10 <= 1
 generator_status(deterministic_scenario,0,generator_2)#11 <= 1
 generator_status(deterministic_scenario,1,generator_1)#12 <= 1
 generator_status(deterministic_scenario,1,generator_2)#13 <= 1
 generator_status(deterministic_scenario,2,generator_1)#14 <= 1
 generator_status(deterministic_scenario,2,generator_2)#15 <= 1
 generator_status(deterministic_scenario,3,generator_1)#16 <= 1
 generator_status(deterministic_scenario,3,generator_2)#17 <= 1
 generator_status(deterministic_scenario,4,generator_1)#18 <= 1
 generator_status(deterministic_scenario,4,generator_2)#19 <= 1
 generator_startup(deterministic_scenario,0,generator_1)#20 <= 1
 generator_startup(deterministic_scenario,0,generator_2)#21 <= 1
 generator_startup(deterministic_scenario,1,generator_1)#22 <= 1
 generator_startup(deterministic_scenario,1,generator_2)#23 <= 1
 generator_startup(deterministic_scenario,2,generator_1)#24 <= 1
 generator_startup(deterministic_scenario,2,generator_2)#25 <= 1
 generator_startup(deterministic_scenario,3,generator_1)#26 <= 1
 generator_startup(deterministic_scenario,3,generator_2)#27 <= 1
 generator_startup(deterministic_scenario,4,generator_1)#28 <= 1
 generator_startup(deterministic_scenario,4,generator_2)#29 <= 1
 generator_shutdown(deterministic_scenario,0,generator_1)#30 <= 1
 generator_shutdown(deterministic_scenario,0,generator_2)#31 <= 1
 generator_shutdown(deterministic_scenario,1,generator_1)#32 <= 1
 generator_shutdown(deterministic_scenario,1,generator_2)#33 <= 1
 generator_shutdown(deterministic_scenario,2,generator_1)#34 <= 1
 generator_shutdown(deterministic_scenario,2,generator_2)#35 <= 1
 generator_shutdown(deterministic_scenario,3,generator_1)#36 <= 1
 generator_shutdown(deterministic_scenario,3,generator_2)#37 <= 1
 generator_shutdown(deterministic_scenario,4,generator_1)#38 <= 1
 generator_shutdown(deterministic_scenario,4,generator_2)#39 <= 1
 battery_net_power(deterministic_scenario,0,battery_1)#45 free
 battery_net_power(deterministic_scenario,1,battery_1)#46 free
 battery_net_power(deterministic_scenario,2,battery_1)#47 free
 battery_net_power(deterministic_scenario,3,battery_1)#48 free
 battery_net_power(deterministic_scenario,4,battery_1)#49 free
 battery_charge_mode(deterministic_scenario,0,battery_1)#60 <= 1
 battery_charge_mode(deterministic_scenario,1,battery_1)#61 <= 1
 battery_charge_mode(deterministic_scenario,2,battery_1)#62 <= 1
 battery_charge_mode(deterministic_scenario,3,battery_1)#63 <= 1
 battery_charge_mode(deterministic_scenario,4,battery_1)#64 <= 1
bin
 generator_status(deterministic_scenario,0,generator_1)#10
 generator_status(deterministic_scenario,0,generator_2)#11
 generator_status(deterministic_scenario,1,generator_1)#12
 generator_status(deterministic_scenario,1,generator_2)#13
 generator_status(deterministic_scenario,2,generator_1)#14
 generator_status(deterministic_scenario,2,generator_2)#15
 generator_status(deterministic_scenario,3,generator_1)#16
 generator_status(deterministic_scenario,3,generator_2)#17
 generator_status(deterministic_scenario,4,generator_1)#18
 generator_status(deterministic_scenario,4,generator_2)#19
 generator_startup(deterministic_scenario,0,generator_1)#20
 generator_startup(deterministic_scenario,0,generator_2)#21
 generator_startup(deterministic_scenario,1,generator_1)#22
 generator_startup(deterministic_scenario,1,generator_2)#23
 generator_startup(deterministic_scenario,2,generator_1)#24
 generator_startup(deterministic_scenario,2,generator_2)#25
 generator_startup(deterministic_scenario,3,generator_1)#26
 generator_startup(deterministic_scenario,3,generator_2)#27
 generator_startup(deterministic_scenario,4,generator_1)#28
 generator_startup(deterministic_scenario,4,generator_2)#29
 generator_shutdown(deterministic_scenario,0,generator_1)#30
 generator_shutdown(deterministic_scenario,0,generator_2)#31
 generator_shutdown(deterministic_scenario,1,generator_1)#32
 generator_shutdown(deterministic_scenario,1,generator_2)#33
 generator_shutdown(deterministic_scenario,2,generator_1)#34
 generator_shutdown(deterministic_scenario,2,generator_2)#35
 generator_shutdown(deterministic_scenario,3,generator_1)#36
 generator_shutdown(deterministic_scenario,3,generator_2)#37
 generator_shutdown(deterministic_scenario,4,generator_1)#38
 generator_shutdown(deterministic_scenario,4,generator_2)#39
 battery_charge_mode(deterministic_scenario,0,battery_1)#60
 battery_charge_mode(deterministic_scenario,1,battery_1)#61
 battery_charge_mode(deterministic_scenario,2,battery_1)#62
 battery_charge_mode(deterministic_scenario,3,battery_1)#63
 battery_charge_mode(deterministic_scenario,4,battery_1)#64
gen
semi
end
