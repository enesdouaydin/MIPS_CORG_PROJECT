
# executor.py
from typing import List, Dict, Optional, Callable
from mips_commands import MIPSProcessor
from memory import MIPSMemory
import re
from pipeline import Pipeline, PipelineStage

class MIPSExecutor:
    def __init__(self, commands: MIPSProcessor, memory: MIPSMemory, labels: Dict[str, int], 
                 pc_update_callback: Callable[[int], None], ui_log_callback: Callable[[str], None], ui):
        self.commands = commands
        self.memory = memory
        self.labels = labels
        self.program_counter = 0
        self.current_line = 0
        self.pc_update_callback = pc_update_callback
        self.ui_log_callback = ui_log_callback
        self.ui = ui  # Store UI reference
        self.instructions = []
        self.pipeline = Pipeline()

    def set_instructions(self, instructions: List[dict]):
        self.instructions = instructions

    def execute_instruction(self, instruction: dict):
        # Clear previous register highlight
        self.commands.clear_highlight()
        
        # Pipeline execution
        self._execute_pipeline_stage(instruction)
        
        # Update UI with pipeline state
        self._update_pipeline_display()
        
        # Update highlight on instruction memory
        self.ui.highlight_instruction(self.current_line)
        
        self._increment_pc_and_line()

    def _execute_pipeline_stage(self, instruction: dict):
        # 1. Instruction Fetch (IF)
        self.pipeline.current_stages[PipelineStage.IF] = instruction
        
        # 2. Instruction Decode (ID)
        if self.pipeline.if_id.instruction:
            self.pipeline.current_stages[PipelineStage.ID] = self.pipeline.if_id.instruction
            
            # Parse instruction
            parts = self.pipeline.if_id.instruction['source'].split()
            command = parts[0]
            handler = self._get_instruction_handler(command)
            if handler and len(parts) > 1:
                handler(command, parts[1:])  # Execute the instruction
        
        # 3. Execute (EX)
        if self.pipeline.id_ex.instruction:
            self.pipeline.current_stages[PipelineStage.EX] = self.pipeline.id_ex.instruction
        
        # 4. Memory Access (MEM)
        if self.pipeline.ex_mem.instruction:
            self.pipeline.current_stages[PipelineStage.MEM] = self.pipeline.ex_mem.instruction
        
        # 5. Write Back (WB)
        if self.pipeline.mem_wb.instruction:
            self.pipeline.current_stages[PipelineStage.WB] = self.pipeline.mem_wb.instruction

        # Move instructions through pipeline registers
        self.pipeline.advance_pipeline()
        
        # Update pipeline registers
        self.pipeline.if_id.instruction = instruction
        
        # Enhanced hazard detection
        hazards = self.pipeline.detect_all_hazards(instruction)
        
        if hazards:
            hazard_info = self.pipeline.get_hazard_info()
            self.ui_log_callback("\nHazard Detection Results:")
            
            if hazard_info["current"]:
                self.ui_log_callback("\nCurrent Hazards:")
                for hazard in hazard_info["current"]:
                    self.ui_log_callback(f"- {hazard}")

    def _update_pipeline_display(self):
        """Update UI with pipeline information."""
        # Get current pipeline state
        pipeline_state = self.pipeline.get_pipeline_state()
        hazards = self.pipeline.get_hazards()
        forwarding = self.pipeline.get_forwarding_actions()
        
        # Log pipeline state in formatted way
        self.ui_log_callback("\n=== Clock Cycle Start ===")
        
        # Display PC
        self.ui_log_callback(f"PC: 0x{self.program_counter:04X}")
        
        # Display Pipeline Registers
        if_id_instr = self.pipeline.if_id.instruction['source'] if self.pipeline.if_id.instruction else "NOP"
        self.ui_log_callback(f"IF/ID: {if_id_instr}")
        
        # ID/EX Register
        if self.pipeline.id_ex.instruction:
            id_ex_info = (f"ID/EX: ALUOp={self.pipeline.id_ex.instruction['source'].split()[0]}, "
                         f"RegDst={bool(self.pipeline.id_ex.write_register)}, "
                         f"ALUSrc={bool(self.pipeline.id_ex.is_stall)}, "
                         f"rs={self.pipeline.id_ex.instruction['source'].split()[1] if len(self.pipeline.id_ex.instruction['source'].split()) > 1 else 'R0'}, "
                         f"rt={self.pipeline.id_ex.instruction['source'].split()[2] if len(self.pipeline.id_ex.instruction['source'].split()) > 2 else 'R0'}")
        else:
            id_ex_info = "ID/EX: ALUOp=NOP, RegDst=False, ALUSrc=False, rs=R0, rt=R0"
        self.ui_log_callback(id_ex_info)
        
        # EX/MEM Register
        ex_mem_info = (f"EX/MEM: alu_result=0x{self.pipeline.ex_mem.alu_result:04X}, "
                       f"write_reg={self.pipeline.ex_mem.write_register or 'R0'}")
        self.ui_log_callback(ex_mem_info)
        
        # MEM/WB Register
        mem_wb_info = (f"MEM/WB: write_data=0x{self.pipeline.mem_wb.write_data:04X}, "
                       f"write_reg={self.pipeline.mem_wb.write_register or 'R0'}")
        self.ui_log_callback(mem_wb_info)
        
        self.ui_log_callback("===================\n")
        
        # Update hazard display
        hazard_info = self.pipeline.get_hazard_info()
        self.ui.update_hazard_display(hazard_info)
        
        # Log forwarding actions if any
        if forwarding:
            self.ui_log_callback("\nForwarding actions:")
            for action in forwarding:
                self.ui_log_callback(f"- {action}")

    def _increment_pc_and_line(self):
        self.program_counter += 4
        self.pc_update_callback(self.program_counter)
        self.current_line += 1
        
    def _get_instruction_handler(self, command):
        instruction_map = {
            # R-Format
            "add": self._handle_r_type_arithmetic,
            "sub": self._handle_r_type_arithmetic,
            "and": self._handle_r_type_logical,
            "or": self._handle_r_type_logical,
            "xor": self._handle_r_type_logical,
            "sll": self._handle_shift,
            "srl": self._handle_shift,
            "slt": self._handle_slt,
            # I-Format
            "lw": self._handle_lw,
            "sw": self._handle_sw,
            "addi": self._handle_addi,
            "beq": self._handle_branch,
            "bne": self._handle_branch,
            "li": self._handle_li,
            "andi": self._handle_logical_immediate,
            "ori": self._handle_logical_immediate,
            # J-Format
            "j": self._handle_jump,
            "jal": self._handle_jump,
            "jr": self._handle_jr,
            # System
            "syscall": self._handle_syscall
        }
        return instruction_map.get(command)
    
    def _handle_r_type_arithmetic(self, command, parts):
        dest, src1, src2 = parts
        self.commands.execute_arithmetic(dest, src1, src2, command)

    def _handle_r_type_logical(self, command, parts):
        dest, src1, src2 = parts
        operation_map = {
            "and": lambda x, y: x & y,
            "or": lambda x, y: x | y,
            "xor": lambda x, y: x ^ y
        }
        operation = operation_map.get(command)
        if operation:
            self.commands.execute_logical(dest, src1, src2, operation)
        else:
            self.ui_log_callback(f"Error: Invalid R-type logical operation: {command}")
    
    def _handle_shift(self, command, parts):
      dest, src1, shift_amount = parts
      
      if isinstance(shift_amount, str) and shift_amount.startswith("$"):
          shift_value = self.commands.get_register_value(shift_amount)
      else:
          try:
              shift_value = int(shift_amount)
          except ValueError:
              self.ui_log_callback(f"Error: Invalid shift amount: {shift_amount}")
              return None
      
      operation_map = {
          "sll": lambda x, y: x << y,
          "srl": lambda x, y: x >> y
      }

      operation = operation_map.get(command)
      if operation:
        self.commands.execute_shift(dest, src1, shift_value, operation)
      else:
        self.ui_log_callback(f"Error: Invalid shift operation: {command}")

    def _handle_lw(self, _, parts):
        rt, offset = parts
        try:
            match = re.match(r'(-?\d+)\((\w+)\)', offset)
            if match:
                offset_val = int(match.group(1))
                base_reg = match.group(2)
                base_val = self.commands.get_register_value(base_reg)
                
                # Calculate memory address (in words, not bytes)
                memory_loc = offset_val // 2
                
                try:
                    value = self.memory.read_word(memory_loc)
                    self.commands.update_register_value(rt, value)
                    return f"Loaded 0x{value:04X} from memory location {memory_loc}"
                except MemoryError as e:
                    return f"Error reading from memory: {str(e)}"
        except Exception as e:
            return f"Error in load word: {str(e)}"

    def _handle_sw(self, _, parts):
        rt, offset = parts
        try:
            match = re.match(r'(-?\d+)\((\w+)\)', offset)
            if match:
                offset_val = int(match.group(1))
                base_reg = match.group(2)
                base_val = self.commands.get_register_value(base_reg)
                
                # Calculate memory address (in words, not bytes)
                memory_loc = offset_val // 2
                value = self.commands.get_register_value(rt)
                
                try:
                    self.memory.write_word(memory_loc, value)
                    return f"Stored 0x{value:04X} at memory location {memory_loc}"
                except MemoryError as e:
                    return f"Error writing to memory: {str(e)}"
        except Exception as e:
            return f"Error in store word: {str(e)}"

    def _handle_slt(self, _, parts):
        dest, src1, src2 = parts
        self.commands.execute_slt(dest, src1, src2)

    def _handle_branch(self, command, parts):
        reg1, reg2, label = parts
        val1 = self.commands.get_register_value(reg1)
        val2 = self.commands.get_register_value(reg2)
        
        if command == "beq" and val1 == val2:
            self._jump_to_label(label, f"Branching to {label} (PC={self.program_counter})")
        elif command == "bne" and val1 != val2:
            self._jump_to_label(label, f"Branching to {label} (PC={self.program_counter})")
    
    def _handle_jump(self, command, parts):
        label = parts[0]
        if command == "j":
           self._jump_to_label(label, f"Jumping to {label} (PC={self.program_counter})")
        elif command == "jal":
            next_instruction = self.program_counter + 4
            self.commands.update_register_value("$ra", next_instruction)
            self._jump_to_label(label, f"Jumping to {label} and storing return address (PC={self.program_counter})")

    def _jump_to_label(self, label, log_message):
      self.program_counter = self.labels[label] * 4
      self.current_line = self.labels[label]
      self.pc_update_callback(self.program_counter)
      self.ui_log_callback(log_message)

    def _handle_addi(self, _, parts):
        dest, src1, immediate = parts
        self.commands.execute_addi(dest, src1, int(immediate))
    
    def _handle_jr(self, _, parts):
        register = parts[0]
        return_address = self.commands.get_register_value(register)
        
        # Set PC to return address
        self.program_counter = return_address - 4  # Subtract 4 because PC will be incremented after this
        self.current_line = (return_address - 4) // 4
        self.pc_update_callback(self.program_counter)
        
        self.ui_log_callback(f"Returning to address {return_address:08X}")

    def _handle_li(self, _, parts):
        dest, immediate = parts
        try:
            value = int(immediate)
            self.commands.update_register_value(dest, value)
            return f"Loaded {value} into {dest}"
        except ValueError:
            return f"Error: Invalid immediate value {immediate}"

    def _handle_syscall(self, _, parts):
        service = self.commands.get_register_value("$v0")
        if service == 10:  # Exit program
            return "Program exit requested"
        return f"Syscall service {service} executed"

    def _handle_logical_immediate(self, command, parts):
        dest, src1, immediate = parts
        try:
            imm_value = int(immediate)
            self.commands.execute_logical_immediate(dest, src1, imm_value, command)
            return f"Executed {command} {dest}, {src1}, {immediate}"
        except ValueError:
            return f"Error: Invalid immediate value {immediate}"
