import os
import argparse
import numpy as np
import time
import json
import socket
import threading
from wlm import WavelengthMeter

app_folder = r"C:/Program Files (x86)/HighFinesse/Wavelength Meter WS7 4935"
default_config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.json"))

class config_action(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        config_file = values
        if not os.path.isfile(config_file):
            raise argparse.ArgumentTypeError(f"config:{config_file} is not a valid file")
        if os.access(config_file, os.R_OK):
            setattr(namespace, self.dest, config_file)
        else:
            raise argparse.ArgumentTypeError(f"config:{config_file} is not a readable file")

def get_config():
    parser = argparse.ArgumentParser(description='Starts a webserver with wavemeter interface.')
    parser.add_argument('--debug', dest='debug', action='store_const', const=True,
                        help='runs the script in debug mode simulating wavelength values')
    parser.add_argument('-c', '--config', action=config_action, default=default_config_file,
                        help='path to config json file, default: config.json in the script folder')
    parser.add_argument('-r', '--root', default=None,
                        help='path where the interface will be, like localhost:8000/root/. Default is "/"')
    parser.add_argument('port', type=int, nargs='?',
                        help='server port, default: 8000')

    args = parser.parse_args()

    config = {
        "port": 8000,
        "root": "/",
        "precision": 11,
        "update_rate": 0.1,
        "debug": False,
        "channels": [{"i": i, "label": f"Channel {i+1}"} for i in range(8)]
    }

    with open(args.config, "r") as f:
        config.update(json.load(f))

    config["port"] = args.port or config["port"]
    config["root"] = "/" + (args.root or config["root"]).lstrip("/").rstrip("/")
    config["debug"] = args.debug or config["debug"]

    return config

config = get_config()
wm = WavelengthMeter(debug=config["debug"])

bind_host = "0.0.0.0"
bind_port = 50000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((bind_host, bind_port))
server.listen(5)
print(f"Server started on {bind_host}:{bind_port}")

def handle_client(client_socket, address):
    print(f"Client connected: {address}")
    try:
        while True:
            freqs = [
                int(np.floor(wm.GetFrequency(1) * 1e8)),
                int(np.floor(wm.GetFrequency(2) * 1e8)),
                int(np.floor(wm.GetFrequency(4) * 1e8)),
                int(np.floor(wm.GetFrequency(7) * 1e8))
            ]
            freq_str = ",".join(map(str, freqs))
            client_socket.sendall(freq_str.encode('utf-8'))
            time.sleep(0.1)
    except (ConnectionResetError, BrokenPipeError):
        print(f"Client disconnected: {address}")
    finally:
        client_socket.close()

while True:
    try:
        client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
        thread.start()
    except KeyboardInterrupt:
        print("Shutting down server.")
        server.close()
        break
