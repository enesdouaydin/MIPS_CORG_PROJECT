# memory.py
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

@dataclass
class MemoryConfig:
    base_address: int
    size: int
    word_size: int = 2  # Changed to 2 bytes (16-bit) per word

class MemoryError(Exception):
    """Custom exception for memory-related errors."""
    pass

class MIPSMemory:
    def __init__(self, base_address: int, size: int):
        self.config = MemoryConfig(base_address, size)
        self.memory: List[int] = [0] * (size // self.config.word_size)  # 512 bytes / 2 bytes per word = 256 words
        self.data_section: Dict[str, int] = {}

    def _validate_address(self, address: int) -> None:
        """Validate memory address."""
        if address % self.config.word_size != 0:
            raise MemoryError(f"Unaligned memory access at address: 0x{address:08X}")
            
        relative_address = address - self.config.base_address
        index = relative_address // self.config.word_size
        
        if not (0 <= index < len(self.memory)):
            if not (0 <= address < self.config.base_address):
                raise MemoryError(f"Memory access out of bounds at address: 0x{address:08X}")

    def read_word(self, address: int) -> int:
        """Read a 16-bit word from memory."""
        try:
            # Handle direct memory access
            if isinstance(address, int):
                if 0 <= address < len(self.memory):
                    return self.memory[address]
                raise MemoryError(f"Memory access out of bounds at address: {address}")
            
        except Exception as e:
            raise MemoryError(f"Invalid memory access: {str(e)}")

    def write_word(self, address: int, value: int):
        """Write a 16-bit word to memory."""
        try:
            # Handle direct memory access
            if isinstance(address, int):
                if 0 <= address < len(self.memory):
                    self.memory[address] = value & 0xFFFF
                    return
                raise MemoryError(f"Memory access out of bounds at address: {address}")
            
        except Exception as e:
            raise MemoryError(f"Invalid memory access: {str(e)}")

    def is_valid_address(self, address: int) -> bool:
        # Check if address is within valid ranges
        relative_address = address - self.config.base_address
        
        # Check if address is word-aligned
        if relative_address % self.config.word_size != 0:
            return False
            
        # Convert to array index
        index = relative_address // self.config.word_size
        
        # Check primary range (relative to base address)
        if 0 <= index < len(self.memory):
            return True
            
        # Check secondary range (absolute addresses below base_address)
        if 0 <= address < self.config.base_address:
            index = address // self.config.word_size
            return 0 <= index < len(self.memory)
            
        return False

    def allocate_data(self, data_section: Dict[str, int]):
        """Initialize data section in memory."""
        self.data_section = {}
        current_address = 0
        
        # Store data sequentially in memory
        for var_name, value in data_section.items():
            if current_address < len(self.memory):
                self.memory[current_address] = value & 0xFFFF
                self.data_section[var_name] = current_address
                current_address += 1

    def update_data_memory(self, var_name: str, value: int):
        if var_name in self.data_section:
            variable_index = list(self.data_section.keys()).index(var_name)
            if 0 <= variable_index < len(self.memory):
                self.memory[variable_index] = value
                self.data_section[var_name] = value

    def get_data_memory_values(self) -> List[int]:
        return self.memory[:]