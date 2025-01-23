from dataclasses import dataclass
from typing import Optional, Dict, List, Set, Tuple
from enum import Enum, auto

class PipelineStage(Enum):
    IF = "Instruction Fetch"
    ID = "Instruction Decode"
    EX = "Execute"
    MEM = "Memory Access"
    WB = "Write Back"

class HazardType(Enum):
    RAW = auto()  # Read After Write
    WAW = auto()  # Write After Write
    WAR = auto()  # Write After Read
    CONTROL = auto()  # Control Hazard
    STRUCTURAL = auto()  # Structural Hazard

@dataclass
class Hazard:
    type: HazardType
    source_instr: str
    dependent_instr: str
    affected_register: str
    resolution: str

@dataclass
class PipelineRegister:
    instruction: Optional[dict] = None
    pc: int = 0
    rs_value: int = 0
    rt_value: int = 0
    rd_value: int = 0
    alu_result: int = 0
    memory_data: int = 0
    write_register: str = ""
    write_data: int = 0
    is_stall: bool = False

class Pipeline:
    def __init__(self):
        # Pipeline registers between stages
        self.if_id = PipelineRegister()
        self.id_ex = PipelineRegister()
        self.ex_mem = PipelineRegister()
        self.mem_wb = PipelineRegister()
        
        # Hazard detection unit
        self.stall_pipeline = False
        self.forward_unit_active = False
        
        # Current stage status
        self.current_stages = {
            PipelineStage.IF: None,
            PipelineStage.ID: None,
            PipelineStage.EX: None,
            PipelineStage.MEM: None,
            PipelineStage.WB: None
        }
        
        self.hazards = []
        self.forwarding_actions = []
        self.current_hazards: List[Hazard] = []
        self.resolved_hazards: List[Hazard] = []
        self.stall_cycles = 0
        self.all_hazards: List[Hazard] = []

    def detect_data_hazard(self, current_instr: dict, previous_instr: dict) -> bool:
        """Detect RAW (Read After Write) hazards."""
        if not current_instr or not previous_instr:
            return False
            
        # Extract registers from instructions
        curr_parts = current_instr['source'].split()
        prev_parts = previous_instr['source'].split()
        
        # Check for dependencies
        if len(curr_parts) >= 3 and len(prev_parts) >= 2:
            if curr_parts[2] in prev_parts[1:]:
                self.hazards.append(f"RAW hazard detected between {prev_parts[0]} and {curr_parts[0]}")
                return True
        return False

    def handle_forwarding(self, current_instr: dict, ex_instr: dict, mem_instr: dict) -> None:
        """Implement forwarding logic."""
        if not current_instr:
            return
            
        # Check if forwarding is needed
        if ex_instr and self.needs_forwarding(current_instr, ex_instr):
            self.forward_unit_active = True
            self.forwarding_actions.append(f"Forwarding from EX stage to {current_instr['source']}")
            
        elif mem_instr and self.needs_forwarding(current_instr, mem_instr):
            self.forward_unit_active = True
            self.forwarding_actions.append(f"Forwarding from MEM stage to {current_instr['source']}")

    def needs_forwarding(self, current_instr: dict, previous_instr: dict) -> bool:
        """Check if forwarding is needed between instructions."""
        if not current_instr or not previous_instr:
            return False
            
        curr_parts = current_instr['source'].split()
        prev_parts = previous_instr['source'].split()
        
        # Check register dependencies
        if len(curr_parts) >= 3 and len(prev_parts) >= 2:
            return curr_parts[2] in prev_parts[1:]
        return False

    def advance_pipeline(self) -> None:
        """Advance the pipeline by one cycle."""
        # Move instructions through pipeline registers
        self.mem_wb = self.ex_mem
        self.ex_mem = self.id_ex
        self.id_ex = self.if_id
        self.if_id = PipelineRegister()
        
        # Update current stage status
        self.current_stages[PipelineStage.WB] = self.current_stages[PipelineStage.MEM]
        self.current_stages[PipelineStage.MEM] = self.current_stages[PipelineStage.EX]
        self.current_stages[PipelineStage.EX] = self.current_stages[PipelineStage.ID]
        self.current_stages[PipelineStage.ID] = self.current_stages[PipelineStage.IF]
        self.current_stages[PipelineStage.IF] = None
        
        # Clear hazards and forwarding actions for new cycle
        self.hazards = []
        self.forwarding_actions = []
        self.forward_unit_active = False

    def get_pipeline_state(self) -> Dict[str, str]:
        """Get the current state of all pipeline stages."""
        return {
            stage.value: (
                self.current_stages[stage]['source'] 
                if self.current_stages[stage] else "Empty"
            )
            for stage in PipelineStage
        }

    def get_hazards(self) -> List[str]:
        """Get list of current hazards."""
        return self.hazards

    def get_forwarding_actions(self) -> List[str]:
        """Get list of current forwarding actions."""
        return self.forwarding_actions 

    def detect_all_hazards(self, current_instr: dict) -> List[Hazard]:
        """Detect all types of hazards for the current instruction."""
        hazards = []
        
        # Check for RAW hazards
        raw_hazards = self._detect_raw_hazards(current_instr)
        hazards.extend(raw_hazards)
        
        # Check for WAW hazards
        waw_hazards = self._detect_waw_hazards(current_instr)
        hazards.extend(waw_hazards)
        
        # Check for control hazards
        control_hazards = self._detect_control_hazards(current_instr)
        hazards.extend(control_hazards)
        
        self.current_hazards = hazards
        # Yeni hazardları all_hazards listesine ekle
        for hazard in hazards:
            if hazard not in self.all_hazards:  # Tekrarları önle
                self.all_hazards.append(hazard)
        
        return hazards

    def _detect_raw_hazards(self, current_instr: dict) -> List[Hazard]:
        """Detect Read After Write (RAW) hazards."""
        hazards = []
        if not current_instr:
            return hazards
            
        curr_parts = current_instr['source'].split()
        if len(curr_parts) < 2:
            return hazards
            
        # Get source registers for current instruction
        src_regs = []
        if len(curr_parts) >= 3:
            src_regs.extend(curr_parts[2:])
        
        # Check against instructions in EX and MEM stages
        for stage, instr in [(PipelineStage.EX, self.current_stages[PipelineStage.EX]),
                           (PipelineStage.MEM, self.current_stages[PipelineStage.MEM])]:
            if instr:
                prev_parts = instr['source'].split()
                if len(prev_parts) >= 2:
                    dest_reg = prev_parts[1]
                    for src_reg in src_regs:
                        if src_reg == dest_reg:
                            hazards.append(Hazard(
                                type=HazardType.RAW,
                                source_instr=instr['source'],
                                dependent_instr=current_instr['source'],
                                affected_register=src_reg,
                                resolution="Forwarding" if self.forward_unit_active else "Stall"
                            ))
        return hazards

    def _detect_waw_hazards(self, current_instr: dict) -> List[Hazard]:
        """Detect Write After Write (WAW) hazards."""
        hazards = []
        if not current_instr:
            return hazards
            
        curr_parts = current_instr['source'].split()
        if len(curr_parts) < 2:
            return hazards
            
        # Get destination register for current instruction
        curr_dest = curr_parts[1]
        
        # Check against instructions in pipeline
        for stage in [PipelineStage.EX, PipelineStage.MEM]:
            instr = self.current_stages[stage]
            if instr:
                prev_parts = instr['source'].split()
                if len(prev_parts) >= 2:
                    prev_dest = prev_parts[1]
                    if prev_dest == curr_dest:
                        hazards.append(Hazard(
                            type=HazardType.WAW,
                            source_instr=instr['source'],
                            dependent_instr=current_instr['source'],
                            affected_register=curr_dest,
                            resolution="Stall"
                        ))
        return hazards

    def _detect_control_hazards(self, current_instr: dict) -> List[Hazard]:
        """Detect Control Hazards (branch/jump instructions)."""
        hazards = []
        if not current_instr:
            return hazards
            
        curr_parts = current_instr['source'].split()
        if curr_parts[0] in ['beq', 'bne', 'j', 'jal', 'jr']:
            hazards.append(Hazard(
                type=HazardType.CONTROL,
                source_instr=current_instr['source'],
                dependent_instr="Next sequential instructions",
                affected_register="PC",
                resolution="Branch prediction/delay slot"
            ))
        return hazards

    def get_hazard_info(self) -> Dict[str, List[dict]]:
        """Get detailed information about current hazards."""
        hazard_info = {
            "current": [],
            "all": [],  # Tüm hazardlar için yeni liste
            "stalls": [f"Total stall cycles: {self.stall_cycles}"]
        }
        
        # Tüm hazardları ekle
        for hazard in self.all_hazards:
            hazard_info["all"].append({
                "type": hazard.type.name,
                "source": hazard.source_instr,
                "dependent": hazard.dependent_instr,
                "register": hazard.affected_register,
                "resolution": hazard.resolution
            })
        
        return hazard_info 

    def reset(self):
        """Reset pipeline state."""
        # Reset pipeline registers
        self.if_id = PipelineRegister()
        self.id_ex = PipelineRegister()
        self.ex_mem = PipelineRegister()
        self.mem_wb = PipelineRegister()
        
        # Reset hazard detection unit
        self.stall_pipeline = False
        self.forward_unit_active = False
        
        # Reset current stage status
        self.current_stages = {
            PipelineStage.IF: None,
            PipelineStage.ID: None,
            PipelineStage.EX: None,
            PipelineStage.MEM: None,
            PipelineStage.WB: None
        }
        
        # Reset hazards and forwarding
        self.hazards = []
        self.forwarding_actions = []
        self.current_hazards = []
        self.resolved_hazards = []
        self.all_hazards = []  # Explicitly clear all hazards
        self.stall_cycles = 0 