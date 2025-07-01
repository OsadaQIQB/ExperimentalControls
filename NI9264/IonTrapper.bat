@echo off
cd /d "C:\Users\lab\Desktop\ExperimentalControls\"
start "" py TurnOnOffLasers_GUI.py
cd .\DAC\
start "" py PaulTrap_network_PySide6GUI.py
pause