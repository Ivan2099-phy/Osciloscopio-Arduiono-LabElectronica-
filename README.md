# Arduino Oscilloscope

<img width="500" height="500" alt="pulsos" src="https://github.com/user-attachments/assets/37bc3e24-553f-47ed-9c32-61d6c20fdf8b" />


## Overview

This project implements a simple oscilloscope using Arduino and Python. It features an intuitive graphical user interface (GUI) designed with QT Designer, allowing users to visualize and analyze waveforms in real-time. This oscilloscope is ideal for electronics enthusiasts, students, and professionals looking for a cost-effective solution for waveform analysis.

## Features

- **Real-time Waveform Visualization**: Capture and display waveforms as they occur.
- **User-Friendly Interface**: Designed with QT Designer for an intuitive user experience.
- **Signal Analysis**: Analyze various signal parameters, such as frequency and amplitude.
- **Arduino Integration**: Utilizes Arduino for signal acquisition and processing.

## Technology Stack

- **Arduino**: For hardware control and signal processing.
- **Python**: Backend logic for data handling and analysis.
- **QT Designer**: Framework for building the graphical user interface.

## Installation

### Prerequisites

- Arduino IDE
- Python 3.x
- QT Designer
- Required Python libraries:
  ```bash
  pip install pyqt5 pyserial
Setup Instructions
Clone the Repository:

Copy
git clone https://github.com/Ivan2099-phy/Osciloscopio-Arduiono-LabElectronica-.git
cd Osciloscopio-Arduiono-LabElectronica-
Upload Arduino Code:

Open the Arduino IDE and load the Arduino code from the arduino directory.
Upload the code to your Arduino board.
Run the Python Application:

Navigate to the Python application directory.
Run the application:
Copy
python main.py
Connect Your Arduino:

Ensure your Arduino is connected to your computer via USB.
Usage
Launch the Python application.
Select the appropriate COM port for your Arduino.
Click on "Start" to begin capturing waveforms.
Use the interface to analyze and visualize the signals.
