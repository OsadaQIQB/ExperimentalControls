# NI USB-6356 Control GUI

A comprehensive Python GUI application for controlling the National Instruments USB-6356 DAQ device. This application provides a unified interface for analog I/O, digital I/O, pulse generation, and counter operations.

## Features

### 1. Analog I/O Control
- **Analog Output (AO)**: Control voltage output on channels ao0 and ao1
- **Analog Input (AI)**: Real-time monitoring of analog input channels with live plotting
- Interactive graph controls with channel selection checkboxes
- Configurable monitoring parameters

### 2. Digital Pulse Generation
- Create complex digital pulse sequences with precise timing
- Visual waveform display using matplotlib
- Multi-channel pulse pattern generation
- Export/import pulse configurations to/from JSON files
- Configurable sample rates and total sequence duration

### 3. Counter Operations
- Real-time edge counting on configurable input terminals
- Live data visualization with time-series plotting
- Automatic data logging with CSV export
- Configurable counting intervals and display windows
- Background thread processing for smooth operation

### 4. Configuration Management
- Save and load system configurations
- JSON-based configuration storage
- Persistent settings across sessions

## System Requirements

### Hardware
- National Instruments USB-6356 DAQ device
- Windows operating system (tested on Windows 10/11)

### Software Dependencies
- Python 3.8 or higher
- Required Python packages (see [Installation](#installation))

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd NIUSB6356
   ```

2. **Install required Python packages**
   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` is not available, install packages manually:
   ```bash
   pip install PySide6 numpy matplotlib pyqtgraph nidaqmx
   ```

3. **Install NI-DAQmx drivers**
   - Download and install NI-DAQmx from the National Instruments website
   - Ensure your USB-6356 device is properly connected and recognized

## Package Dependencies

The application requires the following Python packages:

### Core GUI Framework
- **PySide6**: Qt-based GUI framework for Python
  - `QtWidgets`: UI components
  - `QtCore`: Core functionality including threading

### Data Processing and Visualization
- **numpy**: Numerical computing library for array operations
- **matplotlib**: Plotting library for waveform visualization
  - `matplotlib.backends.backend_qtagg`: Qt integration
- **pyqtgraph**: High-performance plotting for real-time data

### Hardware Interface
- **nidaqmx**: Python API for National Instruments DAQmx driver
  - Provides direct interface to NI hardware
  - Supports analog I/O, digital I/O, and counter operations

### Standard Library
- **sys**: System-specific parameters and functions
- **json**: JSON data serialization
- **csv**: CSV file reading/writing
- **time**: Time-related functions
- **datetime**: Date and time handling

## Usage

### Starting the Application

#### Method 1: Direct Python execution
```bash
python NIUSB6356all_GUI.py
```

#### Method 2: Using the batch file
```bash
NIUSB6356.bat
```

### Application Interface

The application features a tabbed interface with the following sections:

#### 1. I/O Control Tab
- **Analog Output**: Set voltage values for ao0 and ao1 channels
- **Analog Input**: Monitor input channels with real-time plotting
- **Digital I/O**: Control digital input/output operations

#### 2. Pulse Generation Tab
- **Line Registration**: Map logical names to physical digital lines
- **Pulse Configuration**: Set pulse timing parameters (start time, duration)
- **Waveform Visualization**: Preview pulse sequences before output
- **File Operations**: Save/load pulse configurations

#### 3. Counter Tab
- **Device Configuration**: Select counter channel and input terminal
- **Timing Settings**: Configure counting interval and display window
- **Data Logging**: Enable automatic CSV logging of count data
- **Real-time Display**: Live plotting of count rates

### Configuration Files

Pulse configurations are stored in the `configs/` directory as JSON files. Example structure:

```json
{
  "line_map": {
    "Trigger": 0,
    "Laser1": 1,
    "Laser2": 2
  },
  "pulses": [
    {
      "name": "Trigger",
      "start": 0.0,
      "duration": 10e-6
    }
  ],
  "sample_rate": 10000000,
  "total_time": 200e-6
}
```

### Data Logging

Counter data is automatically logged to the `logs/` directory when enabled. Log files are named with timestamps:
- Format: `counter_log_YYYYMMDD_HHMMSS.csv`
- Contains: timestamp and count data

## File Structure

```
NIUSB6356/
├── NIUSB6356all_GUI.py     # Main application file
├── NIUSB6356.bat           # Windows batch launcher
├── configs/                # Configuration files
│   └── *.json             # Pulse sequence configurations
├── logs/                   # Data log files
│   └── *.csv              # Counter log files
└── README.md              # This file
```

## Troubleshooting

### Common Issues

1. **Device Not Found**
   - Verify NI-DAQmx drivers are installed
   - Check USB-6356 connection
   - Ensure device appears in NI MAX (Measurement & Automation Explorer)

2. **Import Errors**
   - Verify all required packages are installed
   - Check Python version compatibility
   - Ensure virtual environment is activated (if using)

3. **Permission Errors**
   - Run application as administrator if needed
   - Check file/directory permissions for config and log folders

### Device Configuration

The default device name is `NIUSB_network`. If your device has a different name:
1. Open NI MAX
2. Find your device name
3. Update the `device_name` parameter in the code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with hardware
5. Submit a pull request

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with National Instruments software licensing terms when using NI-DAQmx drivers.

## Support

For issues related to:
- **Hardware**: Consult National Instruments documentation
- **Software**: Check Python package documentation
- **Application**: Review this README and source code comments

---

*Last updated: July 2025*
