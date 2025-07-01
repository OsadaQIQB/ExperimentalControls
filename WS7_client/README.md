# WS7 Client - Laser Frequency Control System

A Python-based application for controlling DLCpro laser systems and synchronizing them with WS7 wavelength meter measurements for precision frequency stabilization.

## Overview

This application provides a graphical user interface for monitoring and controlling multiple laser frequencies in real-time. It connects to DLCpro laser controllers over a network and uses WS7 wavelength meter data to maintain precise frequency locks on multiple laser lines commonly used in atomic physics experiments.

## Features

- **Multi-laser Control**: Simultaneous control of up to 4 laser lines:
  - Cooling laser (422 nm, ~710 THz)
  - Ionization laser (461 nm, ~650 THz) 
  - Repumper laser (1092 nm, ~274 THz)
  - Clock laser (674 nm, ~444 THz)

- **Real-time Monitoring**: Live frequency measurements from WS7 wavelength meter
- **Frequency Locking**: Individual toggle controls for each laser frequency lock
- **Target Frequency Management**: Save and load target frequencies to JSON configuration
- **Network Communication**: TCP socket connection to WS7 server for frequency data
- **User-friendly GUI**: Built with PySide6 for modern interface

## System Requirements

- Python 3.7+
- Windows operating system
- Network access to DLCpro controllers and WS7 server

## Dependencies

```
PySide6
toptica-lasersdk
numpy
nest-asyncio
```

## Installation

1. Clone or download this repository
2. Install required Python packages:
   ```bash
   pip install PySide6 toptica-lasersdk numpy nest-asyncio
   ```
3. Ensure network connectivity to the laser controllers and WS7 server

## Hardware Configuration

### Network Addresses
- **Cooling/Repumper Laser**: 100.101.0.79
- **Ionization/Quencher Laser**: 100.101.0.77  
- **Clock Laser**: 100.101.0.75
- **WS7 Server**: 100.101.0.97:50000

### Default Target Frequencies
- **Cooling**: 710.96242 THz
- **Ionization**: 650.5038 THz
- **Repumper**: 274.589005 THz
- **Clock**: 444.83556 THz

## Usage

### Starting the Application

#### Method 1: Batch File (Recommended)
```bash
WS7_fetch.bat
```

#### Method 2: Direct Python Execution
```bash
python WS7_fetch_pyside6.py
```

### GUI Controls

1. **Target Frequency Input**: Enter desired frequency values for each laser
2. **Actual Frequency Display**: Shows current measured frequencies from WS7
3. **Frequency Difference**: Displays the difference between target and actual frequencies
4. **Lock Toggle Buttons**: Enable/disable frequency locking for each laser
5. **Save Button**: Store current target frequencies to configuration file

### Configuration File

Target frequencies are automatically saved to `target_freq.json`:

```json
{
  "cooling": 710.96242,
  "ionization": 650.5038,
  "repumper": 274.589005,
  "clock": 444.83556
}
```

## Development

### File Structure

```
WS7_client/
├── README.md                 # This file
├── target_freq.json         # Configuration file for target frequencies
├── WS7_fetch_pyside6.py     # Main application (PySide6 GUI)
└── WS7_fetch.bat           # Windows batch launcher
```

### Key Components

- **GUI Framework**: PySide6 for modern interface
- **Laser Control**: TOPTICA Laser SDK for DLCpro communication
- **Network Communication**: TCP sockets for WS7 server connection
- **Configuration Management**: JSON-based target frequency storage

## Troubleshooting

### Common Issues

1. **Connection Errors**: 
   - Verify network connectivity to laser controllers and WS7 server
   - Check IP addresses and port configurations
   - Ensure firewall settings allow connections

2. **GUI Issues**:
   - Verify PySide6 installation
   - Check Python version compatibility

3. **Laser Control Problems**:
   - Confirm TOPTICA Laser SDK installation
   - Verify laser controller network settings
   - Check laser controller status and availability

### Error Messages

- **"サーバー接続エラー"**: Server connection error - check WS7 server connectivity
- **Network timeouts**: Verify network configuration and device availability

## Safety Considerations

- Always verify target frequencies before enabling locks
- Monitor laser power levels during frequency adjustments
- Ensure proper safety protocols for laser operation
- Have emergency shutdown procedures in place

## License

This software is provided as-is for research and educational purposes. Please ensure compliance with your institution's safety protocols and software licensing requirements.

## Support

For technical support or questions about this application, please contact the laboratory maintenance team or refer to the TOPTICA Laser SDK documentation for laser-specific issues.

---

**Note**: This application is designed for use in atomic physics research environments. Proper training and safety protocols are required before operation.
