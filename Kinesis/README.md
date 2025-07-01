# Thorlabs Kinesis Motor Controller

A comprehensive Python application for controlling Thorlabs Kinesis KCube Inertial Motor Controllers (KIM101) with a modern GUI interface.

## Overview

This project provides a complete solution for controlling multiple Thorlabs Kinesis motor controllers simultaneously. It includes:

- **Multi-device support**: Control up to 12 (user-defined) axes across multiple KIM101 devices
- **Real-time position monitoring**: Automatic position updates with configurable intervals
- **Intuitive GUI**: User-friendly interface built with PySide6
- **Configuration management**: Save and load motor configurations
- **Daemon architecture**: Separate worker process for reliable motor control

## Features

### Motor Control
- **Absolute positioning**: Move motors to specific positions
- **Jog movement**: Incremental movements with configurable step sizes
- **Zero setting**: Set current position as zero reference
- **Position monitoring**: Real-time position display with auto-refresh

### GUI Features
- **Multi-axis control**: Up to 12 independent motor axes
- **Device management**: Auto-detection of connected devices
- **Configuration persistence**: Save/load configurations as JSON files
- **System logging**: Real-time status and error reporting
- **Responsive interface**: Non-blocking operations with background processing

## Project Structure

```
Kinesis/
├── README.md                          # This file
├── requirements.txt                   # Python package dependencies
├── kim101_pythonnet.py               # Core Kinesis controller classes
├── kinesis_gui.py                    # Main GUI application
├── kinesis_worker_daemon.py          # Background worker process
├── KIM_installation.txt              # Installation instructions
├── KinesisGUI.bat                    # Windows batch file to launch GUI
├── run_kinesis_gui.bat              # Alternative launcher
├── test_motor_config.json           # Example configuration file
├── PaulTrapNetwork_motor_config.json # Production configuration example
└── Motion_Control_Examples-main/     # Thorlabs example files (reference)
```

## Installation

### Prerequisites

1. **Install Thorlabs Kinesis Software**
   - Download from: https://www.thorlabs.co.jp/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control&viewtab=0
   - This installs the required .NET libraries and device drivers

2. **Python Environment**
   - Python 3.8 or higher
   - Windows operating system (required for Thorlabs .NET libraries)

### Python Package Installation

Install the required Python packages:

```bash
# Core dependencies
pip install pythonnet PySide6

# Optional: For alternative control methods
pip install pylablib
```

Or install from requirements file:

```bash
pip install -r requirements.txt
```

### Package Dependencies

The application requires the following Python packages:

- **pythonnet**: Interface to Thorlabs .NET API
- **PySide6**: GUI framework for the main interface
- **pylablib**: Alternative control library (optional)

## Usage

### Quick Start

1. **Connect your KIM101 devices** to USB ports
2. **Launch the GUI**:
   ```bash
   python kinesis_gui.py
   ```
   Or double-click `KinesisGUI.bat` on Windows

3. **Add motor axes** using the "Add Axis" button
4. **Select devices** from the dropdown menus
5. **Control motors** using the jog buttons or absolute positioning

### Configuration Management

#### Saving Configurations
- Click "Save" button to save current axis configuration
- Choose filename and location for the JSON configuration file

#### Loading Configurations
- Click "Load" button to load a previously saved configuration
- Select the JSON configuration file

#### Configuration File Format
```json
[
  {
    "device": "97251312",
    "channel": 1,
    "axis_name": "Microscope X",
    "jog_step": "100",
    "goto": "1000",
    "auto_update": true
  }
]
```

### Motor Control Operations

#### Jog Movement
- Set step size in the "Step" field
- Use "← -" and "+ →" buttons for incremental movement
- Movement is relative to current position

#### Absolute Positioning
- Enter desired position in "Go to" field
- Click "Move" button or press Enter
- Motor moves to absolute position

#### Zero Setting
- Click "Zero" button to set current position as zero reference
- Useful for establishing coordinate systems

## Architecture

### Component Overview

1. **GUI Application** (`kinesis_gui.py`)
   - Main user interface
   - Position monitoring thread
   - Configuration management

2. **Worker Daemon** (`kinesis_worker_daemon.py`)
   - Background process for motor control
   - Handles actual hardware communication
   - Maintains persistent device connections

3. **Controller Classes** (`kim101_pythonnet.py`)
   - Low-level device control
   - Thorlabs .NET API interface
   - Multi-device management

### Communication Flow

```
GUI Application ↔ Worker Daemon ↔ Kinesis Controllers ↔ Hardware
```

- GUI sends commands via JSON messages to worker daemon
- Worker daemon maintains persistent connections to hardware
- Position updates flow back through the same path

## Configuration Examples

### Single Device Setup
```json
[
  {
    "device": "97251312",
    "channel": 1,
    "axis_name": "X Axis",
    "jog_step": "100",
    "goto": "",
    "auto_update": true
  }
]
```

### Multi-Device Setup
```json
[
  {
    "device": "97000002",
    "channel": 1,
    "axis_name": "Microscope H",
    "jog_step": "50",
    "goto": "1000",
    "auto_update": true
  },
  {
    "device": "74001138",
    "channel": 1,
    "axis_name": "Focus",
    "jog_step": "10",
    "goto": "500",
    "auto_update": true
  }
]
```

## Troubleshooting

### Common Issues

1. **Device Not Found**
   - Verify USB connection
   - Check device appears in Windows Device Manager
   - Ensure Thorlabs Kinesis software is installed

2. **Connection Timeout**
   - Try disconnecting and reconnecting USB
   - Restart the application
   - Check for conflicting software

3. **Position Update Errors**
   - Verify device is properly connected
   - Check auto-update checkbox is enabled
   - Try manual position refresh

### Error Messages

- **"Worker not available"**: Worker daemon failed to start
- **"Device not found"**: Specified serial number not detected
- **"Position read error"**: Communication failure with device
- **"Move failed"**: Motor movement command rejected

## Development

### Code Structure

The application follows a modular architecture:

- **UI Layer**: PySide6-based GUI components
- **Control Layer**: Command processing and device management
- **Hardware Layer**: Direct Thorlabs API interface

### Extending Functionality

To add new motor control features:

1. Add command handling in `kinesis_worker_daemon.py`
2. Implement UI controls in `kinesis_gui.py`
3. Update the controller classes if needed

## License

This project is provided as-is for educational and research purposes. Please refer to Thorlabs licensing terms for the underlying Kinesis software.

## Support

For hardware-specific issues, consult Thorlabs documentation and support resources.

For software issues, check the system log in the GUI for detailed error messages.

## Version History

- **v1.0**: Initial release with basic motor control
- **v2.0**: Added multi-device support and improved GUI
- **v3.0**: Daemon architecture and enhanced reliability

## Related Resources

- [Thorlabs Kinesis Software](https://www.thorlabs.co.jp/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control&viewtab=0)
- [Motion Control Examples](https://github.com/Thorlabs/Motion_Control_Examples)
- [PythonNET Documentation](https://pythonnet.github.io/)
