"""
KIM101
==================

An example showing the usage of the Thorlabs Kinesis .NET API in controlling the KCube Intertial Motor Controller.
Uses the clr module from pythonnet package
Written and tested in python 3.10.5
"""
import os
import time
import clr
from typing import List, Optional, Dict

# Load Thorlabs Kinesis .NET API
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.KCube.InertialMotorCLI.dll")

from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.KCube.InertialMotorCLI import *
from System import Decimal

class KinesisController:
    """Thorlabs Kinesis multi-channel controller class"""
    
    def __init__(self, serial_no: str):
        self.serial_no = serial_no
        self.device = None
        self.is_connected = False
        self.channels = {}  # Save channel configuration
        
    def connect(self) -> bool:
        """Connect to device"""
        try:
            # Build device list
            DeviceManagerCLI.BuildDeviceList()
            
            # Check if serial number exists
            available_devices = list(DeviceManagerCLI.GetDeviceList())
            if self.serial_no not in available_devices:
                print(f"Device {self.serial_no} not found in available devices: {available_devices}")
                return False
            
            # Create device
            self.device = KCubeInertialMotor.CreateKCubeInertialMotor(self.serial_no)
            
            # Connect
            self.device.Connect(self.serial_no)
            time.sleep(0.25)
            
            # Wait for settings initialization
            if not self.device.IsSettingsInitialized():
                self.device.WaitForSettingsInitialized(10000)
                
            # Start polling and enable device
            self.device.StartPolling(250)
            time.sleep(0.25)
            self.device.EnableDevice()
            time.sleep(0.25)
            
            self.is_connected = True
            print(f"Connected to device: {self.device.GetDeviceInfo().Description}")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from device"""
        if self.device and self.is_connected:
            try:
                self.device.StopPolling()
                self.device.Disconnect()
                self.is_connected = False
                print(f"Device {self.serial_no} disconnected")
            except Exception as e:
                print(f"Disconnect error: {e}")
    
    def setup_channel(self, channel: int, step_rate: int = 500, step_acceleration: int = 100000):
        """Configure channel parameters"""
        try:
            # Get channel enumeration type
            channel_enum = self._get_channel_enum(channel)
            if channel_enum is None:
                return False
            
            # Get configuration
            inertial_motor_config = self.device.GetInertialMotorConfiguration(self.serial_no)
            device_settings = ThorlabsInertialMotorSettings.GetSettings(inertial_motor_config)
            
            # Set channel parameters
            device_settings.Drive.Channel(channel_enum).StepRate = step_rate
            device_settings.Drive.Channel(channel_enum).StepAcceleration = step_acceleration
            
            # Send settings to device
            self.device.SetSettings(device_settings, True, True)
            
            # Save channel information
            self.channels[channel] = {
                'enum': channel_enum,
                'step_rate': step_rate,
                'step_acceleration': step_acceleration
            }
            
            print(f"Channel {channel} configured: StepRate={step_rate}, Acceleration={step_acceleration}")
            return True
            
        except Exception as e:
            print(f"Channel setup error: {e}")
            return False
    
    def _get_channel_enum(self, channel: int):
        """Get enumeration type from channel number"""
        channel_map = {
            1: InertialMotorStatus.MotorChannels.Channel1,
            2: InertialMotorStatus.MotorChannels.Channel2,
            3: InertialMotorStatus.MotorChannels.Channel3,
            4: InertialMotorStatus.MotorChannels.Channel4
        }
        
        if channel not in channel_map:
            print(f"Invalid channel: {channel}. Must be 1-4.")
            return None
            
        return channel_map[channel]
    
    def move_to(self, channel: int, position: int, timeout: int = 5000) -> bool:
        """Move specified channel to absolute position"""
        if not self.is_connected:
            print("Device not connected")
            return False
            
        if channel not in self.channels:
            print(f"Channel {channel} not configured. Setting up with default parameters.")
            if not self.setup_channel(channel):
                return False
            
        try:
            chan_enum = self.channels[channel]['enum']
            print(f"Moving channel {channel} to position {position}")
            self.device.MoveTo(chan_enum, int(position), timeout)
            print(f"Channel {channel} move complete")
            return True
            
        except Exception as e:
            print(f"Move error on channel {channel}: {e}")
            return False
    
    def jog(self, channel: int, direction: int, step_size: int = 100) -> bool:
        """Jog move specified channel (direction: +1=forward, -1=reverse)"""
        if not self.is_connected:
            print("Device not connected")
            return False
            
        try:
            current_pos = self.get_position(channel)
            if current_pos is None:
                return False
                
            target_pos = current_pos + (direction * step_size)
            target_pos = max(0, min(target_pos, 65535))  # Range limit
            return self.move_to(channel, target_pos)
            
        except Exception as e:
            print(f"Jog error on channel {channel}: {e}")
            return False
    
    def get_position(self, channel: int) -> Optional[int]:
        """Get current position of specified channel"""
        if not self.is_connected:
            print("Device not connected")
            return None
            
        if channel not in self.channels:
            print(f"Channel {channel} not configured. Setting up with default parameters.")
            if not self.setup_channel(channel):
                return None
            
        try:
            chan_enum = self.channels[channel]['enum']
            position = self.device.GetPosition(chan_enum)
            return int(position)
            
        except Exception as e:
            print(f"Position read error on channel {channel}: {e}")
            return None
    
    def set_position_as_zero(self, channel: int) -> bool:
        """Set current position of specified channel as zero point"""
        if not self.is_connected:
            print("Device not connected")
            return False
            
        if channel not in self.channels:
            print(f"Channel {channel} not configured. Setting up with default parameters.")
            if not self.setup_channel(channel):
                return False
            
        try:
            chan_enum = self.channels[channel]['enum']
            self.device.SetPositionAs(chan_enum, 0)
            print(f"Channel {channel} position set as zero")
            return True
            
        except Exception as e:
            print(f"Zero set error on channel {channel}: {e}")
            return False
    
    def get_device_info(self) -> str:
        """Get device information"""
        if self.device:
            return self.device.GetDeviceInfo().Description
        return "Device not connected"
    
    @staticmethod
    def list_devices() -> List[str]:
        """Get list of available device serial numbers"""
        try:
            DeviceManagerCLI.BuildDeviceList()
            return list(DeviceManagerCLI.GetDeviceList())
        except Exception as e:
            print(f"Device list error: {e}")
            return []

class MultiDeviceManager:
    """Class for managing multiple Kinesis devices"""
    
    def __init__(self):
        self.controllers: Dict[str, KinesisController] = {}
    
    def add_device(self, serial_no: str) -> bool:
        """Add device"""
        if serial_no in self.controllers:
            print(f"Device {serial_no} already exists")
            return True  # Return True if already exists
            
        controller = KinesisController(serial_no)
        if controller.connect():
            self.controllers[serial_no] = controller
            print(f"Device {serial_no} added successfully")
            return True
        else:
            print(f"Failed to add device {serial_no}")
            return False
    
    def remove_device(self, serial_no: str):
        """Remove device"""
        if serial_no in self.controllers:
            self.controllers[serial_no].disconnect()
            del self.controllers[serial_no]
            print(f"Device {serial_no} removed")
    
    def get_controller(self, serial_no: str) -> Optional[KinesisController]:
        """Get controller for specified serial number"""
        return self.controllers.get(serial_no)
    
    def disconnect_all(self):
        """Disconnect all devices"""
        for controller in self.controllers.values():
            controller.disconnect()
        self.controllers.clear()
        print("All devices disconnected")
    
    def is_device_connected(self, serial_no: str) -> bool:
        """Check if device is connected"""
        controller = self.controllers.get(serial_no)
        return controller is not None and controller.is_connected

# Usage example
if __name__ == "__main__":
    # Display list of available devices
    available_devices = KinesisController.list_devices()
    print("Available devices:", available_devices)
    
    if not available_devices:
        print("No devices found")
        exit()
    
    # Single device example
    print("\n=== Single Device Example ===")
    controller = KinesisController("97251312")  # Specify serial number
    
    if controller.connect():
        # Configure channels 1 and 2
        controller.setup_channel(1, step_rate=500, step_acceleration=100000)
        controller.setup_channel(2, step_rate=500, step_acceleration=100000)
        
        # Move channel 1 to position 1000
        controller.move_to(1, 1000)
        
        # Move channel 2 to position 2000
        controller.move_to(2, 2000)
        
        # Check current positions
        pos1 = controller.get_position(1)
        pos2 = controller.get_position(2)
        print(f"Channel 1 position: {pos1}")
        print(f"Channel 2 position: {pos2}")
        
        # Jog movement
        controller.jog(1, 1, 100)  # Move channel 1 +100 steps
        controller.jog(2, -1, 50)  # Move channel 2 -50 steps
        
        controller.disconnect()
    
    # # Multiple devices example
    # print("\n=== Multiple Devices Example ===")
    # manager = MultiDeviceManager()
    
    # # Add all available devices
    # for device_serial in available_devices[:2]:  # Only first 2 devices
    #     manager.add_device(device_serial)
    
    # # Control each device
    # for serial_no, controller in manager.controllers.items():
    #     print(f"\nControlling device: {serial_no}")
    #     controller.setup_channel(1)
    #     controller.move_to(1, 500)
    #     pos = controller.get_position(1)
    #     print(f"Device {serial_no}, Channel 1 position: {pos}")
    
    # # Disconnect all
    # manager.disconnect_all()
