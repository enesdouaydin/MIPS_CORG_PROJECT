# main.py
import tkinter as tk
from interface import MIPSUI
from mips_commands import MIPSProcessor
from parser import MIPSParser
from memory import MIPSMemory
from executor import MIPSExecutor
from converter import MIPSConverter
from pipeline import Pipeline

class MIPSSimulator:
    DATA_SECTION_PROCESSED = "Data section processed. Ready to step through text segment."
    TEXT_SECTION_LOADED = "Loaded instructions. Ready to step through."
    NO_INSTRUCTIONS_TO_EXECUTE = "No more instructions to execute."
    NO_CODE_LOADED = "No code loaded."
    MIPS_CONVERTED = "MIPS code converted to machine code."
    WORD_SIZE = 2  # Changed to 2 bytes (16-bit)
    MEMORY_SIZE = 512  # 512 bytes total memory

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("16-bit MIPS Simulator")
        self.root.geometry("1400x1100")

        self.data_memory_base = 0x1000  # Simplified address space for 16-bit
        self.data_memory_size = self.MEMORY_SIZE // self.WORD_SIZE  # 256 words
        self.instruction_memory_size = self.MEMORY_SIZE // self.WORD_SIZE  # 256 instructions
        self.memory = MIPSMemory(self.data_memory_base, self.data_memory_size)
        self.parser = MIPSParser()
        self.ui = MIPSUI(root, self.data_memory_base, self._update_program_counter)
        self.processor = MIPSProcessor(self.ui.get_register_tree())
        self.executor = None
        self.instructions = []
        self.labels = {}
        self.text_section_loaded = False
        self.converter = MIPSConverter()

        self.ui._run_button_action = self._run_button_action
        self.ui._step_button_action = self._step_button_action
        self.ui._convert_button_action = self._convert_button_action
        
    def _update_program_counter(self, pc):
        self.ui.update_program_counter_display(pc)
        
    def _load_sections(self):
        code = self.ui.get_mips_code()
        lines = [line.strip() for line in code.split('\n') if line.strip()]

        data_section = self.parser.parse_data_section(lines)
        data_section = {k: v & 0xFFFF for k, v in data_section.items()}
        self.memory.allocate_data(data_section)
        self.ui.log_to_console(f"Data Section: {data_section}")
        self.ui.update_data_memory_display(self.memory.get_data_memory_values())

        self.instructions = self.parser.parse_text_section(lines)
        self.labels = self.parser.map_labels([instr["source"] for instr in self.instructions])
        self.ui.set_instruction_memory(self.instructions)
        
        self.executor = MIPSExecutor(
            self.processor,
            self.memory,
            self.labels,
            self._update_program_counter,
            self.ui.log_to_console,
            self.ui
        )
        
        # Update R7 (return address register) with program end
        self.processor.update_register_value("R7", len(self.instructions) * 2)
        self.ui.log_to_console(f"Set R7 (return address) to {len(self.instructions) * 2}")
        
        self.ui.log_to_console(self.TEXT_SECTION_LOADED)
        self.executor.set_instructions(self.instructions)
        self.text_section_loaded = True
        self.executor.current_line = 0
        self.executor.program_counter = 0
        self._update_program_counter(0)
      
    def _run_button_action(self):
        self.memory = MIPSMemory(self.data_memory_base, self.data_memory_size)  # Clear data memory with 512 byte size
        self.processor.clear_registers() # Clear registers
        self._load_sections()
        self.text_section_loaded = True # set the flag to true after loading

    def _step_button_action(self):
        if not self.text_section_loaded:
            self._load_sections()
          
        if self.executor and self.executor.current_line < len(self.instructions):
            instruction = self.instructions[self.executor.current_line]
            self.executor.execute_instruction(instruction)
            self.ui.update_data_memory_display(self.memory.get_data_memory_values())
        else:
            if not self.executor:
                self.ui.log_to_console(self.NO_CODE_LOADED)
            elif self.executor.current_line >= len(self.instructions):
                self.ui.log_to_console(self.NO_INSTRUCTIONS_TO_EXECUTE)
            

    def _convert_button_action(self):
        code = self.ui.get_mips_code()
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        text_instructions = self.parser.parse_text_section(lines)
        machine_code_pairs = []

        for instruction in text_instructions:
            try:
                machine_code_instr = self.converter.convert_to_machine_code(instruction['source'])
                machine_code_pairs.append((instruction['source'], machine_code_instr))
            except Exception as e:
                machine_code_pairs.append((instruction['source'],f"Error: {str(e)}"))

        self.ui.set_machine_code_output(machine_code_pairs)
        self.ui.log_to_console(self.MIPS_CONVERTED)

    def _clear_registers(self):
        # Clear console
        self.ui.console_output.delete('1.0', 'end')
        
        # Clear instruction memory
        for item in self.ui.instruction_memory_tree.get_children():
            self.ui.instruction_memory_tree.delete(item)

        # Clear machine code
        for item in self.ui.machine_code_tree.get_children():
            self.ui.machine_code_tree.delete(item)
        
        # Clear data memory
        initial_values = ["0x0000"] * 16
        for i in self.ui.data_memory_tree.get_children():
            self.ui.data_memory_tree.delete(i)
        
        addresses = [f"0x{self.data_memory_base + (i*32):04X}" for i in range(8)]
        for addr in addresses:
            self.ui.data_memory_tree.insert("", "end", values=[addr] + initial_values)
        
        # Clear registers
        for item in self.ui.tree.get_children():
            self.ui.tree.set(item, column="Value", value="0x0000")
        
        # Reset pipeline state
        if self.executor:
            self.executor.pipeline = Pipeline()  # Create a new pipeline instance
        
        # Clear hazard display and force update
        self.ui.clear_hazard_display()
        self.ui.hazard_tree.update()  # Force GUI update
        
        # Reset program counter
        self.ui.update_program_counter_display(0)
        self.program_counter_callback(0)
        
        # Reset text section loaded flag
        self.text_section_loaded = False


if __name__ == "__main__":
    root = tk.Tk()
    MIPSSimulator(root)
    root.mainloop()