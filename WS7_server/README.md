# WS7 Wavelength Meter Server

A Python project that provides communication with the Angstrom WS7 wavelength meter and network server functionality.

## Features

- **Wavelength Meter Communication**: Retrieve wavelength and frequency data from High Finesse Angstrom WS7 wavelength meter
- **Multi-channel Support**: Simultaneous measurement on up to 8 channels
- **Network Server**: Remote data access via TCP/IP socket communication
- **Debug Mode**: Simulation functionality without actual hardware

## File Structure

- `wlm.py`: WavelengthMeter class implementation (low-level communication with wavelength meter)
- `WS7_server_threading.py`: Multi-threaded TCP server implementation

## Requirements

- **OS**: Windows (requires WS7 DLL)
- **Python**: 3.6 or higher
- **High Finesse Angstrom WS7**: Wavelength meter hardware and drivers

## Installation

### 1. Install Python Packages

```powershell
pip install numpy argparse
```

### 2. Verify System Requirements

Ensure the WS7 wavelength meter driver is installed and the following DLL files exist:
- `C:\Windows\System32\wlmData.dll`
- `C:\Program Files (x86)\HighFinesse\Wavelength Meter WS7 4935\`

## Usage

### Basic Wavelength Measurement

```powershell
# Measure wavelength on all channels
python wlm.py

# Measure specific channels (e.g., channels 1, 2, 3)
python wlm.py 1 2 3

# Debug mode (testing without hardware)
python wlm.py --debug
```

### Network Server Operation

```powershell
# Start server with default settings (port 50000)
python WS7_server_threading.py

# Start server in debug mode
python WS7_server_threading.py --debug

# Start server with config file
python WS7_server_threading.py -c config.json

# Start server with custom port
python WS7_server_threading.py 8080
```

## Configuration

### config.json (Optional)

You can create a JSON configuration file for server settings:

```json
{
    "port": 8000,
    "root": "/",
    "precision": 11,
    "update_rate": 0.1,
    "debug": false,
    "channels": [
        {"i": 0, "label": "Channel 1"},
        {"i": 1, "label": "Channel 2"},
        {"i": 2, "label": "Channel 3"},
        {"i": 3, "label": "Channel 4"},
        {"i": 4, "label": "Channel 5"},
        {"i": 5, "label": "Channel 6"},
        {"i": 6, "label": "Channel 7"},
        {"i": 7, "label": "Channel 8"}
    ]
}
```

## API Specification

### WavelengthMeter Class

#### Methods

- `GetWavelength(channel=1)`: Get wavelength for specified channel (nm)
- `GetFrequency(channel=1)`: Get frequency for specified channel (THz)
- `GetExposureMode()`: Get exposure mode status
- `SetExposureMode(b)`: Set exposure mode
- `GetAll()`: Get all measurement values in dict format

#### Properties

- `wavelengths`: List of wavelengths for all channels
- `frequencies`: List of frequencies for all channels
- `wavelength`: Wavelength for channel 1
- `switcher_mode`: Get/set switcher mode

### TCP Server Specification

- **Port**: 50000 (default)
- **Protocol**: TCP
- **Data Format**: Comma-separated frequency values (integers, unit: 0.01 MHz)
- **Transmission Interval**: 0.1 seconds (100ms)
- **Data Example**: `651203456,429876543,412345678,398765432`

## Troubleshooting

### Common Issues

1. **DLL not found**
   - Verify that WS7 drivers are properly installed
   - Check if `wlmData.dll` exists in `C:\Windows\System32\`

2. **Permission errors**
   - Run Python scripts with administrator privileges
   - Windows UAC may be the cause

3. **Port already in use**
   - Specify a different port number or terminate existing processes

### Debug Mode

For testing without actual wavelength meter hardware:

```powershell
python wlm.py --debug
python WS7_server_threading.py --debug
```

## License

MIT License

Copyright (c) 2025 WS7 Server Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Related Information

- High Finesse Angstrom WS7: Precision wavelength meter
- Target Applications: Laser spectroscopy experiments, wavelength calibration, etc.
