from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QTabWidget
)
from PySide6.QtCore import Qt
import nidaqmx
import numpy as np
import datetime
import serial
import time
import pyvisa

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ion Trapper GUI")

        # Initialize serial connections
        self.ser1 = serial.Serial('COM4', 9600)
        self.ser2 = serial.Serial('COM5', 9600)

        # Initialize RF source
        self.rm = pyvisa.ResourceManager()
        self.RFsource = self.rm.open_resource("USB0::0x1AB1::0x099C::DSG8J252400161::INSTR")
        self.RF_freq = float(self.RFsource.query(":SOUR:FREQ?")) / 1e6  # Read frequency in MHz
        self.RF_pow = float(self.RFsource.query(":SOUR:POW?"))  # Read power in dBm

        # Load DAC voltages
        self.ao_input = np.loadtxt("DAC_voltages.txt")

        # Create main layout
        self.main_layout = QVBoxLayout()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_rf_tab(), "RF")
        self.tabs.addTab(self.create_shutters_tab(), "Shutters")
        self.main_layout.addWidget(self.tabs)

        # DAC layout
        self.main_layout.addLayout(self.create_dac_layout())

        # Set main layout
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Toggle states
        self.toggle_states = {
            "cooling_shutter": False,
            "repumper_shutter": False,
            "1st_ionization_shutter": False,
            "2nd_ionization_shutter": False,
            "ablation_shutter": False,
            "clock_shutter": False,
            "loading_shutter": False,
            "all_shutter": False,
            "RF_source": False,
        }

    def create_rf_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(self.create_toggle_button("RF Source", "RF_source", self.toggle_rf_source))
        layout.addWidget(self.create_rf_controls())
        return self.wrap_layout(layout)

    def create_shutters_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(self.create_toggle_button("Cooling Shutter", "cooling_shutter", self.toggle_cooling_shutter))
        layout.addWidget(self.create_toggle_button("Repumper Shutter", "repumper_shutter", self.toggle_repumper_shutter))
        layout.addWidget(self.create_toggle_button("1st Ionization Shutter", "1st_ionization_shutter", self.toggle_1st_ionization_shutter))
        layout.addWidget(self.create_toggle_button("2nd Ionization Shutter", "2nd_ionization_shutter", self.toggle_2nd_ionization_shutter))
        layout.addWidget(self.create_toggle_button("Ablation Shutter", "ablation_shutter", self.toggle_ablation_shutter))
        layout.addWidget(self.create_toggle_button("Clock Shutter", "clock_shutter", self.toggle_clock_shutter))
        layout.addWidget(self.create_toggle_button("Loading Shutter", "loading_shutter", self.toggle_loading_shutter))
        layout.addWidget(self.create_toggle_button("All Shutters", "all_shutter", self.toggle_all_shutter))
        return self.wrap_layout(layout)

    def create_dac_layout(self):
        layout = QVBoxLayout()

        # Arrange V1-V7 in the same layout as PaulTrap_network_GUI.py
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("V3"))
        row1.addWidget(self.create_dac_input(2))
        row1.addWidget(QLabel("V2"))
        row1.addWidget(self.create_dac_input(1))
        row1.addWidget(QLabel("V1"))
        row1.addWidget(self.create_dac_input(0))
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("V7"))
        row2.addWidget(self.create_dac_input(6))
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("V4"))
        row3.addWidget(self.create_dac_input(3))
        row3.addWidget(QLabel("V5"))
        row3.addWidget(self.create_dac_input(4))
        row3.addWidget(QLabel("V6"))
        row3.addWidget(self.create_dac_input(5))
        layout.addLayout(row3)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_dac_voltages)
        layout.addWidget(save_button)

        return layout

    def create_dac_input(self, index):
        input_field = QLineEdit(str(self.ao_input[index]))
        input_field.returnPressed.connect(lambda idx=index: self.update_dac_voltage_nidaqmx(idx))
        input_field.textChanged.connect(lambda value, idx=index: self.update_dac_voltage(idx, value))
        return input_field

    def create_rf_controls(self):
        layout = QVBoxLayout()
        freq_row = QHBoxLayout()
        freq_label = QLabel("Frequency (MHz):")
        freq_input = QLineEdit(str(self.RF_freq))
        freq_input.textChanged.connect(self.update_rf_frequency)
        freq_row.addWidget(freq_label)
        freq_row.addWidget(freq_input)
        layout.addLayout(freq_row)

        pow_row = QHBoxLayout()
        pow_label = QLabel("Power (dBm):")
        pow_input = QLineEdit(str(self.RF_pow))
        pow_input.textChanged.connect(self.update_rf_power)
        pow_row.addWidget(pow_label)
        pow_row.addWidget(pow_input)
        layout.addLayout(pow_row)

        return self.wrap_layout(layout)

    def create_toggle_button(self, label, key, callback):
        button = QPushButton(label)
        button.setCheckable(True)
        button.clicked.connect(lambda: self.toggle_button(key, callback))
        return button

    def wrap_layout(self, layout):
        container = QWidget()
        container.setLayout(layout)
        return container

    def toggle_button(self, key, callback):
        self.toggle_states[key] = not self.toggle_states[key]
        callback(self.toggle_states[key])

    def toggle_cooling_shutter(self, state):
        self.ser1.write(b'21' if state else b'20')

    def toggle_repumper_shutter(self, state):
        self.ser1.write(b'31' if state else b'30')

    def toggle_1st_ionization_shutter(self, state):
        self.ser2.write(b'01' if state else b'00')

    def toggle_2nd_ionization_shutter(self, state):
        self.ser1.write(b'01' if state else b'00')

    def toggle_ablation_shutter(self, state):
        self.ser1.write(b'11' if state else b'10')

    def toggle_clock_shutter(self, state):
        self.ser2.write(b'11' if state else b'10')

    def toggle_loading_shutter(self, state):
        # Toggle only 1st ionization, 2nd ionization, and ablation shutters
        self.toggle_1st_ionization_shutter(state)
        self.toggle_2nd_ionization_shutter(state)
        self.toggle_ablation_shutter(state)

        # Update button states visually
        self.update_loading_buttons(state)

    def toggle_all_shutter(self, state):
        # Toggle all shutters
        self.toggle_cooling_shutter(state)
        self.toggle_repumper_shutter(state)
        self.toggle_1st_ionization_shutter(state)
        self.toggle_2nd_ionization_shutter(state)
        self.toggle_ablation_shutter(state)
        self.toggle_clock_shutter(state)

        # Update button states visually
        self.update_all_buttons(state)

    def update_loading_buttons(self, state):
        for key in ["1st_ionization_shutter", "2nd_ionization_shutter", "ablation_shutter"]:
            self.toggle_states[key] = state
            button = self.findChild(QPushButton, key)
            if button:
                button.setChecked(state)

    def update_all_buttons(self, state):
        for key in ["cooling_shutter", "repumper_shutter", "1st_ionization_shutter", "2nd_ionization_shutter", "ablation_shutter", "clock_shutter"]:
            self.toggle_states[key] = state
            button = self.findChild(QPushButton, key)
            if button:
                button.setChecked(state)

    def toggle_rf_source(self, state):
        self.RFsource.write(":OUTP 1" if state else ":OUTP 0")

    def update_dac_voltage(self, index, value):
        try:
            self.ao_input[index] = float(value)
        except ValueError:
            pass

    def update_dac_voltage_nidaqmx(self, index):
        try:
            voltage = self.ao_input[index]
            # Replace 'Dev1' with the correct device name (e.g., 'cDAQ9185-1E6C94B')
            device_name = "DAC_network"  # Update this to the correct device name
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(f"{device_name}/ao{index}")
                task.write(voltage)
            print(f"DAC voltage updated: V{index + 1} = {voltage}V")
        except Exception as e:
            print(f"Error updating DAC voltage: {e}")

    def save_dac_voltages(self):
        np.savetxt("DAC_voltages.txt", self.ao_input)

    def update_rf_frequency(self, value):
        try:
            self.RF_freq = float(value)
            self.RFsource.write(f":SOUR:FREQ {self.RF_freq * 1e6}")
        except ValueError:
            pass

    def update_rf_power(self, value):
        try:
            self.RF_pow = float(value)
            self.RFsource.write(f":SOUR:POW {self.RF_pow}")
        except ValueError:
            pass


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()