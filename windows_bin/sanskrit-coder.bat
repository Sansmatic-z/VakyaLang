@echo off
set PYTHONUTF8=1
pushd "%~dp0.."
python -m sanskrit_coder.main
popd
