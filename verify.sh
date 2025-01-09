#!/bin/bash
# wichtig keine leerzeichen
# INSTANCES=displib_instances_testing/displib_testinstances_headway1.json
# INSTANCES=displib_instances_testing/displib_testinstances_swapping1.json
INSTANCES=displib_instances_testing/displib_testinstances_swapping2.json
# INSTANCES=displib_instances_phase1/line2_close_4.json
# INSTANCES=

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