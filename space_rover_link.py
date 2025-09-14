#!/usr/bin/env python3
import requests, serial.tools.list_ports

print("Python OK and venv active!")
print("Ports:", [p.device for p in serial.tools.list_ports.comports()])
r = requests.get("https://api.github.com", timeout=5)
print("HTTP status:", r.status_code)




