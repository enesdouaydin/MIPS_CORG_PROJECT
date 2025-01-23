#register_data.py
from typing import List, Dict, TypedDict

class Register(TypedDict):
    name: str
    number: int
    value: str

class MIPSRegisters:
    @staticmethod
    def create_register(name: str, number: int) -> Register:
        return {
            "name": name,
            "number": number,
            "value": "0x0000"
        }

    @classmethod
    def get_registers(cls) -> List[Register]:
        register_definitions = [
            (f"R{i}", i) for i in range(8)
        ]
        
        return [cls.create_register(name, number) for name, number in register_definitions]

register = MIPSRegisters.get_registers()