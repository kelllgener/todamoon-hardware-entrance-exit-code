# TODAMOON Hardware Entrance/Exit Code

This repository contains the backend logic for the **TODAMOON** scanner system using an **ESP32-Cam** module. The scanner is designed to monitor entrance and exit events in real-time.

---

## ​ Project Structure

- `entrance-scanner.py`  
  - For detecting and processing entrance events from the ESP32-Cam.

- `exit-scanner.py`  
  - For detecting and processing exit events.

- `modified-entrance-scanner.py`  
  - An updated or experimental version of the entrance scanner script with improvements.
 
- `entranceScannerCamera`  
  - Directory containing ESP32-Cam entrance scanner programs written in C and C++.

- `exitScannerCamera`  
  - Directory containing ESP32-Cam exit scanner programs written in C and C++.

- `.gitignore`  
  - Files and folders to exclude from version control.

---

##  Getting Started

### Prerequisites

- **Hardware**: ESP32-Cam module
- **Software**:
  - Python 3.x
  - Required Python libraries (e.g., 'opencv-python', 'numpy', 'aiohttp', 'pycryptodome', 'firebase-admin', 'psutil') depending on script requirements

### Setup Instructions

1. **Clone the repository**  
   ```bash
   git clone https://github.com/kelllgener/todamoon-hardware-entrance-exit-code.git
   cd todamoon-hardware-entrance-exit-code
