import sys
import subprocess
import json
import os
import atexit
import threading
import queue
import time
from typing import List, Optional
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTextEdit, QScrollArea,
    QMessageBox, QFileDialog, QSpinBox, QCheckBox
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QFont

CONFIG_FILE = "kinesis_config.json"
POSITION_UPDATE_MS = 2000  # Extended to 2-second interval (load reduction)

class LogManager:
    """Log management class"""
    def __init__(self, log_widget):
        self.log_widget = log_widget
        self.logs = []
        self.max_lines = 3
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add log entry"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        self.logs.append(log_entry)
        
        # Remove old logs if maximum lines exceeded
        if len(self.logs) > self.max_lines:
            self.logs = self.logs[-self.max_lines:]
        
        # Update log widget
        self.update_display()
    
    def update_display(self):
        """Update log display"""
        self.log_widget.setText("\n".join(self.logs))

# Global log manager
log_manager = None

def log_message(message: str, level: str = "INFO"):
    """Log output function"""
    global log_manager
    if log_manager:
        log_manager.add_log(message, level)
    print(f"DEBUG: {message}")  # Also maintain console output for debugging

class PositionUpdateThread(QThread):
    """Position update dedicated thread"""
    position_updated = Signal(str, int, object)  # device, channel, position
    
    def __init__(self, worker_client):
        super().__init__()
        self.worker_client = worker_client
        self.active_devices = {}  # {(device, channel): True/False}
        self.running = True
        self.mutex = threading.Lock()
    
    def add_device(self, device: str, channel: int):
        """Add device to monitoring"""
        with self.mutex:
            self.active_devices[(device, channel)] = True
            log_message(f"Added device to monitor: {device}:{channel}")
    
    def remove_device(self, device: str, channel: int):
        """Remove device from monitoring"""
        with self.mutex:
            if (device, channel) in self.active_devices:
                del self.active_devices[(device, channel)]
                log_message(f"Removed device from monitor: {device}:{channel}")
    
    def set_device_active(self, device: str, channel: int, active: bool):
        """Set device monitoring state"""
        with self.mutex:
            if (device, channel) in self.active_devices:
                self.active_devices[(device, channel)] = active
                log_message(f"Set device {device}:{channel} active: {active}")
    
    def run(self):
        """Position update loop"""
        log_message("Position update thread started")
        while self.running:
            try:
                with self.mutex:
                    devices_to_check = [(dev, ch) for (dev, ch), active in self.active_devices.items() if active]
                
                if len(devices_to_check) > 0:
                    log_message(f"Checking positions for {len(devices_to_check)} devices")
                
                for device, channel in devices_to_check:
                    if not self.running:
                        break
                    
                    if device not in ["<no device>", "<error>"]:
                        try:
                            # Shorten timeout to improve responsiveness
                            result = self.worker_client.send_command_with_timeout("get_position", 5, device, channel)
                            if result.get("status") == "success":
                                position = result.get("data")
                                self.position_updated.emit(device, channel, position)
                            else:
                                log_message(f"Position error for {device}:{channel}: {result.get('data', 'Unknown error')}", "ERROR")
                        except Exception as e:
                            log_message(f"Position update error for {device}:{channel} - {e}", "ERROR")
                
                # Wait
                self.msleep(POSITION_UPDATE_MS)
                
            except Exception as e:
                log_message(f"Position thread error: {e}", "ERROR")
                self.msleep(1000)
        
        log_message("Position update thread stopped")
    
    def stop(self):
        """Stop thread"""
        log_message("Stopping position update thread")
        self.running = False
        self.wait()

