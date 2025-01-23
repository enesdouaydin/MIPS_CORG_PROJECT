import tkinter as tk
import tkinter.ttk as ttk
from typing import List, Dict
from register_data import register

class MIPSUI:
    def __init__(self, root: tk.Tk, data_memory_base: int, program_counter_callback):
        self.root = root
        # Set theme colors with new color scheme
        self.COLORS = {
            'bg_dark': '#220033',        # Darkest background
            'bg_light': '#1D0622',      # Dark gray
            'accent': '#A020F0',        # Purple Accent
            'text': '#ffffff',          # Light gray
            'success': '#00FF00',       # Neon Green
            'warning': '#FFEA00',       # Neon Yellow
            'error': '#FF4500',         # Neon Orange
            'raw_hazard': '#2BBF00', # Koyu kırmızı
            'waw_hazard': '#9B00B3',   # Mor
            'control_hazard': '#00BFFF', # Neon Amber
            'structural_hazard': '#B0E0E6' # Neon Light Blue
        }
        
        # Configure root window
        self.root.configure(bg=self.COLORS['bg_dark'])
        
        self.data_memory_base = data_memory_base
        self.program_counter_callback = program_counter_callback
        self.data_memory_values = [0] * (512 // 4)  # Initialize for 512 bytes / 4 bytes per word

        self._run_button_action = lambda: None
        self._step_button_action = lambda: None
        self._convert_button_action = lambda: None

        self._create_widgets()
        self._update_line_numbers()

    def _create_widgets(self):
        # Main frame styling
        self.main_frame = tk.Frame(self.root, bg=self.COLORS['bg_dark'])
        self.main_frame.pack(fill="both", expand=True)

        # Top frame for buttons and PC
        top_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg_dark'])
        top_frame.pack(side="top", fill="x", pady=(10,5))

        # Content frame - ana içerik için
        content_frame = tk.Frame(self.main_frame, bg=self.COLORS['bg_dark'])
        content_frame.pack(fill="both", expand=True, pady=10)

        # Sol taraf (editor ve console) için frame
        left_section = tk.Frame(content_frame, bg=self.COLORS['bg_dark'], width=350)
        left_section.pack(side="left", fill="both", expand=True, padx=(5,15))
        left_section.pack_propagate(False)

        # Editor frame
        self.edit_frame = tk.Frame(left_section, bg=self.COLORS['bg_light'], height=200)
        self.edit_frame.pack(fill="both", expand=True, pady=(0,10))
        self.edit_frame.pack_propagate(False)

        # Console frame
        self.console_frame = tk.Frame(left_section, bg=self.COLORS['bg_light'], height=500)
        self.console_frame.pack(fill="x", expand=False, pady=(0,5))
        self.console_frame.pack_propagate(False)

        # Sağ üst kısım için frame
        right_top_section = tk.Frame(content_frame, bg=self.COLORS['bg_dark'])
        right_top_section.pack(side="right", fill="y", padx=15)

        # Machine Code ve Register frame'leri arasına padding
        self.machine_code_frame = tk.Frame(right_top_section, bg=self.COLORS['bg_light'])
        self.machine_code_frame.pack(side="left", fill="both", padx=(0,5))

        self.register_frame = tk.Frame(right_top_section, bg=self.COLORS['bg_light'])
        self.register_frame.pack(side="right", fill="both", padx=(5,0))

        # Add hazard display frame
        self.hazard_frame = tk.Frame(right_top_section, bg=self.COLORS['bg_light'])
        self.hazard_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Hazard display title
        tk.Label(
            self.hazard_frame,
            text="Pipeline Hazards",
            font=("Arial", 10, "bold"),
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text']
        ).pack(anchor="w", padx=5, pady=2)
        
        # Create Treeview for hazard display
        columns = ("Type", "Source", "Dependent", "Register", "Resolution")
        self.hazard_tree = ttk.Treeview(
            self.hazard_frame,
            columns=columns,
            height=5,
            show='headings',
            style='Custom.Treeview'
        )
        
        # Configure columns
        for col, width in zip(columns, [60, 120, 120, 60, 80]):
            self.hazard_tree.heading(col, text=col)
            self.hazard_tree.column(col, width=width, anchor='center')
        
        self.hazard_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add scrollbar for hazard tree
        hazard_scrollbar = ttk.Scrollbar(
            self.hazard_frame,
            orient="vertical",
            command=self.hazard_tree.yview
        )
        hazard_scrollbar.pack(side="right", fill="y")
        self.hazard_tree.configure(yscrollcommand=hazard_scrollbar.set)

        # Modify bottom section to better accommodate both memory displays
        bottom_section = tk.Frame(self.main_frame, bg=self.COLORS['bg_dark'])
        bottom_section.pack(side="bottom", fill="x", pady=10)

        # Create a frame to hold both memory displays
        memory_displays_frame = tk.Frame(bottom_section, bg=self.COLORS['bg_dark'])
        memory_displays_frame.pack(fill="x", expand=True)

        # Split the memory displays frame into left and right sections
        left_memory_frame = tk.Frame(memory_displays_frame, bg=self.COLORS['bg_dark'])
        left_memory_frame.pack(side="left", fill="both", expand=True, padx=(5, 2.5))

        right_memory_frame = tk.Frame(memory_displays_frame, bg=self.COLORS['bg_dark'])
        right_memory_frame.pack(side="right", fill="both", expand=True, padx=(2.5, 5))

        # Instruction Memory Frame (Left)
        self.instruction_frame = tk.Frame(left_memory_frame, bg=self.COLORS['bg_light'])
        self.instruction_frame.pack(fill="both", expand=True)

        instruction_title_frame = tk.Frame(self.instruction_frame, bg=self.COLORS['bg_light'])
        instruction_title_frame.pack(fill='x', pady=(2,0))
        tk.Label(
            instruction_title_frame,
            text="Instruction Memory",
            font=("Arial", 10, "bold"),
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text']
        ).pack(anchor="w", padx=5, pady=2)

        # Instruction Memory TreeView with increased height
        columns = ("Address", "Source Code")
        self.instruction_memory_tree = ttk.Treeview(
            self.instruction_frame, 
            columns=columns, 
            height=8,  # Increased height to show more instructions
            show='headings',
            selectmode='browse'
        )
        
        # Configure instruction memory columns
        for col in columns:
            self.instruction_memory_tree.heading(col, text=col)
            self.instruction_memory_tree.column(col, width=170, anchor='center')
        
        # Add scrollbar for instruction memory
        instruction_scrollbar = ttk.Scrollbar(
            self.instruction_frame,
            orient="vertical",
            command=self.instruction_memory_tree.yview
        )
        instruction_scrollbar.pack(side="right", fill="y")
        self.instruction_memory_tree.configure(yscrollcommand=instruction_scrollbar.set)
        
        self.instruction_memory_tree.pack(fill="both", expand=True, padx=5, pady=5)
        # Highlight Tag configure
        self.instruction_memory_tree.tag_configure('highlight', background='#00ADB5', foreground='#EEEEEE')

        # Data Memory Frame (Right)
        self.data_frame = tk.Frame(right_memory_frame, bg=self.COLORS['bg_light'])
        self.data_frame.pack(fill="both", expand=True)

        data_title_frame = tk.Frame(self.data_frame, bg=self.COLORS['bg_light'])
        data_title_frame.pack(fill='x', pady=(2,0))
        tk.Label(
            data_title_frame,
            text="Data Memory",
            font=("Arial", 10, "bold"),
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text']
        ).pack(anchor="w", padx=5, pady=2)

        # Data Memory TreeView with increased height
        columns = ["Address"] + [f"Value(+{i*4})" for i in range(16)]
        self.data_memory_tree = ttk.Treeview(
            self.data_frame, 
            columns=columns, 
            height=8,  # Increased height to show all 8 rows
            show='headings',
            selectmode='browse'
        )

        # Configure data memory columns
        for col in columns:
            self.data_memory_tree.heading(col, text=col)
            self.data_memory_tree.column(col, width=50, anchor='center')

        # Add scrollbar for data memory
        data_scrollbar = ttk.Scrollbar(
            self.data_frame,
            orient="vertical",
            command=self.data_memory_tree.yview
        )
        data_scrollbar.pack(side="right", fill="y")
        self.data_memory_tree.configure(yscrollcommand=data_scrollbar.set)
        
        self.data_memory_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Terminal title
        tk.Label(
            self.console_frame,
            text="Terminal",
            font=("Arial", 10, "bold"),
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text']
        ).pack(anchor="w", padx=5, pady=2)

        # Console gradient frame
        console_gradient = tk.Canvas(
            self.console_frame,
            bg=self.COLORS['bg_dark'],
            highlightthickness=0,
            height=8
        )
        console_gradient.pack(fill='x', padx=5)

        # Create gradient effect
        for i in range(8):
            color = self._interpolate_color(
                self.COLORS['bg_dark'],
                self.COLORS['bg_light'],
                i/8
            )
            console_gradient.create_line(0, i, 10000, i, fill=color)
        
        # Console output
        self.console_output = tk.Text(
            self.console_frame, 
            height=15,
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['success'],
            font=('Consolas', 10),
            padx=5,
            pady=5,
            wrap='word',
            borderwidth=1,
            relief='solid'
        )
        self.console_output.pack(fill='both', expand=True, padx=5, pady=(0,5))
        
        self.console_input = tk.Entry(
            self.console_frame,
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text'],
            font=('Consolas', 10),
            borderwidth=1,
            relief='solid'
        )
        self.console_input.pack(fill='x', padx=5, pady=(5,0))

        # Add labels for each section
        register_title_frame = tk.Frame(self.register_frame, bg=self.COLORS['bg_light'])
        register_title_frame.pack(fill='x', pady=(2,0))
        tk.Label(
            register_title_frame,
            text="Registers",
            font=("Arial", 10, "bold"),
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text']
        ).pack(anchor="w", padx=5, pady=2)

        machine_code_title_frame = tk.Frame(self.machine_code_frame, bg=self.COLORS['bg_light'])
        machine_code_title_frame.pack(fill='x', pady=(2,0))
        tk.Label(
            machine_code_title_frame,
            text="Machine Code",
            font=("Arial", 10, "bold"),
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text']
        ).pack(anchor="w", padx=5, pady=2)

        # Button styling
        button_style = {
            'bg': self.COLORS['accent'],
            'fg': self.COLORS['bg_dark'],
            'font': ('Arial', 9, 'bold'),
            'width': 8,
            'relief': 'flat',
            'padx': 3,
            'pady': 3
        }
        
        tk.Button(top_frame, text="Clear", command=self._clear_registers, **button_style).pack(side='left', padx=2)
        tk.Button(top_frame, text="Run", command=lambda: self._run_button_action(), **button_style).pack(side='left', padx=2)
        tk.Button(top_frame, text="Step", command=lambda: self._step_button_action(), **button_style).pack(side='left', padx=2)
        tk.Button(top_frame, text="Convert", command=lambda: self._convert_button_action(), **button_style).pack(side='left', padx=2)

        # PC Counter Label styling
        self.pc_label = tk.Label(
            top_frame, 
            text="PC: 0x00000000",
            font=("Consolas", 11, "bold"),
            fg=self.COLORS['accent'],
            bg=self.COLORS['bg_dark']
        )
        self.pc_label.pack(side="right", padx=10)

        # Line numbers styling
        self.line_numbers = tk.Text(
            self.edit_frame,
            width=4,
            padx=2,
            pady=5,
            takefocus=0,
            border=0,
            bg=self.COLORS['bg_light'],
            fg=self.COLORS['text'],
            font=('Consolas', 10)
        )
        self.line_numbers.pack(side='left', fill='y')

        # Editor text styling
        self.edit_text = tk.Text(
            self.edit_frame, 
            wrap='none', 
            undo=True,
            bg=self.COLORS['bg_dark'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['text'],
            font=('Consolas', 10),
            pady=5,
            padx=5,
            width=30
        )
        self.edit_text.pack(side='left', fill='both', expand=True)
        self.edit_text.bind('<KeyRelease>', self._update_line_numbers)
        self.edit_text.bind("<MouseWheel>", self._on_mouse_wheel)
        self.edit_text.bind("<Control-z>", self._undo)
        self.edit_text.bind("<Control-y>", self._redo)
        
        # Treeview style configuration
        style = ttk.Style()
        
        # Configure all frames to use bg_dark
        style.configure('TFrame', background=self.COLORS['bg_dark'])
        
        # Configure Treeview and its components
        style.configure(
            "Treeview",
            background=self.COLORS['bg_dark'],
            foreground=self.COLORS['text'],
            fieldbackground=self.COLORS['bg_dark'],
            borderwidth=0
        )
        
        style.configure(
            "Treeview.Heading",
            background=self.COLORS['accent'],
            foreground=self.COLORS['bg_dark'],
            relief='flat',
            borderwidth=0,
            font=('Arial', 9, 'bold')
        )
        
        # Remove Treeview borders
        style.layout("Treeview", [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])

        # Configure selection color
        style.map('Treeview',
            background=[('selected', '#00ADB5')],
            foreground=[('selected', '#EEEEEE')]
        )

        # Custom style for all Treeviews
        style.configure(
            "Custom.Treeview",
            background=self.COLORS['bg_dark'],
            foreground=self.COLORS['text'],
            fieldbackground=self.COLORS['bg_dark'],
            borderwidth=0,
            font=('Consolas', 9)
        )

        # Update frame configurations
        for frame in [self.register_frame, self.machine_code_frame, 
                     self.instruction_frame, self.data_frame, self.hazard_frame]:
            frame.configure(
                bg=self.COLORS['bg_dark'],
                highlightthickness=0,
                borderwidth=0
            )

        # Register TreeView
        columns = ("Name", "Number", "Value")
        self.tree = ttk.Treeview(
            self.register_frame,
            columns=columns,
            height=7,
            style='Custom.Treeview',
            show='headings'
        )

        for col, width in zip(columns, [50, 50, 70]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')

        self.tree.tag_configure('evenrow', background=self.COLORS['bg_light'])
        self.tree.tag_configure('oddrow', background=self.COLORS['bg_dark'])

        for index, reg in enumerate(register):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=(
                reg["name"], 
                reg["number"], 
                "0x0000"
            ), tags=(tag,))

        self.tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Machine Code TreeView
        columns = ("Instruction", "Machine Code")
        self.machine_code_tree = ttk.Treeview(
            self.machine_code_frame, 
            columns=columns, 
            height=6,
            style='Custom.Treeview',
            show='headings'
        )

        for col, width in zip(columns, [130, 150]):
            self.machine_code_tree.heading(col, text=col)
            self.machine_code_tree.column(col, width=width, anchor='center')

        self.machine_code_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Add highlight tag for register changes
        self.tree.tag_configure('highlight', 
            background='#00ADB5',
            foreground='#EEEEEE'
        )

        # Update evenrow/oddrow colors
        self.tree.tag_configure('evenrow', 
            background=self.COLORS['bg_light'],
            foreground=self.COLORS['text']
        )
        self.tree.tag_configure('oddrow', 
            background=self.COLORS['bg_dark'],
            foreground=self.COLORS['text']
        )

        # Set background color for all treeviews
        for tree in [self.tree, self.instruction_memory_tree, 
                     self.data_memory_tree, self.machine_code_tree, self.hazard_tree]:
            tree.configure(
                style='Custom.Treeview',
                show='headings',
                selectmode='browse'
            )
            
            # Configure tags for alternating row colors
            tree.tag_configure('evenrow', 
                background=self.COLORS['bg_light'],
                foreground=self.COLORS['text']
            )
            tree.tag_configure('oddrow', 
                background=self.COLORS['bg_dark'],
                foreground=self.COLORS['text']
            )

        # Sağ üst kısım için genişlik ayarı
        self.machine_code_frame.configure(width=300)
        self.register_frame.configure(width=220)
        self.hazard_frame.configure(width=450)

        self.machine_code_frame.pack_propagate(False)
        self.register_frame.pack_propagate(False)
        self.hazard_frame.pack_propagate(False)

    def _update_line_numbers(self, event=None):
        lines = self.edit_text.get('1.0', 'end-1c').split('\n')
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        self.line_numbers.insert(
            '1.0', 
            "\n".join(str(i + 1) for i in range(len(lines)))
        )
        self.line_numbers.config(state='disabled')
        self.line_numbers.yview_moveto(self.edit_text.yview()[0])

    def _on_mouse_wheel(self, event):
        scroll_amount = -1 * (event.delta // 120)
        self.edit_text.yview_scroll(scroll_amount, "units")
        self.line_numbers.yview_scroll(scroll_amount, "units")
        return "break"

    def _undo(self, event=None):
        try:
            self.edit_text.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _redo(self, event=None):
        try:
            self.edit_text.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def _clear_registers(self):
        self.console_output.delete('1.0', 'end')
        for item in self.instruction_memory_tree.get_children():
            self.instruction_memory_tree.delete(item)

        for item in self.machine_code_tree.get_children():
            self.machine_code_tree.delete(item)

        initial_values = ["0x0000"] * 16
        for i in self.data_memory_tree.get_children():
            self.data_memory_tree.delete(i)

        addresses = [f"0x{self.data_memory_base + (i*32):04X}" for i in range(8)]

        for addr in addresses:
            self.data_memory_tree.insert("", "end", values=[addr] + initial_values)

        for item in self.tree.get_children():
            self.tree.set(item, column="Value", value="0x0000")
        self.update_program_counter_display(0)
        self.program_counter_callback(0)
        self.clear_hazard_display()

    def update_program_counter_display(self, pc: int):
        hex_pc = f"0x{pc:04X}"
        self.pc_label.config(text=f"PC: {hex_pc}")

    def update_data_memory_display(self, data_memory_values: List[int]):
        for i in self.data_memory_tree.get_children():
            self.data_memory_tree.delete(i)
            
        addresses = [f"0x{self.data_memory_base + (i*32):04X}" for i in range(8)]
        
        for addr_idx, addr in enumerate(addresses):
            row_values = [addr]
            for val_idx in range(16):
                mem_index = addr_idx * 16 + val_idx
                if mem_index < len(data_memory_values):
                    val = data_memory_values[mem_index]
                    hex_val = f"0x{val:04X}" if val is not None else "0x0000"
                    row_values.append(hex_val)
                else:
                    row_values.append("0x0000")

            self.data_memory_tree.insert("", "end", values=row_values)

    def get_mips_code(self):
        return self.edit_text.get('1.0', 'end-1c')

    def log_to_console(self, message):
        self.console_output.insert('end', f"{message}\n")
        self.console_output.see('end')

    def set_instruction_memory(self, instructions: List[dict]):
        for item in self.instruction_memory_tree.get_children():
             self.instruction_memory_tree.delete(item)
        
        for instr in instructions:
            item_id = self.instruction_memory_tree.insert("", "end", values=(
                instr['address'],
                instr['source']
            ))
            if 'highlight' in self.instruction_memory_tree.tag_has(item_id):
                self.instruction_memory_tree.item(item_id, tags='highlight')
            else:
                self.instruction_memory_tree.item(item_id, tags='')
    
    def set_machine_code_output(self, machine_code_pairs: List[tuple]):
        for item in self.machine_code_tree.get_children():
            self.machine_code_tree.delete(item)
            
        for instruction, code in machine_code_pairs:
            if code is not None:
                self.machine_code_tree.insert("", "end", values=(
                    instruction,
                    code
                ))
          
    def get_register_tree(self) -> ttk.Treeview:
        return self.tree

    def _interpolate_color(self, color1, color2, fraction):
        def hex_to_rgb(color):
            return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        
        def rgb_to_hex(rgb):
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        
        c1 = hex_to_rgb(color1)
        c2 = hex_to_rgb(color2)
        
        rgb = tuple(int(c1[i] + (c2[i] - c1[i]) * fraction) for i in range(3))
        return rgb_to_hex(rgb)

    def update_hazard_display(self, hazard_info: Dict[str, List[dict]]):
        for item in self.hazard_tree.get_children():
            self.hazard_tree.delete(item)
        
        for hazard in hazard_info["all"]:
            self.hazard_tree.insert("", "end", values=(
                hazard["type"],
                hazard["source"],
                hazard["dependent"],
                hazard["register"],
                hazard["resolution"]
            ), tags=(hazard["type"],))
        
        self.hazard_tree.tag_configure('RAW', background=self.COLORS['raw_hazard'])
        self.hazard_tree.tag_configure('WAW', background=self.COLORS['waw_hazard'])
        self.hazard_tree.tag_configure('CONTROL', background=self.COLORS['control_hazard'])
        self.hazard_tree.tag_configure('STRUCTURAL', background=self.COLORS['structural_hazard'])
        
        self.hazard_tree.yview_moveto(1)

    def clear_hazard_display(self):
        for item in self.hazard_tree.get_children():
            self.hazard_tree.delete(item)
        
        self.hazard_tree.insert("", "end", values=("", "", "", "", ""))
        
        for tag in ['RAW', 'WAW', 'CONTROL', 'STRUCTURAL']:
            self.hazard_tree.tag_configure(tag, background=self.COLORS['bg_dark'])
        
        self.hazard_tree.update()
        self.hazard_frame.update()

    def highlight_instruction(self, line_number):
        for item in self.instruction_memory_tree.get_children():
            if 'highlight' in self.instruction_memory_tree.tag_has(item):
                self.instruction_memory_tree.item(item, tags='')

        if self.instruction_memory_tree.get_children() and 0 <= line_number < len(self.instruction_memory_tree.get_children()):
            item_id = self.instruction_memory_tree.get_children()[line_number]
            self.instruction_memory_tree.item(item_id, tags='highlight')
            total_rows = len(self.instruction_memory_tree.get_children())
            visible_rows = 8  # Updated to match new height
            scroll_fraction = max(0, min(1, (line_number - visible_rows / 2) / (total_rows - visible_rows)))
            self.instruction_memory_tree.yview_moveto(scroll_fraction)
