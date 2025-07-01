# unified_niusb6356_gui.py

# !!IMPORTANT!! NI device name is set here to be 'NIUSB_network' and they should be changed as you need. Use ''replace all''

# This GUI provides a unified interface for controlling the NI USB-6356 device, including analog outputs, analog inputs, digital inputs/outputs, pulse sequences, and counter readings.    


import sys
import json
import csv
import time
from datetime import datetime
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QLineEdit, QGridLayout, QFileDialog, QCheckBox, QSpinBox,
    QStackedLayout, QComboBox, QDoubleSpinBox, QTabWidget, QSplitter, QTextEdit, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
import pyqtgraph as pg
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

import nidaqmx
from nidaqmx.constants import LineGrouping, Edge, AcquisitionType

# --- Digital Pulse Output Class ---
class DigitalPulseSequence:
    def __init__(self, device_name='NIUSB_network', port=0, sample_rate=10_000_000, total_time=200e-6):
        self.device_name = device_name
        self.port = port
        self.sample_rate = sample_rate
        self.total_samples = int(sample_rate * total_time)
        self.total_time = total_time
        self.line_map = {}  # name -> line
        self.patterns = {}
        self.pulses = []

    def register_line(self, name, line):
        self.line_map[name] = line
        if line not in self.patterns:
            self.patterns[line] = np.zeros(self.total_samples, dtype=bool)
        self.rebuild()

    def add_pulse(self, name, start, duration):
        if name not in self.line_map:
            raise ValueError(f"{name} is not registered")
        self.pulses.append({'name': name, 'start': start, 'duration': duration})
        self.rebuild()

    def remove_pulse(self, index):
        del self.pulses[index]
        self.rebuild()

    def rebuild(self):
        for arr in self.patterns.values():
            arr[:] = False
        for p in self.pulses:
            line = self.line_map[p["name"]]
            s = int(p["start"] * self.sample_rate)
            e = int((p["start"] + p["duration"]) * self.sample_rate)
            self.patterns[line][s:e] = True

    def output(self):
        if not self.pulses:
            raise RuntimeError("No pulses registered")
        lines = sorted(set(self.line_map[name] for name in [p["name"] for p in self.pulses]))
        pattern = np.array([self.patterns[l] for l in lines], dtype=bool)
        chan_range = f"line{lines[0]}:{lines[-1]}"
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                f"{self.device_name}/port{self.port}/{chan_range}",
                line_grouping=LineGrouping.CHAN_PER_LINE)
            task.timing.cfg_samp_clk_timing(
                rate=self.sample_rate,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=self.total_samples)
            task.write(pattern, auto_start=False)
            task.start()
            task.wait_until_done(timeout=2)
        print("✅ Output completed")

    def export_json(self, path):
        data = {
            'line_map': self.line_map,
            'pulses': self.pulses,
            'sample_rate': self.sample_rate,
            'total_time': self.total_time
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_json(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        self.line_map = data['line_map']
        self.sample_rate = data['sample_rate']
        self.total_time = data['total_time']
        self.total_samples = int(self.sample_rate * self.total_time)
        self.pulses = data['pulses']
        self.patterns = {line: np.zeros(self.total_samples, dtype=bool) for line in set(self.line_map.values())}
        self.rebuild()

class PulseGui(QWidget):
    def __init__(self):
        super().__init__()
        self.seq = DigitalPulseSequence()
        layout = QVBoxLayout()

        # Line registration
        line_layout = QHBoxLayout()
        self.line_number_box = QComboBox()
        self.line_number_box.addItems([str(i) for i in range(8)])
        self.line_name_input = QLineEdit()
        self.line_register_btn = QPushButton("Register Line")
        self.line_register_btn.clicked.connect(self.register_line)
        line_layout.addWidget(QLabel("Line No"))
        line_layout.addWidget(self.line_number_box)
        line_layout.addWidget(QLabel("Name"))
        line_layout.addWidget(self.line_name_input)
        line_layout.addWidget(self.line_register_btn)
        layout.addLayout(line_layout)

        # Line mapping table
        self.line_info = QTextEdit()
        self.line_info.setReadOnly(True)
        layout.addWidget(QLabel("Line Mapping"))
        layout.addWidget(self.line_info)

        # Add pulse
        pulse_layout = QHBoxLayout()
        self.line_select = QComboBox()
        self.start_input = QLineEdit("0")
        self.duration_input = QLineEdit("10")
        self.add_pulse_btn = QPushButton("Add Pulse")
        self.add_pulse_btn.clicked.connect(self.add_pulse)
        pulse_layout.addWidget(QLabel("Line"))
        pulse_layout.addWidget(self.line_select)
        pulse_layout.addWidget(QLabel("Start (us)"))
        pulse_layout.addWidget(self.start_input)
        pulse_layout.addWidget(QLabel("Duration (us)"))
        pulse_layout.addWidget(self.duration_input)
        pulse_layout.addWidget(self.add_pulse_btn)
        layout.addLayout(pulse_layout)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Line", "Start", "Duration"])
        self.table.itemSelectionChanged.connect(self.plot)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_pulse)
        self.output_btn = QPushButton("Output")
        self.output_btn.clicked.connect(self.output)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save)
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self.load)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.output_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.load_btn)
        layout.addLayout(btn_layout)

        # Waveform
        self.fig = plt.figure(figsize=(6, 3))
        self.canvas = FigureCanvasQTAgg(self.fig)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.refresh()

    def register_line(self):
        line = int(self.line_number_box.currentText())
        name = self.line_name_input.text()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name")
            return
        self.seq.register_line(name, line)
        self.refresh()

    def add_pulse(self):
        name = self.line_select.currentText()
        try:
            start = float(self.start_input.text()) * 1e-6
            dur = float(self.duration_input.text()) * 1e-6
            self.seq.add_pulse(name, start, dur)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Add Failed", str(e))

    def remove_pulse(self):
        row = self.table.currentRow()
        if row >= 0:
            self.seq.remove_pulse(row)
            self.refresh()

    def output(self):
        try:
            self.seq.output()
            # QMessageBox.information(self, "Completed", "Output completed")
        except Exception as e:
            QMessageBox.critical(self, "Output Failed", str(e))

    def save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "JSON (*.json)")
        if path:
            self.seq.export_json(path)

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load", "", "JSON (*.json)")
        if path:
            self.seq.import_json(path)
            self.refresh()

    def refresh(self):
        self.line_select.clear()
        self.line_select.addItems(self.seq.line_map.keys())

        self.table.setRowCount(0)
        for p in self.seq.pulses:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(p["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(f"{p['start']*1e6:.1f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{p['duration']*1e6:.1f}"))

        self.line_info.setPlainText(
            "\n".join(f"{v}: {k}" for k, v in self.seq.line_map.items())
        )
        self.plot()

    def plot(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        lines = sorted(self.seq.patterns.keys())
        t = np.arange(self.seq.total_samples) / self.seq.sample_rate * 1e6
        selected_names = set()
        for idx in self.table.selectionModel().selectedRows():
            name = self.table.item(idx.row(), 0).text()
            selected_names.add(name)

        for line in lines:
            label = [k for k, v in self.seq.line_map.items() if v == line]
            if not label:
                continue
            name = label[0]
            y = self.seq.patterns[line] * 1 + line
            color = 'red' if name in selected_names else None
            ax.step(t, y, where='post', label=name, color=color)

        ax.set_xlabel("Time (us)")
        ax.set_ylabel("Line")
        ax.set_yticks(lines)
        ax.grid(True)
        ax.legend()
        self.canvas.draw()

# --- Counter Thread Class ---
class CounterReader(QThread):
    count_signal = Signal(object)

    def __init__(self, device_name="NIUSB_network", counter="ctr0", terminal="PFI8", interval=1.0):
        super().__init__()
        self.device_name = device_name
        self.counter = counter
        self.terminal = terminal
        self.interval = interval
        self.running = False
        self.task = None
        self.last_count = 0
        self.MAX_COUNT = 2**32

    def run(self):
        try:
            self.task = nidaqmx.Task()
            chan = f"{self.device_name}/{self.counter}"
            self.task.ci_channels.add_ci_count_edges_chan(chan, edge=Edge.RISING)
            self.task.ci_channels.all.ci_count_edges_term = f"/{self.device_name}/{self.terminal}"
            self.task.start()
            self.last_count = self.task.read()
            self.running = True
            while self.running:
                current = self.task.read()
                diff = (current - self.last_count) % self.MAX_COUNT
                self.count_signal.emit(diff)
                self.last_count = current
                time.sleep(self.interval)
        except Exception as e:
            print(f"[CounterReader Error] {e}")

    def stop(self):
        self.running = False
        if self.task:
            self.task.close()
        self.wait()

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        super().__init__(self.fig)
        self.ax.set_title("Pulse Count / s")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Counts")
        self.ax.grid(True)
        self.x_data = []
        self.y_data = []
        self.t0 = time.time()
        self.time_window = 30

    def update_plot(self, count):
        t = time.time() - self.t0
        self.x_data.append(t)
        self.y_data.append(count)
        if len(self.x_data) > self.time_window:
            self.x_data = self.x_data[-self.time_window:]
            self.y_data = self.y_data[-self.time_window:]
        self.ax.clear()
        self.ax.plot(self.x_data, self.y_data, marker='o')
        self.ax.set_title("Pulse Count / s")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Counts")
        self.ax.grid(True)
        self.draw()

# --- Main Unified GUI ---
class UnifiedNIUSB6356GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NI USB-6356 Full Function GUI")
        self.config = {"ao0": 0.0, "ao1": 0.0, "time_window": 10}
        self.load_config()
        self.start_time = time.time()
        self.time_window = self.config.get("time_window", 10)
        self.ai_data = {ch: [] for ch in ["ai0", "ai1", "ai2", "ai3"]}
        self.ai_time = []

        self.reader = None
        self.data_log = []

        self.init_ui()

        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_inputs)
        self.timer.start()

    def init_ui(self):
        # --- Left side: I/O tabs (AO, AI, DI/DO, Pulse) ---
        left_tab = QTabWidget()
        # --- I/O tab ---
        io_tab = QWidget()
        io_layout = QVBoxLayout(io_tab)

        # AO
        ao_group = QWidget()
        ao_layout = QVBoxLayout(ao_group)
        ao_grid = QGridLayout()
        ao_grid.addWidget(QLabel("Analog Output (AO)"), 0, 0, 1, 2)
        self.ao_controls = {}
        for i, ch in enumerate(["ao0", "ao1"]):
            label = QLabel(ch)
            line_edit = QLineEdit(str(self.config.get(ch, 0.0)))
            set_btn = QPushButton("Set")
            set_btn.clicked.connect(lambda _, c=ch, le=line_edit: self.set_ao(c, le))
            ao_grid.addWidget(label, i+1, 0)
            ao_grid.addWidget(line_edit, i+1, 1)
            ao_grid.addWidget(set_btn, i+1, 2)
            self.ao_controls[ch] = line_edit
        ao_layout.addLayout(ao_grid)
        io_layout.addWidget(ao_group)

        # AI
        ai_group = QWidget()
        ai_layout = QVBoxLayout(ai_group)
        ai_grid = QGridLayout()
        ai_grid.addWidget(QLabel("Analog Input (AI)"), 0, 0, 1, 2)
        self.ai_labels = {}
        for i, ch in enumerate(self.ai_data):
            label = QLabel(ch)
            val_label = QLabel("N/A")
            ai_grid.addWidget(label, i+1, 0)
            ai_grid.addWidget(val_label, i+1, 1)
            self.ai_labels[ch] = val_label
        ai_layout.addLayout(ai_grid)
        # AI Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setYRange(-0.1, 5.0)
        self.plot_widget.setMouseEnabled(y=False)
        self.plot_widget.addLegend()
        self.plot_curves = {}
        self.ai_checkboxes = {}
        graph_ctrl_layout = QHBoxLayout()
        for ch in self.ai_data:
            cb = QCheckBox(ch)
            cb.setChecked(True)
            self.ai_checkboxes[ch] = cb
            graph_ctrl_layout.addWidget(cb)
            self.plot_curves[ch] = self.plot_widget.plot(pen=pg.mkPen(width=2), name=ch)
        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 300)
        self.time_spin.setValue(self.time_window)
        self.time_spin.valueChanged.connect(self.update_time_window)
        graph_ctrl_layout.addWidget(QLabel("Window (s):"))
        graph_ctrl_layout.addWidget(self.time_spin)
        ai_layout.addWidget(QLabel("Analog Input Plot"))
        ai_layout.addWidget(self.plot_widget)
        ai_layout.addLayout(graph_ctrl_layout)
        io_layout.addWidget(ai_group)

        # DI/DO
        dio_group = QWidget()
        dio_layout = QVBoxLayout(dio_group)
        self.io_stacks = {}
        self.io_do_buttons = {}
        self.io_di_labels = {}
        for port in [0, 1, 2]:
            dio_layout.addWidget(QLabel(f"Port {port}"))
            combo = QComboBox()
            combo.addItems(["Digital Output", "Digital Input"])
            dio_layout.addWidget(combo)
            stack = QStackedLayout()
            self.io_stacks[port] = (combo, stack)

            do_widget = QWidget()
            do_layout = QGridLayout()
            for i in range(8):
                ch = f"port{port}/line{i}"
                btn = QPushButton(f"{ch}: OFF")
                btn.setCheckable(True)
                btn.clicked.connect(lambda _, b=btn, c=ch: self.toggle_do(c, b))
                do_layout.addWidget(btn, i//4, i%4)
                self.io_do_buttons[ch] = btn
            do_widget.setLayout(do_layout)

            di_widget = QWidget()
            di_layout = QGridLayout()
            for i in range(8):
                ch = f"port{port}/line{i}"
                label = QLabel(f"{ch}: N/A")
                di_layout.addWidget(label, i//4, i%4)
                self.io_di_labels[ch] = label
            di_widget.setLayout(di_layout)

            stack.addWidget(do_widget)
            stack.addWidget(di_widget)
            combo.currentIndexChanged.connect(lambda i, s=stack: s.setCurrentIndex(i))
            container = QWidget()
            container.setLayout(stack)
            dio_layout.addWidget(container)
        io_layout.addWidget(dio_group)

        left_tab.addTab(io_tab, "I/O")

        # --- Pulse tab ---
        self.pulse_tab = PulseGui()
        left_tab.addTab(self.pulse_tab, "Pulse")

        # --- Right side: Counter tab ---
        right_tab = QTabWidget()
        counter_tab = QWidget()
        counter_layout = QVBoxLayout(counter_tab)
        # Counter UI
        counter_ctrl_layout = QHBoxLayout()
        self.device_box = QLineEdit("NIUSB_network")
        self.counter_box = QLineEdit("ctr0")
        self.terminal_box = QLineEdit("PFI8")
        self.interval_spinbox = QDoubleSpinBox()
        self.interval_spinbox.setRange(0.1, 5.0)
        self.interval_spinbox.setValue(1.0)
        self.time_window_spinbox = QSpinBox()
        self.time_window_spinbox.setRange(10, 300)
        self.time_window_spinbox.setValue(30)
        self.start_button = QPushButton("Start Counter")
        self.stop_button = QPushButton("Stop Counter")
        self.stop_button.setEnabled(False)
        self.save_checkbox = QCheckBox("Save Log")
        self.save_checkbox.setChecked(True)
        for w in [QLabel("Device:"), self.device_box, QLabel("Counter:"), self.counter_box,
                  QLabel("Terminal:"), self.terminal_box, QLabel("Interval (s):"), self.interval_spinbox,
                  QLabel("Time Window:"), self.time_window_spinbox,
                  self.start_button, self.stop_button, self.save_checkbox]:
            counter_ctrl_layout.addWidget(w)
        counter_layout.addLayout(counter_ctrl_layout)
        self.counter_canvas = MplCanvas()
        counter_layout.addWidget(self.counter_canvas)
        self.start_button.clicked.connect(self.start_counter)
        self.stop_button.clicked.connect(self.stop_counter)
        right_tab.addTab(counter_tab, "Counter")

        # --- Config tab ---
        config_tab = QWidget()
        cfg_layout = QHBoxLayout(config_tab)
        for lbl, func in [("Save Config", self.save_config_dialog), ("Load Config", self.load_config_dialog),
                          ("Export CSV", self.export_csv_dialog)]:
            btn = QPushButton(lbl)
            btn.clicked.connect(func)
            cfg_layout.addWidget(btn)
        right_tab.addTab(config_tab, "Config")

        # --- Split left and right with Splitter ---
        splitter = QSplitter()
        splitter.addWidget(left_tab)
        splitter.addWidget(right_tab)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        self.setCentralWidget(splitter)

    def update_inputs(self):
        current_time = time.time() - self.start_time
        self.ai_time.append(current_time)
        if len(self.ai_time) > 1000:
            self.ai_time.pop(0)

        for ch in self.ai_labels:
            try:
                with nidaqmx.Task() as task:
                    task.ai_channels.add_ai_voltage_chan(f"NIUSB_network/{ch}")
                    value = task.read()
                    self.ai_labels[ch].setText(f"{value:.3f} V")
                    self.ai_data[ch].append(value)
                    if len(self.ai_data[ch]) > 1000:
                        self.ai_data[ch].pop(0)
                    if self.ai_checkboxes[ch].isChecked():
                        time_filtered = [t for t in self.ai_time if t >= current_time - self.time_window]
                        data_filtered = self.ai_data[ch][-len(time_filtered):]
                        self.plot_curves[ch].setData(time_filtered, data_filtered)
            except Exception as e:
                self.ai_labels[ch].setText("Err")
                print(f"AI Error ({ch}):", e)

        for port in [0, 1, 2]:
            combo, stack = self.io_stacks[port]
            if combo.currentIndex() == 1:
                try:
                    with nidaqmx.Task() as task:
                        task.di_channels.add_di_chan(f"NIUSB_network/port{port}/line0:7", line_grouping=LineGrouping.CHAN_PER_LINE)
                        values = task.read()
                        for i in range(8):
                            ch = f"port{port}/line{i}"
                            self.io_di_labels[ch].setText(f"{ch}: {'HIGH' if values[i] else 'LOW'}")
                except Exception as e:
                    print(f"DI Error (port{port}):", e)

    def set_ao(self, channel, line_edit):
        try:
            voltage = float(line_edit.text())
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(f"NIUSB_network/{channel}")
                task.write(voltage)
            self.config[channel] = voltage
        except Exception as e:
            print(f"AO Error ({channel}):", e)

    def toggle_do(self, channel, button):
        try:
            port_line = channel.split("/")[-1]
            port = port_line.split("line")[0].replace("port", "")
            line = int(port_line.split("line")[-1])
            state = button.isChecked()
            with nidaqmx.Task() as task:
                task.do_channels.add_do_chan(f"NIUSB_network/{channel}")
                task.write(state)
            button.setText(f"{channel}: {'ON' if state else 'OFF'}")
        except Exception as e:
            print(f"DO Error ({channel}):", e)

    def update_time_window(self, value):
        self.time_window = value
        self.config["time_window"] = value

    def export_csv_dialog(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export CSV", "ai_data.csv", "CSV Files (*.csv)")
        if fname:
            try:
                with open(fname, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    header = ["Time"] + list(self.ai_data.keys())
                    writer.writerow(header)
                    for i in range(len(self.ai_time)):
                        row = [self.ai_time[i]]
                        for ch in self.ai_data:
                            try:
                                row.append(self.ai_data[ch][i])
                            except IndexError:
                                row.append("")
                        writer.writerow(row)
            except Exception as e:
                print("CSV export error:", e)

    def save_config_dialog(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Config", "config.json", "JSON Files (*.json)")
        if fname:
            with open(fname, 'w') as f:
                json.dump(self.config, f, indent=2)

    def load_config_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON Files (*.json)")
        if fname:
            with open(fname, 'r') as f:
                self.config = json.load(f)
                for ch, le in self.ao_controls.items():
                    if ch in self.config:
                        le.setText(str(self.config[ch]))
                self.time_spin.setValue(self.config.get("time_window", 10))

    def load_config(self):
        try:
            with open("default_config.json", 'r') as f:
                self.config = json.load(f)
        except:
            pass

    def start_counter(self):
        self.reader = CounterReader(
            device_name=self.device_box.text(),
            counter=self.counter_box.text(),
            terminal=self.terminal_box.text(),
            interval=self.interval_spinbox.value()
        )
        self.reader.count_signal.connect(self.handle_count)
        self.reader.start()
        self.counter_canvas.t0 = time.time()
        self.counter_canvas.x_data = []
        self.counter_canvas.y_data = []
        self.counter_canvas.time_window = self.time_window_spinbox.value()
        self.data_log = []
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_counter(self):
        if self.reader:
            self.reader.stop()
            self.reader = None
        if self.save_checkbox.isChecked():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f".\logs\counter_log_{timestamp}.csv"
            with open(filename, "w") as f:
                f.write("time_sec,count\n")
                for t, c in self.data_log:
                    f.write(f"{t:.3f},{c}\n")
            print(f"Saved log to {filename}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def handle_count(self, count):
        self.counter_canvas.update_plot(count)
        timestamp = time.time() - self.counter_canvas.t0
        self.data_log.append((timestamp, count))

    def closeEvent(self, event):
        self.stop_counter()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnifiedNIUSB6356GUI()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