class KinesisWorkerClient:
    """Communication client with persistent worker (improved version)"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.lock = threading.Lock()
        self.request_id_counter = 0
        self.pending_requests = {}  # {request_id: queue}
        self.start_worker()
        atexit.register(self.cleanup)
    
    def start_worker(self):
        """Start worker process"""
        try:
            log_message("Starting worker daemon...")
            
            # First check if kinesis_worker_daemon.py exists
            if not os.path.exists("kinesis_worker_daemon.py"):
                log_message("kinesis_worker_daemon.py not found!", "ERROR")
                return
            
            self.process = subprocess.Popen(
                [sys.executable, "kinesis_worker_daemon.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout as well
                text=True,
                bufsize=0,  # No buffering
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            # Wait briefly and check if process started normally
            time.sleep(1)
            if self.process.poll() is not None:
                log_message(f"Worker process died immediately. Return code: {self.process.returncode}", "ERROR")
                return
            
            # Start response reading thread
            self.reader_thread = threading.Thread(target=self._read_responses, daemon=True)
            self.reader_thread.start()
            
            # Wait for and consume startup messages
            time.sleep(2)  # Give time to process startup messages
            
            # Clear queue (remove startup messages, etc.)
            while not self.response_queue.empty():
                try:
                    old_msg = self.response_queue.get_nowait()
                except queue.Empty:
                    break
            
            log_message("Worker daemon ready")
            
        except Exception as e:
            log_message(f"Failed to start worker daemon: {e}", "ERROR")
            self.process = None
    
    def _read_responses(self):
        """Read responses in separate thread"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    line = line.strip()
                    
                    if line.startswith('{') and line.endswith('}'):
                        # JSON response
                        try:
                            response = json.loads(line)
                            self.response_queue.put(("json", response))
                        except json.JSONDecodeError:
                            self.response_queue.put(("error", f"Invalid JSON: {line}"))
                    else:
                        # Normal message (startup messages, etc.)
                        self.response_queue.put(("text", line))
                else:
                    break
            except Exception as e:
                log_message(f"Reader thread error: {e}", "ERROR")
                break
    
    def _wait_for_json_response(self, timeout=10):
        """Wait for JSON response only"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                msg_type, data = self.response_queue.get(timeout=1)
                if msg_type == "json":
                    return data
                elif msg_type == "error":
                    return {"status": "error", "data": data}
                else:
                    # Ignore text messages and continue
                    continue
            except queue.Empty:
                continue
        
        log_message(f"Response timeout after {timeout}s", "ERROR")
        return {"status": "error", "data": "Response timeout"}
    
    def send_command_with_timeout(self, command: str, timeout: int, *args) -> dict:
        """Send command to worker (with timeout specification)"""
        with self.lock:
            if not self.process or self.process.poll() is not None:
                log_message("Worker process not available", "ERROR")
                return {"status": "error", "data": "Worker not available"}
            
            try:
                command_data = {
                    "command": command,
                    "args": list(args)
                }
                
                # Send command
                self.process.stdin.write(json.dumps(command_data) + "\n")
                self.process.stdin.flush()
                
                # Wait for JSON response only
                response = self._wait_for_json_response(timeout=timeout)
                
                return response                    
            except Exception as e:
                log_message(f"Send command error: {e}", "ERROR")
                return {"status": "error", "data": str(e)}
    
    def send_command(self, command: str, *args) -> dict:
        """Send command to worker (default timeout)"""
        return self.send_command_with_timeout(command, 10, *args)
    
    def cleanup(self):
        """Cleanup"""
        log_message("Cleaning up worker client...")
        if self.process and self.process.poll() is None:
            try:
                # Send shutdown command
                self.send_command_with_timeout("shutdown", 3)
                self.process.wait(timeout=3)
            except:
                log_message("Force terminating worker process", "WARN")
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except:
                    self.process.kill()

# Global worker client
worker_client = None

def get_available_devices():
    """Get list of available devices"""
    global worker_client
    if not worker_client:
        return ["<no worker>"]
    
    try:
        log_message("Getting available devices...")
        result = worker_client.send_command("list_devices")
        
        if result.get("status") == "success":
            devices = result.get("data", [])
            if devices:
                log_message(f"Found {len(devices)} devices")
                return devices
            else:
                log_message("No devices found", "WARN")
                return ["<no device>"]
        else:
            log_message(f"Device list error: {result.get('data', 'Unknown error')}", "ERROR")
            return ["<error>"]
    except Exception as e:
        log_message(f"Get devices error: {e}", "ERROR")
        return ["<error>"]

class MotorControlBlock(QWidget):
    """Single axis control block"""
    
    def __init__(self, index: int, device_choices: List[str], remove_callback, position_thread, data: dict = None):
        super().__init__()
        self.index = index
        self.device_choices = device_choices
        self.remove_callback = remove_callback
        self.position_thread = position_thread
        self.position_update_enabled = True  # Enabled by default
        self.current_device = ""
        self.current_channel = 1
        
        self._build_ui()
        
        if data:
            self.load_data(data)
        else:
            if self.device_choices:
                self.device_combo.setCurrentIndex(0)
            self.channel_spin.setValue(1)
            self._update_monitoring()
    
    def _build_ui(self):
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Title row
        title_layout = QHBoxLayout()
        self.title_label = QLabel(f"Axis {self.index + 1}")
        self.title_label.setFont(QFont("", 12, QFont.Bold))
        title_layout.addWidget(self.title_label)
        
        self.axis_name_edit = QLineEdit(f"Axis {self.index + 1}")
        self.axis_name_edit.setFixedWidth(120)
        title_layout.addWidget(self.axis_name_edit)
        
        self.update_checkbox = QCheckBox("Auto Update")
        self.update_checkbox.setChecked(True)  # Enabled by default
        self.update_checkbox.stateChanged.connect(self.toggle_position_update)
        title_layout.addWidget(self.update_checkbox)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setFixedWidth(70)
        self.remove_btn.clicked.connect(lambda: self.remove_callback(self))
        title_layout.addWidget(self.remove_btn)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Device selection row
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(self.device_choices)
        self.device_combo.setFixedWidth(140)
        self.device_combo.currentTextChanged.connect(self._on_device_changed)
        device_layout.addWidget(self.device_combo)
        
        device_layout.addWidget(QLabel("Ch:"))
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 4)
        self.channel_spin.setValue(1)
        self.channel_spin.setFixedWidth(50)
        self.channel_spin.valueChanged.connect(self._on_channel_changed)
        device_layout.addWidget(self.channel_spin)
        device_layout.addStretch()
        layout.addLayout(device_layout)
        
        # Current position + manual update row
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        self.pos_label = QLabel("?")
        self.pos_label.setFixedWidth(80)
        self.pos_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 4px; border: 1px solid #ccc; }")
        pos_layout.addWidget(self.pos_label)
        
        self.refresh_pos_btn = QPushButton("↻")
        self.refresh_pos_btn.setFixedSize(30, 25)
        self.refresh_pos_btn.clicked.connect(self.manual_position_update)
        pos_layout.addWidget(self.refresh_pos_btn)
        pos_layout.addStretch()
        layout.addLayout(pos_layout)
        
        # Jog settings + button row
        jog_layout = QHBoxLayout()
        jog_layout.addWidget(QLabel("Step:"))
        self.jog_step_input = QLineEdit("100")
        self.jog_step_input.setFixedWidth(60)
        jog_layout.addWidget(self.jog_step_input)
        
        self.left_btn = QPushButton("← -")
        self.left_btn.setFixedSize(50, 30)
        self.left_btn.clicked.connect(lambda: self.single_jog(-1))  # Changed to single jog
        jog_layout.addWidget(self.left_btn)
        
        self.right_btn = QPushButton("+ →")
        self.right_btn.setFixedSize(50, 30)
        self.right_btn.clicked.connect(lambda: self.single_jog(1))  # Changed to single jog
        jog_layout.addWidget(self.right_btn)
        jog_layout.addStretch()
        layout.addLayout(jog_layout)
        
        # Absolute move row
        move_layout = QHBoxLayout()
        move_layout.addWidget(QLabel("Go to:"))
        self.goto_input = QLineEdit()
        self.goto_input.setFixedWidth(80)
        self.goto_input.returnPressed.connect(self.absolute_move)  # Move on Enter key
        move_layout.addWidget(self.goto_input)
        
        self.move_btn = QPushButton("Move")
        self.move_btn.setFixedSize(60, 25)
        self.move_btn.clicked.connect(self.absolute_move)
        move_layout.addWidget(self.move_btn)
        
        self.zero_btn = QPushButton("Zero")
        self.zero_btn.setFixedSize(50, 25)
        self.zero_btn.clicked.connect(self.set_zero)
        move_layout.addWidget(self.zero_btn)
        move_layout.addStretch()
        layout.addLayout(move_layout)
    
    def _on_device_changed(self):
        """Process device change"""
        self._update_monitoring()
    
    def _on_channel_changed(self):
        """Process channel change"""
        self._update_monitoring()
    
    def _update_monitoring(self):
        """Update position monitoring"""
        # Remove old monitoring
        if self.current_device and self.current_channel:
            self.position_thread.remove_device(self.current_device, self.current_channel)
        
        # Add new monitoring
        self.current_device = self.device_combo.currentText()
        self.current_channel = self.channel_spin.value()
        
        if self.current_device not in ["<no device>", "<error>", "<no worker>"]:
            self.position_thread.add_device(self.current_device, self.current_channel)
            self.position_thread.set_device_active(self.current_device, self.current_channel, self.position_update_enabled)
    
    def toggle_position_update(self, state):
        """Toggle position update enable/disable"""
        self.position_update_enabled = state == Qt.CheckState.Checked.value or state == 2
        if self.current_device not in ["<no device>", "<error>", "<no worker>"]:
            self.position_thread.set_device_active(self.current_device, self.current_channel, self.position_update_enabled)
    
    def update_position_display(self, device: str, channel: int, position):
        """Update position display (called from thread)"""
        if device == self.current_device and channel == self.current_channel:
            self.pos_label.setText(str(position))
            self.pos_label.setStyleSheet("QLabel { background-color: #e8f5e8; padding: 4px; border: 1px solid #90EE90; }")
    
    def send_command(self, command: str, *args) -> dict:
        """Send command to worker"""
        global worker_client
        if not worker_client:
            return {"status": "error", "data": "Worker not available"}
        return worker_client.send_command(command, *args)
    
    def single_jog(self, direction: int):
        """Single jog movement"""
        device = self.device_combo.currentText()
        channel = self.channel_spin.value()
        step = self.jog_step_input.text()
        
        if device in ["<no device>", "<error>", "<no worker>"]:
            log_message("No device selected for jog", "WARN")
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        try:
            step_size = int(step)
            log_message(f"Jog {device}:{channel} dir:{direction} step:{step_size}")
            result = self.send_command("jog", device, channel, direction, step_size)
            
            if result.get("status") != "success":
                log_message(f"Jog failed: {result.get('data', 'Unknown error')}", "ERROR")
                QMessageBox.warning(self, "Jog Error", result.get("data", "Unknown error"))
            else:
                # Wait briefly after jog, then manually update position
                QTimer.singleShot(300, self.manual_position_update)
        except ValueError:
            log_message("Invalid step size for jog", "ERROR")
            QMessageBox.warning(self, "Error", "Invalid step size")
    
    def absolute_move(self):
        """Absolute position movement"""
        device = self.device_combo.currentText()
        channel = self.channel_spin.value()
        position = self.goto_input.text()
        
        if device in ["<no device>", "<error>", "<no worker>"]:
            log_message("No device selected for move", "WARN")
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        try:
            pos = int(position)
            log_message(f"Move {device}:{channel} to position {pos}")
            result = self.send_command("move_to", device, channel, pos)
            
            if result.get("status") != "success":
                log_message(f"Move failed: {result.get('data', 'Unknown error')}", "ERROR")
                QMessageBox.warning(self, "Move Error", result.get("data", "Unknown error"))
            else:
                # Wait briefly after move, then manually update position
                QTimer.singleShot(1000, self.manual_position_update)
        except ValueError:
            log_message("Invalid position for move", "ERROR")
            QMessageBox.warning(self, "Error", "Invalid position")
    
    def set_zero(self):
        """Set current position as zero point"""
        device = self.device_combo.currentText()
        channel = self.channel_spin.value()
        
        if device in ["<no device>", "<error>", "<no worker>"]:
            log_message("No device selected for zero set", "WARN")
            QMessageBox.warning(self, "Error", "No device selected")
            return
        
        log_message(f"Set zero for {device}:{channel}")
        result = self.send_command("set_zero", device, channel)
        
        if result.get("status") != "success":
            log_message(f"Zero set failed: {result.get('data', 'Unknown error')}", "ERROR")
            QMessageBox.warning(self, "Zero Set Error", result.get("data", "Unknown error"))
        else:
            self.pos_label.setText("0")
            self.pos_label.setStyleSheet("QLabel { background-color: #e8f5e8; padding: 4px; border: 1px solid #90EE90; }")
    
    def manual_position_update(self):
        """Manually update position"""
        device = self.device_combo.currentText()
        channel = self.channel_spin.value()
        
        if device in ["<no device>", "<error>", "<no worker>"]:
            return
        
        try:
            result = self.send_command("get_position", device, channel)
            
            if result.get("status") == "success":
                position = result.get("data")
                self.pos_label.setText(str(position))
                self.pos_label.setStyleSheet("QLabel { background-color: #e8f5e8; padding: 4px; border: 1px solid #90EE90; }")
            else:
                self.pos_label.setText("Error")
                self.pos_label.setStyleSheet("QLabel { background-color: #ffe8e8; padding: 4px; border: 1px solid #ff6666; }")
        except Exception as e:
            log_message(f"Position update error: {e}", "ERROR")
            self.pos_label.setText("?")
            self.pos_label.setStyleSheet("QLabel { background-color: #ffe8e8; padding: 4px; border: 1px solid #ff6666; }")
    
    def get_data(self) -> dict:
        """Get configuration data"""
        return {
            "device": self.device_combo.currentText(),
            "channel": self.channel_spin.value(),
            "axis_name": self.axis_name_edit.text(),
            "jog_step": self.jog_step_input.text(),
            "goto": self.goto_input.text(),
            "auto_update": self.update_checkbox.isChecked(),
        }
    
    def load_data(self, data: dict):
        """Load configuration data"""
        device = data.get("device", self.device_choices[0] if self.device_choices else "")
        if device and device not in self.device_choices:
            self.device_combo.addItem(device)
        
        idx = self.device_combo.findText(device)
        if idx >= 0:
            self.device_combo.setCurrentIndex(idx)
        
        self.channel_spin.setValue(data.get("channel", 1))
        self.axis_name_edit.setText(data.get("axis_name", f"Axis {self.index + 1}"))
        self.jog_step_input.setText(data.get("jog_step", "100"))
        self.goto_input.setText(data.get("goto", ""))
        self.update_checkbox.setChecked(data.get("auto_update", True))
        self.position_update_enabled = data.get("auto_update", True)
        self._update_monitoring()
    
    def cleanup(self):
        """Cleanup"""
        if self.current_device and self.current_channel:
            self.position_thread.remove_device(self.current_device, self.current_channel)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.blocks = []
        
        # First initialize worker client
        global worker_client, log_manager
        worker_client = KinesisWorkerClient()
        
        # Start position update thread
        self.position_thread = PositionUpdateThread(worker_client)
        self.position_thread.position_updated.connect(self._on_position_updated)
        self.position_thread.start()
        
        # Build UI
        self._build_ui()
        
        # Initialize log manager (after UI is built)
        log_manager = LogManager(self.log_display)
        
        # Get device list
        log_message("MainWindow initializing...")
        self.available_devices = get_available_devices()
        
        self.config_file = CONFIG_FILE
        self.load_config()
    
    def _on_position_updated(self, device: str, channel: int, position):
        """Position update event"""
        for block in self.blocks:
            block.update_position_display(device, channel, position)
    
    def _build_ui(self):
        self.setWindowTitle("Thorlabs Kinesis Controller GUI")
        self.setGeometry(200, 200, 800, 700)  # Expand window size
        
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        
        main_layout = QVBoxLayout(self)
        
        # Log display area (fixed 3 lines)
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("System Log:"))
        self.log_display = QLabel()
        self.log_display.setFixedHeight(60)  # Height for 3 lines
        self.log_display.setStyleSheet("""
            QLabel {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                padding: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        self.log_display.setAlignment(Qt.AlignTop)
        self.log_display.setWordWrap(True)
        log_layout.addWidget(self.log_display)
        main_layout.addLayout(log_layout)
        
        # Configuration file display
        self.config_label = QLabel(f"Config: {CONFIG_FILE}")
        main_layout.addWidget(self.config_label)
        
        # Device status display
        self.device_status_label = QLabel("Devices: Loading...")
        main_layout.addWidget(self.device_status_label)
        
        # Axis count display
        self.axis_count_label = QLabel("Axes: 0/12")
        main_layout.addWidget(self.axis_count_label)
        
        # Control button row
        control_layout = QHBoxLayout()
        
        self.add_axis_btn = QPushButton("Add Axis")
        self.add_axis_btn.clicked.connect(self.add_axis)
        control_layout.addWidget(self.add_axis_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_config_dialog)
        control_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self.load_config_dialog)
        control_layout.addWidget(self.load_btn)
        
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        control_layout.addWidget(self.refresh_btn)
        
        self.disconnect_all_btn = QPushButton("Disconnect All")
        self.disconnect_all_btn.clicked.connect(self.disconnect_all_devices)
        control_layout.addWidget(self.disconnect_all_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)
    
    def add_axis(self):
        """Add axis"""
        if len(self.blocks) >= 12:  # Changed to 12 axes
            log_message("Maximum 12 axes supported", "WARN")
            QMessageBox.warning(self, "Limit", "Maximum 12 axes supported")
            return
        
        log_message(f"Added Axis {len(self.blocks) + 1}")
        block = MotorControlBlock(len(self.blocks), self.available_devices, self.remove_block, self.position_thread)
        self.blocks.append(block)
        self.scroll_layout.addWidget(block)
        self._update_axis_count()
    
    def remove_block(self, block):
        """Remove axis"""
        log_message(f"Removed Axis {block.index + 1}")
        block.cleanup()
        self.scroll_layout.removeWidget(block)
        self.blocks.remove(block)
        block.deleteLater()
        self._reindex_blocks()
        self._update_axis_count()
    
    def _reindex_blocks(self):
        """Renumber axis indices"""
        for i, block in enumerate(self.blocks):
            block.index = i
            block.title_label.setText(f"Axis {i + 1}")
    
    def _update_axis_count(self):
        """Update axis count display"""
        self.axis_count_label.setText(f"Axes: {len(self.blocks)}/12")
        
        # Disable Add Axis button when 12 axes reached
        self.add_axis_btn.setEnabled(len(self.blocks) < 12)
    
    def refresh_devices(self):
        """Update device list"""
        log_message("Refreshing device list...")
        self.available_devices = get_available_devices()
        self.device_status_label.setText(f"Devices: {', '.join(self.available_devices)}")
        
        for block in self.blocks:
            current_device = block.device_combo.currentText()
            block.device_combo.clear()
            block.device_combo.addItems(self.available_devices)
            
            idx = block.device_combo.findText(current_device)
            if idx >= 0:
                block.device_combo.setCurrentIndex(idx)
    
    def save_config_dialog(self):
        """Configuration save dialog"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Config", self.config_file, "JSON Files (*.json)"
        )
        if path:
            self.save_config(path)
    
    def load_config_dialog(self):
        """Configuration load dialog"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Config", "", "JSON Files (*.json)"
        )
        if path:
            self.load_config(path)
    
    def save_config(self, path=None):
        """Save configuration"""
        if path is None:
            path = self.config_file
        
        data = []
        for block in self.blocks:
            data.append(block.get_data())
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.config_file = path
            self.config_label.setText(f"Config: {path}")
            log_message(f"Config saved: {os.path.basename(path)}")
        except Exception as e:
            log_message(f"Save failed: {e}", "ERROR")
            QMessageBox.warning(self, "Save Failed", str(e))
    
    def load_config(self, path=None):
        """Load configuration"""
        if path is None:
            path = self.config_file
        
        if not os.path.exists(path):
            self._update_axis_count()  # Update axis count display
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Warn if configuration contains more than 12 axes
            if len(data) > 12:
                log_message(f"Config contains {len(data)} axes, loading only first 12", "WARN")
                QMessageBox.warning(self, "Config Warning", f"Configuration contains {len(data)} axes.\nOnly the first 12 axes will be loaded.")
                data = data[:12]  # Load only first 12 axes
            
            # Clear existing blocks
            for block in self.blocks[:]:
                self.remove_block(block)
            
            # Restore blocks from configuration
            for item in data:
                if len(self.blocks) >= 12:  # Safety check
                    break
                block = MotorControlBlock(len(self.blocks), self.available_devices, self.remove_block, self.position_thread, item)
                self.blocks.append(block)
                self.scroll_layout.addWidget(block)
            
            self.config_file = path
            self.config_label.setText(f"Config: {path}")
            if len(data) > 0:
                log_message(f"Config loaded: {os.path.basename(path)} ({len(self.blocks)} axes)")
            
            self._update_axis_count()  # Update axis count display
            
        except Exception as e:
            log_message(f"Load failed: {e}", "ERROR")
            QMessageBox.warning(self, "Load Failed", str(e))
            self._update_axis_count()  # Also update axis count display on error
    
    def disconnect_all_devices(self):
        """Disconnect all devices"""
        global worker_client
        if worker_client:
            log_message("Disconnecting all devices...")
            result = worker_client.send_command("disconnect_all")
            if result.get("status") == "success":
                log_message("All devices disconnected")
                QMessageBox.information(self, "Success", result.get("data", "Disconnected"))
            else:
                log_message(f"Disconnect failed: {result.get('data', 'Unknown error')}", "ERROR")
                QMessageBox.warning(self, "Error", result.get("data", "Unknown error"))
    
    def closeEvent(self, event):
        """Cleanup on application exit"""
        log_message("Application closing...")
        self.position_thread.stop()
        for block in self.blocks:
            block.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())