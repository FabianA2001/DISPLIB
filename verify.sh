#!/bin/bash

echo -------------------------------------------------------------------
echo solver
echo -------------------------------------------------------------------
python src/main.py

echo  
echo  
echo -------------------------------------------------------------------
echo verify
echo -------------------------------------------------------------------
python displib_verify_v0_3/displib_verify.py displib_instances_testing/displib_testinstances_headway1.json solution.json