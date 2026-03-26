@echo off
set PYTHONUTF8=1
pushd "%~dp0.."
python vak.py %*
popd
