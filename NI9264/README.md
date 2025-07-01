# Paul Trap Ion Control System

A comprehensive control system for Paul trap ion experiments with GUI-based control of DAC voltages, RF parameters, and laser shutters.

## Overview

This system provides experimental control for ion trapping experiments using:
- **DAC Control**: 8-channel voltage control via National Instruments DAQ
- **RF Source Control**: Frequency and power control for the RF trap
- **Shutter Control**: Multiple laser shutter controls via serial communication to Arduino(s)
- **Real-time GUI**: PySide6-based interface for interactive control

## Features

- **Multi-tab GUI Interface**
  - RF tab: Control RF frequency (MHz) and power (dBm)
  - Shutters tab: Individual and grouped shutter controls
  - DAC voltage controls with real-time updates

- **Hardware Integration**
  - National Instruments DAQ (NI-9264) for analog output
  - Serial communication for shutter controllers (COM4, COM5)
  - VISA-compatible RF source control
  - Automatic device detection and initialization

- **Data Management**
  - Voltage settings persistence via `DAC_voltages.txt`
  - RF parameter storage in `RF_Params.txt`
  - Timestamped logging capabilities

## System Requirements

### Hardware
- National Instruments DAQ device (NI-9264 or compatible)
- RF source with VISA/USB interface
- Serial-controlled shutter systems on COM4 and COM5
- Windows operating system

### Software Dependencies

The system requires the following Python packages:

```
PySide6>=6.0.0
nidaqmx>=0.6.0
numpy>=1.20.0
pyvisa>=1.11.0
pyserial>=3.5
```

## Installation

1. **Install Python Dependencies**
   ```bash
   pip install PySide6 nidaqmx numpy pyvisa pyserial
   ```

2. **Install NI-DAQmx Runtime**
   - Download and install NI-DAQmx runtime from National Instruments
   - Ensure your DAQ device is properly configured

3. **Configure Hardware**
   - Connect DAQ device and verify device name (update `device_name` in code if needed)
   - Connect RF source via USB
   - Set up serial connections for shutter controllers on COM4 and COM5

## Usage

### Starting the Application

**Method 1: Direct Python execution**
```bash
python PaulTrap_network_PySide6GUI.py
```

**Method 2: Using the batch file**
```bash
IonTrapper.bat
```

### GUI Controls

#### RF Tab
- **Frequency Control**: Set RF frequency in MHz
- **Power Control**: Set RF power in dBm
- **RF Output Toggle**: Turn RF source on/off

#### Shutters Tab
- **Individual Shutters**: 
  - Cooling Shutter
  - Repumper Shutter
  - 1st Ionization Shutter
  - 2nd Ionization Shutter
  - Ablation Shutter
  - Clock Shutter
- **Group Controls**:
  - Loading: Controls ionization and ablation shutters
  - All: Controls all shutters simultaneously

#### DAC Voltage Controls
- **6 Voltage Channels**: V1 through V6
- **Real-time Updates**: Press Enter to apply voltage immediately
- **Save Function**: Persist voltage settings to file

### Configuration Files

#### DAC_voltages.txt
Contains the 8 DAC voltage values (one per line):
```
6.000000000000000000e+00
-8.000000000000000000e+00
6.000000000000000000e+00
8.000000000000000000e+00
-8.000000000000000000e+00
1.000000000000000000e+00
-3.000000000000000000e+00
```

#### RF_Params.txt
Stores RF source parameters:
```
44.4    # Frequency in MHz
-22.0   # Power in dBm
```

## Hardware Configuration

### DAQ Device Setup
- Update the `device_name` variable in the code to match your DAQ device name
- Default: `"DAC_network"`
- Common alternatives: `"Dev1"`, `"cDAQ9185-1E6C94B"`

### Serial Port Configuration
- **COM4**: Controls cooling, repumper, 2nd ionization, and ablation shutters
- **COM5**: Controls 1st ionization and clock shutters
- Baud rate: 9600

### RF Source Setup
- Uses VISA USB interface
- Default resource: `"USB0::0x1AB1::0x099C::DSG8J252400161::INSTR"`
- Supports SCPI commands for frequency and power control

## Troubleshooting

### Common Issues

1. **DAQ Device Not Found**
   - Verify NI-DAQmx runtime installation
   - Check device name in NI MAX
   - Update `device_name` variable in code

2. **Serial Port Errors**
   - Verify COM port assignments in Device Manager
   - Check cable connections
   - Ensure no other applications are using the ports

3. **RF Source Connection Issues**
   - Check USB connection
   - Verify VISA runtime installation
   - Update resource string if using different RF source

4. **Import Errors**
   - Install missing Python packages
   - Verify Python environment setup

## Safety Notes

- Always verify voltage limits before applying DAC voltages
- Ensure proper grounding of all equipment
- Follow laser safety protocols when operating shutters
- Monitor RF power levels to prevent equipment damage

## File Structure

```
NI9264/
├── PaulTrap_network_PySide6GUI.py  # Main GUI application
├── IonTrapper.bat                   # Startup batch file
├── DAC_voltages.txt                 # DAC voltage configuration
├── RF_Params.txt                    # RF source parameters
└── README.md                        # This documentation
```

## License

This software is developed for research purposes. Please ensure compliance with your institution's software usage policies.
