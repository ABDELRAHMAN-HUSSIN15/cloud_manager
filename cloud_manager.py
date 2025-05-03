import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import uuid

class VMManager:
    def __init__(self, root):
        self.root = root
        self.root.title("QEMU VM Manager")
        self.root.geometry("900x600")
        self.root.minsize(800, 600)
        
        # State variables
        self.iso_path = tk.StringVar()
        self.disk_name = tk.StringVar(value="my_vm_disk")
        self.disk_format = tk.StringVar(value="qcow2")
        self.disk_size = tk.IntVar(value=20)
        self.ram = tk.IntVar(value=2048)
        self.cpu = tk.IntVar(value=2)
        self.vm_process = None
        self.created_disks = []
        self.selected_disk = tk.StringVar()
        
        # Load previously created disks
        self.load_disks()
        
        # Setup theme and styles
        self.setup_styles()
        
        # Build the UI
        self.build_gui()
        
    def setup_styles(self):
        # Configure a modern theme
        style = ttk.Style()
        style.theme_use("clam")
        
        # Define colors
        primary_color = "#4a6baf"
        secondary_color = "#f0f2f5"
        accent_color = "#6d8ad3"
        text_color = "#333333"
        
        # Configure styles for different widgets
        style.configure("TFrame", background=secondary_color)
        style.configure("Card.TFrame", background="white", relief="flat", borderwidth=0)
        
        style.configure("TLabel", 
                        background=secondary_color, 
                        foreground=text_color, 
                        font=('Segoe UI', 11))
        style.configure("Card.TLabel", 
                        background="white", 
                        foreground=text_color, 
                        font=('Segoe UI', 11))
        style.configure("Header.TLabel", 
                        background=secondary_color, 
                        foreground=primary_color, 
                        font=('Segoe UI', 16, 'bold'))
        style.configure("Subheader.TLabel", 
                        background=secondary_color, 
                        foreground=text_color, 
                        font=('Segoe UI', 12, 'bold'))
        style.configure("Card.Subheader.TLabel", 
                        background="white", 
                        foreground=text_color, 
                        font=('Segoe UI', 12, 'bold'))
        
        style.configure("TButton", 
                        background=primary_color, 
                        foreground="white", 
                        font=('Segoe UI', 10),
                        borderwidth=0,
                        focusthickness=0,
                        padding=8)
        style.map("TButton", 
                background=[('active', accent_color), ('pressed', primary_color)])
        
        style.configure("Secondary.TButton", 
                        background="#e0e0e0", 
                        foreground=text_color)
        style.map("Secondary.TButton", 
                background=[('active', "#d0d0d0"), ('pressed', "#e0e0e0")])
        
        style.configure("Danger.TButton", 
                        background="#e74c3c", 
                        foreground="white")
        style.map("Danger.TButton", 
                background=[('active', "#c0392b"), ('pressed', "#e74c3c")])
        
        style.configure("Success.TButton", 
                        background="#2ecc71", 
                        foreground="white")
        style.map("Success.TButton", 
                background=[('active', "#27ae60"), ('pressed', "#2ecc71")])
        
        style.configure("TEntry", 
                        padding=8, 
                        fieldbackground="white",
                        font=('Segoe UI', 10))
        
        style.configure("TCombobox", 
                        padding=8,
                        font=('Segoe UI', 10))
        style.map("TCombobox", 
                fieldbackground=[('readonly', "white")])
        
        style.configure("Horizontal.TScale", 
                        troughcolor="#d0d0d0", 
                        sliderrelief="flat",
                        sliderthickness=16,
                        background=primary_color)
        
        # Configure the notebook style
        style.configure("TNotebook", 
                        background=secondary_color,
                        tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", 
                        background="#e0e0e0",
                        foreground=text_color,
                        padding=[15, 5],
                        font=('Segoe UI', 10))
        style.map("TNotebook.Tab", 
                background=[("selected", "white")],
                foreground=[("selected", primary_color)],
                expand=[("selected", [1, 1, 1, 0])])
        
        # Status bar style
        style.configure("Status.TLabel", 
                        background="#f8f9fa", 
                        foreground="#6c757d",
                        font=('Segoe UI', 10),
                        padding=5)
        
        # Set the background color for the root window
        self.root.configure(background=secondary_color)
    
    def build_gui(self):
        # Create a main frame to hold everything
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="QEMU Virtual Machine Manager", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_vm_tab()
        self.create_disk_tab()
        self.manage_disks_tab()
        
        # Status bar at the bottom
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", style="Status.TLabel")
        self.status_label.pack(fill=tk.X)
    
    def create_vm_tab(self):
        vm_frame = ttk.Frame(self.notebook)
        self.notebook.add(vm_frame, text="Create VM")
        
        # Left panel for VM configuration
        left_panel = ttk.Frame(vm_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # VM Configuration Card
        vm_config_card = ttk.Frame(left_panel, style="Card.TFrame")
        vm_config_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add some padding inside the card
        card_content = ttk.Frame(vm_config_card, style="Card.TFrame")
        card_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Card header
        ttk.Label(card_content, text="VM Configuration", style="Card.Subheader.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 15))
        
        # ISO Selection
        ttk.Label(card_content, text="ISO File:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        iso_entry = ttk.Entry(card_content, textvariable=self.iso_path, width=30)
        iso_entry.grid(row=1, column=1, sticky="we", pady=5)
        ttk.Button(card_content, text="Browse", command=self.choose_iso).grid(row=1, column=2, padx=5, pady=5)
        
        # Disk Selection
        ttk.Label(card_content, text="Select Disk:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        disk_combo = ttk.Combobox(card_content, textvariable=self.selected_disk, state="readonly", width=30)
        disk_combo.grid(row=2, column=1, sticky="we", pady=5)
        self.update_disk_combo(disk_combo)
        ttk.Button(card_content, text="Refresh", command=lambda: self.update_disk_combo(disk_combo)).grid(row=2, column=2, padx=5, pady=5)
        
        # RAM and CPU
        ttk.Label(card_content, text="RAM (MB):", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        ram_frame = ttk.Frame(card_content, style="Card.TFrame")
        ram_frame.grid(row=3, column=1, columnspan=2, sticky="we", pady=5)
        ttk.Scale(ram_frame, from_=512, to=16384, variable=self.ram, orient="horizontal").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(ram_frame, textvariable=self.ram, style="Card.TLabel", width=6).pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(card_content, text="CPU Cores:", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=5)
        cpu_frame = ttk.Frame(card_content, style="Card.TFrame")
        cpu_frame.grid(row=4, column=1, columnspan=2, sticky="we", pady=5)
        ttk.Scale(cpu_frame, from_=1, to=8, variable=self.cpu, orient="horizontal").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(cpu_frame, textvariable=self.cpu, style="Card.TLabel", width=6).pack(side=tk.RIGHT, padx=5)
        
        # Add some space
        ttk.Frame(card_content, style="Card.TFrame", height=20).grid(row=5, column=0, columnspan=3)
        
        # Action buttons
        button_frame = ttk.Frame(card_content, style="Card.TFrame")
        button_frame.grid(row=6, column=0, columnspan=3, sticky="we", pady=10)
        
        ttk.Button(button_frame, text="Start VM", style="Success.TButton", command=self.start_vm).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop VM", style="Danger.TButton", command=self.stop_vm).pack(side=tk.LEFT, padx=5)
        
        # Right panel for VM status and info
        right_panel = ttk.Frame(vm_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # VM Status Card
        vm_status_card = ttk.Frame(right_panel, style="Card.TFrame")
        vm_status_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add some padding inside the card
        status_content = ttk.Frame(vm_status_card, style="Card.TFrame")
        status_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Card header
        ttk.Label(status_content, text="VM Status", style="Card.Subheader.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Status indicator
        self.vm_status_frame = ttk.Frame(status_content, style="Card.TFrame")
        self.vm_status_frame.pack(fill=tk.X, pady=5)
        
        self.vm_status_indicator = ttk.Label(self.vm_status_frame, text="●", foreground="gray", font=('Segoe UI', 16), style="Card.TLabel")
        self.vm_status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        self.vm_status_text = ttk.Label(self.vm_status_frame, text="VM is not running", style="Card.TLabel")
        self.vm_status_text.pack(side=tk.LEFT)
        
        # VM Info
        self.vm_info_frame = ttk.Frame(status_content, style="Card.TFrame")
        self.vm_info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Make the columns expandable
        card_content.columnconfigure(1, weight=1)
        
    def create_disk_tab(self):
        disk_frame = ttk.Frame(self.notebook)
        self.notebook.add(disk_frame, text="Create Disk")
        
        # Create a card for disk creation
        disk_card = ttk.Frame(disk_frame, style="Card.TFrame")
        disk_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add some padding inside the card
        card_content = ttk.Frame(disk_card, style="Card.TFrame")
        card_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Card header
        ttk.Label(card_content, text="Create Virtual Disk", style="Card.Subheader.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        
        # Disk options
        ttk.Label(card_content, text="Disk Name:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(card_content, textvariable=self.disk_name, width=40).grid(row=1, column=1, sticky="we", pady=10)
        
        ttk.Label(card_content, text="Disk Format:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=10)
        format_combo = ttk.Combobox(card_content, textvariable=self.disk_format, values=["qcow2", "raw", "vdi", "vmdk"], state="readonly", width=40)
        format_combo.grid(row=2, column=1, sticky="we", pady=10)
        
        ttk.Label(card_content, text="Disk Size (GB):", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=10)
        size_frame = ttk.Frame(card_content, style="Card.TFrame")
        size_frame.grid(row=3, column=1, sticky="we", pady=10)
        ttk.Scale(size_frame, from_=10, to=200, variable=self.disk_size, orient="horizontal").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(size_frame, textvariable=self.disk_size, style="Card.TLabel", width=6).pack(side=tk.RIGHT, padx=5)
        
        # Create button
        button_frame = ttk.Frame(card_content, style="Card.TFrame")
        button_frame.grid(row=4, column=0, columnspan=2, sticky="we", pady=20)
        
        ttk.Button(button_frame, text="Create Disk", command=self.create_disk).pack(side=tk.LEFT)
        
        # Make the second column expandable
        card_content.columnconfigure(1, weight=1)
    
    def manage_disks_tab(self):
        manage_frame = ttk.Frame(self.notebook)
        self.notebook.add(manage_frame, text="Manage Disks")
        
        # Create a card for disk management
        manage_card = ttk.Frame(manage_frame, style="Card.TFrame")
        manage_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add some padding inside the card
        card_content = ttk.Frame(manage_card, style="Card.TFrame")
        card_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Card header
        ttk.Label(card_content, text="Manage Virtual Disks", style="Card.Subheader.TLabel").pack(anchor="w", pady=(0, 15))
        
        # Create a frame for the disk list
        self.disk_list_frame = ttk.Frame(card_content, style="Card.TFrame")
        self.disk_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a treeview for the disk list
        columns = ("name", "format", "size", "path")
        self.disk_tree = ttk.Treeview(self.disk_list_frame, columns=columns, show="headings")
        
        # Define headings
        self.disk_tree.heading("name", text="Disk Name")
        self.disk_tree.heading("format", text="Format")
        self.disk_tree.heading("size", text="Size (GB)")
        self.disk_tree.heading("path", text="Path")
        
        # Define columns
        self.disk_tree.column("name", width=150)
        self.disk_tree.column("format", width=80)
        self.disk_tree.column("size", width=80)
        self.disk_tree.column("path", width=300)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(self.disk_list_frame, orient=tk.VERTICAL, command=self.disk_tree.yview)
        self.disk_tree.configure(yscroll=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.disk_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = ttk.Frame(card_content, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Refresh", command=self.refresh_disk_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", style="Danger.TButton", command=self.delete_selected_disk).pack(side=tk.LEFT, padx=5)
        
        # Populate the disk list
        self.refresh_disk_list()
    
    def choose_iso(self):
        iso = filedialog.askopenfilename(filetypes=[("ISO Files", "*.iso")])
        if iso:
            self.iso_path.set(iso)
    
    def create_disk(self):
        name = self.disk_name.get()
        size = self.disk_size.get()
        fmt = self.disk_format.get()
        
        if not name:
            messagebox.showerror("Error", "Please enter a disk name.")
            return
        
        disk_filename = f"{name}.{fmt}"
        disk_path = os.path.abspath(disk_filename)
        
        if os.path.exists(disk_path):
            overwrite = messagebox.askyesno("Disk Exists", f"Disk '{disk_filename}' already exists. Overwrite?")
            if not overwrite:
                return
        
        try:
            self.status_label.config(text="Creating disk...")
            self.root.update()
            
            subprocess.run([
                "qemu-img", "create", "-f", fmt,
                disk_path, f"{size}G"
            ], check=True)
            
            # Add to created disks
            disk_info = {
                "id": str(uuid.uuid4()),
                "name": name,
                "format": fmt,
                "size": size,
                "path": disk_path
            }
            
            self.created_disks.append(disk_info)
            self.save_disks()
            self.refresh_disk_list()
            self.update_disk_combo()
            
            self.status_label.config(text=f"Disk '{disk_filename}' created successfully.")
            messagebox.showinfo("Success", f"Disk '{disk_filename}' created successfully.")
            
        except subprocess.CalledProcessError as e:
            self.status_label.config(text="Disk creation failed.")
            messagebox.showerror("Disk Creation Failed", str(e))
    
    def start_vm(self):
        if not self.iso_path.get():
            messagebox.showerror("Error", "Please select an ISO file.")
            return
        
        if not self.selected_disk.get():
            messagebox.showerror("Error", "Please select a disk.")
            return
        
        # Find the selected disk
        disk_path = None
        for disk in self.created_disks:
            if disk["name"] == self.selected_disk.get():
                disk_path = disk["path"]
                disk_format = disk["format"]
                break
        
        if not disk_path:
            messagebox.showerror("Error", "Selected disk not found.")
            return
        
        command = [
            "qemu-system-x86_64",
            "-cdrom", self.iso_path.get(),
            "-m", str(self.ram.get()),
            "-smp", str(self.cpu.get()),
            "-drive", f"file={disk_path},format={disk_format}"
        ]
        
        def run_vm():
            self.vm_status_indicator.config(foreground="green")
            self.vm_status_text.config(text="VM is running...")
            self.status_label.config(text="VM is running...")
            
            try:
                self.vm_process = subprocess.Popen(command)
                self.vm_process.wait()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start VM: {e}")
            finally:
                self.vm_status_indicator.config(foreground="gray")
                self.vm_status_text.config(text="VM is not running")
                self.status_label.config(text="VM stopped")
        
        threading.Thread(target=run_vm).start()
    
    def stop_vm(self):
        if self.vm_process and self.vm_process.poll() is None:
            self.vm_process.terminate()
            self.vm_status_indicator.config(foreground="gray")
            self.vm_status_text.config(text="VM stopped")
            self.status_label.config(text="VM stopped")
        else:
            messagebox.showinfo("Info", "No VM is currently running.")
    
    def load_disks(self):
        try:
            if os.path.exists("disks.json"):
                with open("disks.json", "r") as f:
                    self.created_disks = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load disks: {e}")
            self.created_disks = []
    
    def save_disks(self):
        try:
            with open("disks.json", "w") as f:
                json.dump(self.created_disks, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save disks: {e}")
    
    def refresh_disk_list(self):
        # Clear the treeview
        for item in self.disk_tree.get_children():
            self.disk_tree.delete(item)
        
        # Add disks to the treeview
        for disk in self.created_disks:
            self.disk_tree.insert("", "end", values=(
                disk["name"],
                disk["format"],
                disk["size"],
                disk["path"]
            ))
    
    def update_disk_combo(self, combo=None):
        disk_names = [disk["name"] for disk in self.created_disks]
        
        if combo:
            combo["values"] = disk_names
        else:
            # Update all comboboxes
            for child in self.root.winfo_children():
                self.update_comboboxes(child, disk_names)
    
    def update_comboboxes(self, widget, values):
        if isinstance(widget, ttk.Combobox) and widget["textvariable"] == str(self.selected_disk):
            widget["values"] = values
        
        for child in widget.winfo_children():
            self.update_comboboxes(child, values)
    
    def delete_selected_disk(self):
        selected = self.disk_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No disk selected.")
            return
        
        # Get the selected disk name
        item = self.disk_tree.item(selected[0])
        disk_name = item["values"][0]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete disk '{disk_name}'?")
        if not confirm:
            return
        
        # Find the disk in the list
        for i, disk in enumerate(self.created_disks):
            if disk["name"] == disk_name:
                # Check if the disk file exists
                if os.path.exists(disk["path"]):
                    try:
                        os.remove(disk["path"])
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete disk file: {e}")
                        return
                
                # Remove from the list
                self.created_disks.pop(i)
                self.save_disks()
                self.refresh_disk_list()
                self.update_disk_combo()
                
                self.status_label.config(text=f"Disk '{disk_name}' deleted.")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = VMManager(root)
    root.mainloop()
