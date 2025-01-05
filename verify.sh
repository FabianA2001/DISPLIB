#!/bin/bash

clear
echo -------------------------------------------------------------------
echo solver
echo -------------------------------------------------------------------
python3 src/main.py

echo  
echo  
echo -------------------------------------------------------------------
echo verify
echo -------------------------------------------------------------------
python3 displib_verify_v0_3/displib_verify.py displib_instances_testing/displib_testinstances_headway1.json solution.json