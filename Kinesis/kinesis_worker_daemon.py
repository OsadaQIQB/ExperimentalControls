import sys
import os
import json
import threading
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kim101_pythonnet import KinesisController, MultiDeviceManager

class KinesisWorkerDaemon:
    def __init__(self):
        self.device_manager = MultiDeviceManager()
        self.running = True
        print("DEBUG: KinesisWorkerDaemon initialized", file=sys.stderr)
        
    def ensure_device_connected(self, serial_no: str) -> KinesisController:
        """Ensure device is connected (maintain connection)"""
        controller = self.device_manager.get_controller(serial_no)
        if controller is None:
            print(f"DEBUG: Connecting to new device: {serial_no}", file=sys.stderr)
            if self.device_manager.add_device(serial_no):
                controller = self.device_manager.get_controller(serial_no)
                print(f"DEBUG: Successfully connected to device: {serial_no}", file=sys.stderr)
            else:
                raise Exception(f"Failed to connect to device {serial_no}")
        elif not controller.is_connected:
            print(f"DEBUG: Reconnecting to device: {serial_no}", file=sys.stderr)
            if controller.connect():
                print(f"DEBUG: Reconnected to device {serial_no}", file=sys.stderr)
            else:
                raise Exception(f"Failed to reconnect to device {serial_no}")
        else:
            print(f"DEBUG: Device {serial_no} already connected", file=sys.stderr)
        
        return controller
    
    def process_command(self, command_data):
        """Process command"""
        try:
            command = command_data["command"]
            args = command_data.get("args", [])
            
            print(f"DEBUG: Processing command: {command} with args: {args}", file=sys.stderr)
            
            if command == "list_devices":
                devices = KinesisController.list_devices()
                print(f"DEBUG: Found devices: {devices}", file=sys.stderr)
                return {"status": "success", "data": devices}
                
            elif command == "move_to":
                serial_no, channel, position = args
                controller = self.ensure_device_connected(serial_no)
                success = controller.move_to(int(channel), int(position))
                return {"status": "success" if success else "error", "data": f"Move {'complete' if success else 'failed'}"}
                
            elif command == "jog":
                serial_no, channel, direction, step_size = args
                controller = self.ensure_device_connected(serial_no)
                success = controller.jog(int(channel), int(direction), int(step_size))
                return {"status": "success" if success else "error", "data": f"Jog {'complete' if success else 'failed'}"}
                
            elif command == "get_position":
                serial_no, channel = args
                controller = self.ensure_device_connected(serial_no)
                position = controller.get_position(int(channel))
                if position is not None:
                    return {"status": "success", "data": position}
                else:
                    return {"status": "error", "data": "Failed to get position"}
                    
            elif command == "set_zero":
                serial_no, channel = args
                controller = self.ensure_device_connected(serial_no)
                success = controller.set_position_as_zero(int(channel))
                return {"status": "success" if success else "error", "data": f"Zero {'set' if success else 'failed'}"}
                
            elif command == "disconnect_device":
                serial_no = args[0]
                self.device_manager.remove_device(serial_no)
                return {"status": "success", "data": f"Device {serial_no} disconnected"}
                
            elif command == "disconnect_all":
                self.device_manager.disconnect_all()
                return {"status": "success", "data": "All devices disconnected"}
                
            elif command == "get_connected_devices":
                connected = list(self.device_manager.controllers.keys())
                return {"status": "success", "data": connected}
                
            elif command == "shutdown":
                self.running = False
                self.device_manager.disconnect_all()
                return {"status": "success", "data": "Daemon shutting down"}
                
            else:
                return {"status": "error", "data": f"Unknown command: {command}"}
                
        except Exception as e:
            print(f"DEBUG: Command processing error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {"status": "error", "data": str(e)}
    
    def run(self):
        """Main loop - receive commands from standard input"""
        print("Kinesis Worker Daemon started")
        sys.stdout.flush()
        
        while self.running:
            try:
                # Read JSON command from standard input
                line = sys.stdin.readline()
                if not line:
                    print("DEBUG: No input received, breaking", file=sys.stderr)
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                print(f"DEBUG: Received line: {line}", file=sys.stderr)
                command_data = json.loads(line)
                result = self.process_command(command_data)
                
                # Output result as JSON
                result_json = json.dumps(result)
                print(result_json)
                sys.stdout.flush()
                print(f"DEBUG: Sent result: {result_json}", file=sys.stderr)
                
            except KeyboardInterrupt:
                print("DEBUG: KeyboardInterrupt received", file=sys.stderr)
                break
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}", file=sys.stderr)
                error_result = {"status": "error", "data": f"Invalid JSON: {e}"}
                print(json.dumps(error_result))
                sys.stdout.flush()
            except Exception as e:
                print(f"DEBUG: Main loop error: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                error_result = {"status": "error", "data": str(e)}
                print(json.dumps(error_result))
                sys.stdout.flush()
        
        # Cleanup
        print("DEBUG: Cleaning up devices", file=sys.stderr)
        self.device_manager.disconnect_all()
        print("Daemon stopped")

if __name__ == "__main__":
    daemon = KinesisWorkerDaemon()
    daemon.run()