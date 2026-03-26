@echo off
set PYTHONUTF8=1
pushd "%~dp0.."
python master_test.py
popd
pause
