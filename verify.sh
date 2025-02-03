#!/bin/bash
# wichtig keine leerzeichen
INSTANCES=displib_instances_testing/displib_testinstances_headway1.json
# INSTANCES=displib_instances_testing/displib_testinstances_swapping1.json
# INSTANCES=displib_instances_testing/displib_testinstances_swapping2.json
# INSTANCES=displib_instances_phase1/line1_critical_0.json
# INSTANCES=displib_instances_phase1/line1_critical_1.json
# INSTANCES=displib_instances_phase1/line1_critical_2.json
# INSTANCES=displib_instances_phase1/line1_critical_3.json
# INSTANCES=displib_instances_phase1/line1_critical_4.json
# INSTANCES=displib_instances_phase1/line1_critical_5.json
# INSTANCES=displib_instances_phase1/line1_critical_6.json
# INSTANCES=displib_instances_phase1/line1_critical_7.json
# INSTANCES=displib_instances_phase1/line1_critical_8.json
# INSTANCES=displib_instances_phase1/line1_critical_9.json
# INSTANCES=displib_instances_phase1/line1_full_0.json
# INSTANCES=displib_instances_phase1/line1_full_1.json
# INSTANCES=displib_instances_phase1/line1_full_2.json
# INSTANCES=displib_instances_phase1/line1_full_3.json
# INSTANCES=displib_instances_phase1/line1_full_4.json
# INSTANCES=displib_instances_phase1/line1_full_5.json
# INSTANCES=displib_instances_phase1/line1_full_6.json
# INSTANCES=displib_instances_phase1/line1_full_7.json
# INSTANCES=displib_instances_phase1/line1_full_8.json
# INSTANCES=displib_instances_phase1/line1_full_9.json
# INSTANCES=displib_instances_phase1/line2_close_0.json
# INSTANCES=displib_instances_phase1/line2_close_1.json
# INSTANCES=displib_instances_phase1/line2_close_2.json
# INSTANCES=displib_instances_phase1/line2_close_3.json
# INSTANCES=displib_instances_phase1/line2_close_4.json
# INSTANCES=displib_instances_phase1/line2_close_5.json
# INSTANCES=displib_instances_phase1/line2_close_6.json
# INSTANCES=displib_instances_phase1/line2_close_7.json
# INSTANCES=displib_instances_phase1/line2_close_8.json
# INSTANCES=displib_instances_phase1/line2_headway_0.json
# INSTANCES=displib_instances_phase1/line2_headway_1.json
# INSTANCES=displib_instances_phase1/line2_headway_2.json
# INSTANCES=displib_instances_phase1/line2_headway_3.json
# INSTANCES=displib_instances_phase1/line2_headway_4.json
# INSTANCES=displib_instances_phase1/line2_headway_5.json
# INSTANCES=displib_instances_phase1/line2_headway_6.json
# INSTANCES=displib_instances_phase1/line2_headway_7.json
# INSTANCES=displib_instances_phase1/line3_1.json
# INSTANCES=displib_instances_phase1/line3_2.json
# INSTANCES=displib_instances_phase1/line3_3.json
# INSTANCES=displib_instances_phase1/line3_4.json
# INSTANCES=displib_instances_phase1/line3_5.json

clear
echo -------------------------------------------------------------------
echo solver
echo -------------------------------------------------------------------
python3 src/main.py $INSTANCES

echo  
echo  
echo -------------------------------------------------------------------
echo verify
echo -------------------------------------------------------------------
python3 displib_verify_v0_3/displib_verify.py $INSTANCES solution.json