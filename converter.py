# converter.py
from typing import Optional, Dict, Match
import re
from dataclasses import dataclass

@dataclass
class InstructionFormat:
    opcode: str
    rs: str = "00000"
    rt: str = "00000"
    rd: str = "00000"
    shamt: str = "00000"
    funct: str = "000000"
    immediate: str = "0000000000000000"
    address: str = "00000000000000000000000000"

class MIPSConverter:
    def __init__(self):
        self._load_instruction_maps()
        self._compile_regex_patterns()

    def _load_instruction_maps(self) -> None:
        """Load instruction mapping dictionaries."""
        # Updated for 8 registers (R0-R7)
        self.REGISTER_MAP = {
            f"R{i}": format(i, '03b') for i in range(8)  # 3 bits for register addressing
        }
        
        # Simplified instruction set for 16-bit instructions
        self.OPCODE_MAP = {
            "add": "000",  # Example format: 000 rrr rrr rrr xxx
            "sub": "001",
            "and": "010",
            "or":  "011",
            "lw":  "100",  # Example format: 100 rrr rrr xxxxxxx
            "sw":  "101",
            "beq": "110",
            "j":   "111"   # Example format: 111 xxxxxxxxxxxxx
        }

    def _compile_regex_patterns(self) -> None:
        """Compile regex patterns used in parsing."""
        self.MEMORY_ACCESS_PATTERN = re.compile(r'(-?\d+)\((\$\w+)\)')

    def convert_to_machine_code(self, instruction: str) -> str:
        """Convert MIPS instruction to 16-bit machine code."""
        try:
            parts = [part.strip() for part in instruction.replace(",", " ").split()]
            command = parts[0]
            
            # Skip labels and empty lines
            if command.endswith(":") or not command:
                return None
                
            # Convert to 16-bit instruction format
            if command in ["add", "sub", "and", "or"]:
                # R-type format: opcode(3) rs(3) rt(3) rd(3) unused(4)
                rd, rs, rt = parts[1:]
                opcode = self.OPCODE_MAP[command]
                rs_bin = self.REGISTER_MAP[rs]
                rt_bin = self.REGISTER_MAP[rt]
                rd_bin = self.REGISTER_MAP[rd]
                return f"{opcode}{rs_bin}{rt_bin}{rd_bin}0000"
                
            elif command in ["lw", "sw"]:
                # I-type format: opcode(3) rs(3) rt(3) immediate(7)
                rt, offset = parts[1:]
                opcode = self.OPCODE_MAP[command]
                match = re.match(r'(-?\d+)\((\w+)\)', offset)
                if match:
                    imm = int(match.group(1)) & 0x7F  # 7-bit immediate
                    rs = match.group(2)
                    return f"{opcode}{self.REGISTER_MAP[rs]}{self.REGISTER_MAP[rt]}{format(imm, '07b')}"
                    
            elif command == "beq":
                # I-type format: opcode(3) rs(3) rt(3) immediate(7)
                rs, rt, label = parts[1:]
                opcode = self.OPCODE_MAP[command]
                rs_bin = self.REGISTER_MAP[rs]
                rt_bin = self.REGISTER_MAP[rt]
                # For branch, we'll use a placeholder immediate value
                return f"{opcode}{rs_bin}{rt_bin}0000000"
                
            elif command == "j":
                # J-type format: opcode(3) address(13)
                label = parts[1]
                opcode = self.OPCODE_MAP[command]
                # For jump, we'll use a placeholder address
                return f"{opcode}0000000000000"
                
            return None  # Return None for unsupported instructions or labels
            
        except Exception as e:
            return None  # Return None instead of error message