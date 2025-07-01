import sys
import os
import json
import socket
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QGridLayout, QMessageBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer, Qt
from toptica.lasersdk.dlcpro.v2_2_0 import DLCpro, NetworkConnection

CONFIG_FILE = "target_freq.json"
fontsize = 14

def load_target_freqs():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_target_freqs(values):
    data = {
        "cooling": float(values["target422"]),
        "ionization": float(values["target461"]),
        "repumper": float(values["target1092"]),
        "clock": float(values["target674"]),
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def main():
    saved = load_target_freqs()
    target_422 = saved.get("cooling", 710.962460)
    target_461 = saved.get("ionization", 650.503800)
    target_1092 = saved.get("repumper", 274.589035)
    target_674 = saved.get("clock", 444.777000)

    app = QApplication(sys.argv)

    def dummy_pixmap():
        pixmap = QPixmap(40, 20)
        pixmap.fill(Qt.lightGray)
        return pixmap

    toggle_btn_on = dummy_pixmap()
    toggle_btn_off = dummy_pixmap()

    try:
        with DLCpro(NetworkConnection('100.101.0.79')) as cooling_repumper, \
             DLCpro(NetworkConnection('100.101.0.77')) as ionize1st_quencher, \
             DLCpro(NetworkConnection('100.101.0.75')) as clock:

            win = QWidget()
            win.setWindowTitle("Locking DLpro(s) to WS7")

            labels = {}
            inputs = {}
            diffs = {}
            toggles = {}
            actuals = {}
            lock = {"target422": False, "target461": False, "target1092": False, "target674": False}

            grid = QGridLayout()
            row = 0

            def add_freq_row(label_text, key, target_value):
                nonlocal row
                label = QLabel(label_text)
                label.setStyleSheet(f"font: {fontsize}pt 'Yu Gothic UI';")
                input_ = QLineEdit(str(target_value))
                input_.setFixedWidth(150)
                input_.setStyleSheet(f"font: bold {fontsize}pt Arial;")
                diff = QLabel("0")
                diff.setStyleSheet(f"font: bold {fontsize}pt Arial;")
                actual = QLabel("--- THz")
                actual.setStyleSheet(f"font: bold {fontsize}pt Arial;")
                toggle = QPushButton()
                toggle.setIcon(toggle_btn_off)
                toggle.setCheckable(True)
                toggle.setIconSize(toggle_btn_off.size())

                inputs[key] = input_
                diffs[key] = diff
                actuals[key] = actual
                toggles[key] = toggle

                def toggle_func(checked, k=key, b=toggle):
                    lock[k] = checked
                    b.setIcon(toggle_btn_on if checked else toggle_btn_off)
                toggle.clicked.connect(toggle_func)

                grid.addWidget(label, row, 0)
                grid.addWidget(input_, row, 1)
                row += 1
                grid.addWidget(QLabel("Actual Freq."), row, 0)
                grid.addWidget(actual, row, 1)
                row += 1
                grid.addWidget(QLabel("Freq. Difference"), row, 0)
                grid.addWidget(diff, row, 1)
                grid.addWidget(toggle, row, 2)
                row += 1

            add_freq_row("Target freq. (cooling)", "target422", target_422)
            add_freq_row("Target freq. (1st ionization)", "target461", target_461)
            add_freq_row("Target freq. (repumper)", "target1092", target_1092)
            add_freq_row("Target freq. (clock)", "target674", target_674)

            btn_start = QPushButton("START")
            btn_stop = QPushButton("STOP")
            btn_save = QPushButton("Save")
            grid.addWidget(btn_start, row, 0)
            grid.addWidget(btn_stop, row, 1)
            grid.addWidget(btn_save, row + 1, 0)
            win.setLayout(grid)

            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(("100.101.0.97", 50000))
            except Exception as e:
                QMessageBox.critical(win, "Error", f"Server connection failed: {e}")
                return

            def save_clicked():
                values = {k: inputs[k].text() for k in inputs}
                save_target_freqs(values)
                QMessageBox.information(win, "Save Complete", "Target frequencies have been saved.")
            btn_save.clicked.connect(save_clicked)
            btn_stop.clicked.connect(app.quit)

            def update():
                try:
                    response = client.recv(4096)
                    raw_data = response.decode("utf-8").strip()
                    fields = raw_data.split(",")
                    freq_mhz = []
                    for f in fields[:4]:
                        digits = ''.join(filter(str.isdigit, f))[:11]  
                        freq_mhz.append(int(digits) / 1e8 if digits else 0.0)

                    keys = ["target422", "target461", "target1092", "target674"]
                    devices = {
                        "target422": cooling_repumper.laser1.dl.pc,
                        "target461": ionize1st_quencher.laser1.dl.pc,
                        "target1092": cooling_repumper.laser2.dl.pc,
                        "target674": clock.laser1.dl.pc
                    }
                    factors = {
                        "target422": 0.0002,
                        "target461": 0.0001,
                        "target1092": 0.0002,
                        "target674": 0.0002,
                    }

                    for i, key in enumerate(keys):
                        input_val = float(inputs[key].text())
                        actuals[key].setText(f"{freq_mhz[i]:.11f} THz")  
                        diff = 1e6 * (freq_mhz[i] - input_val)
                        diffs[key].setText(f"{diff:.2f}")
                        if lock[key] and abs(diff) < 10000:
                            v_now = devices[key].voltage_set.get()
                            devices[key].voltage_set.set(v_now - diff * factors[key])

                except Exception as e:
                    print("Communication error:", e)

            timer = QTimer()
            timer.timeout.connect(update)
            timer.start(100)

            win.show()
            app.exec()
            client.close()

    except Exception as e:
        print("DLCpro connection error:", e)

    client.close()


if __name__ == '__main__':
    main()
