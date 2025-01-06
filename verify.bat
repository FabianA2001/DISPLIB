@echo off
set INSTANCES=displib_instances_testing\displib_testinstances_headway1.json

cls
echo -------------------------------------------------------------------
echo solver
echo -------------------------------------------------------------------
python src\main.py %INSTANCES%

echo.
echo.
echo -------------------------------------------------------------------
echo verify
echo -------------------------------------------------------------------
python displib_verify_v0_3\displib_verify.py %INSTANCES% solution.json
