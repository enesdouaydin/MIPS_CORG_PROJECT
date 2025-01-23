# MIPS Simulator

This project is a MIPS architecture simulator written in Python. It allows you to execute MIPS assembly code, examine the contents of registers and memory in real-time. Additionally, it provides the ability to convert assembly code into machine code.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Code Structure](#code-structure)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This simulator is designed for students learning MIPS assembly language and developers working with this architecture. It supports basic MIPS instructions, visualizes memory and register states, and converts assembly code to machine code. The simulator offers a GUI-based interface, making it more user-friendly.

## Features

*   **Execute MIPS Assembly Instructions:** Supports basic MIPS instructions such as `add`, `sub`, `mul`, `div`, `and`, `or`, `sll`, `srl`, `addi`, `lw`, `sw`, `beq`, `bne`, `j`, `jal`, `slt`, `jr`.
*   **Register and Memory Visualization:** Real-time display of the contents of all MIPS registers and data memory.
*   **Step-by-Step Execution:** Step through the code and examine the state of registers and memory at each step.
*   **Program Counter (PC) Display:** Display and track the program counter's value at each step.
*   **Debugging:** Detection of errors such as unsupported instructions or invalid addresses, displayed as messages in the console.
*   **GUI-Based Interface:** User-friendly, interactive, and intuitive graphical interface.
*   **Assembly to Machine Code Conversion:** Convert MIPS assembly code into 32-bit machine code and display it.
*   **Memory Management:** Simulation of data and instruction memory.
*   **Console Output:** Display of events during execution (e.g., read, write, jump) in the console.

## Requirements

*   Python 3.7 or higher
*   `tkinter` library (included with Python, no extra installation needed)
*   (If you have a `requirements.txt` file, add its contents here)

## Installation

1.  Clone the project repository to your local machine:
    ```bash
    git clone [repository-address]
    cd [project-folder]
    ```
2.  Install required dependencies (if any):
    ```bash
    pip install -r requirements.txt (If exists)
    ```

## Usage

1.  To start the simulator, use the following command:
    ```bash
    python main.py
    ```
2.  In the opened GUI interface, follow these steps:
    *   Write or paste your MIPS assembly code into the text area in the top left.
    *   You can monitor the register values in the "Registers" section at the bottom left.
    *   You can see how the instructions are placed in memory in the "Instruction Memory" section on the top right.
    *   You can observe the memory contents in the "Data Memory" section in the middle right.
    *   You can view the machine code equivalent of the MIPS assembly code in the "Machine Code" section on the bottom right.
    *   Use the "Clear" button to reset all register and memory values.
    *   Use the "Run" button to run your code from the beginning.
    *   Use the "Step" button to execute your code step by step.
    *   Use the "Convert Machine Code" button to convert the entered code to machine code.
    *   You can follow the events during execution in the console.

## Code Structure

The project consists of the following main files:

*   `main.py`: The main entry point of the application, initializes the `tkinter` interface and manages other components.
*   `parser.py`: Parses MIPS assembly code and separates data and instruction sections. It also maps labels.
*   `register_data.py`: Defines the names, numbers, and initial values of MIPS registers.
*   `converter.py`: Converts MIPS assembly instructions to 32-bit machine code.
*   `executor.py`: Executes instructions, updates memory and registers, and manages control flow such as branching and jumping.
*   `mips_commands.py`: Implements the logic of MIPS instructions and updates register values.
*   `memory.py`: Simulates data and instruction memories, and manages read and write operations.
*   `interface.py`: Creates the GUI interface and handles user interaction.

