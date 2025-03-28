import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from typing import Optional
from ssh_client import SSHClient, CommandRunner
from config import CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSHApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Kal-tools")
        self.ssh_client: Optional[SSHClient] = None
        self.command_runner: Optional[CommandRunner] = None
        
        # Configure window
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Setup frames
        self._setup_frames()
        self._setup_menu()
        
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _setup_frames(self):
        """Initialize and configure all frames."""
        # Connection Frame
        self.connection_frame = ConnectionFrame(self, self._on_connect)
        self.connection_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Control Frame
        self.control_frame = ControlFrame(self, self._on_command)
        self.control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.control_frame.grid_remove()  # Hidden until connected

    def _setup_menu(self):
        """Setup application menu."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Connect", command=self._on_connect)
        file_menu.add_command(label="Disconnect", command=self._on_disconnect)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _on_connect(self):
        """Handle connection to proxy server."""
        try:
            host = self.connection_frame.host_entry.get().strip()
            username = self.connection_frame.username_entry.get().strip()
            key_path = self.connection_frame.key_path_entry.get().strip()
            passphrase = self.connection_frame.passphrase_entry.get().strip() or None

            self.ssh_client = SSHClient(host, username, key_path, passphrase)
            self.ssh_client.connect()
            
            self.command_runner = CommandRunner(self.ssh_client)
            
            # Update UI
            self.connection_frame.grid_remove()
            self.control_frame.grid()
            
            messagebox.showinfo("Success", f"Connected to proxy server: {host}")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            logger.error(f"Connection error: {str(e)}")

    def _on_disconnect(self):
        """Handle disconnection from proxy server."""
        if self.ssh_client:
            try:
                self.ssh_client.disconnect()
                self.ssh_client = None
                self.command_runner = None
                
                # Update UI
                self.control_frame.grid_remove()
                self.connection_frame.grid()
                
                messagebox.showinfo("Disconnected", "Successfully disconnected from proxy server")
            except Exception as e:
                messagebox.showerror("Disconnection Error", str(e))
                logger.error(f"Disconnection error: {str(e)}")

    def _on_command(self, client_ip: str, command: str):
        """Handle command execution."""
        if not self.command_runner:
            messagebox.showerror("Error", "Not connected to proxy server")
            return
            
        try:
            command_config = CONFIG['AVAILABLE_COMMANDS'].get(command)
            if not command_config:
                raise ValueError(f"Unknown command: {command}")
                
            if isinstance(command_config.get('command'), str):
                commands = [command_config['command']]
            else:
                commands = command_config.get('commands', [])
                
            outputs, logclient_output = self.command_runner.run_command_sequence(client_ip, commands)
            
            # Update output display
            self.control_frame.display_output(outputs, logclient_output)
        except Exception as e:
            messagebox.showerror("Command Error", str(e))
            logger.error(f"Command execution error: {str(e)}")

    def _show_about(self):
        """Show about dialog."""
        about_text = """STB Management Tool
Version 1.0

A tool for managing and troubleshooting set-top boxes
through SSH proxy connection."""
        messagebox.showinfo("About", about_text)


class ConnectionFrame(ttk.LabelFrame):
    """Frame for handling proxy server connection."""
    def __init__(self, parent, connect_callback):
        super().__init__(parent, text="Proxy Server Connection")
        self.connect_callback = connect_callback
        self._setup_ui()

    def _setup_ui(self):
        """Setup connection frame UI elements."""
        # Host
        ttk.Label(self, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.host_entry = ttk.Entry(self, width=30)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        self.host_entry.insert(0, CONFIG['DEFAULT_PROXY_HOST'])

        # Username
        ttk.Label(self, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.username_entry = ttk.Entry(self, width=30)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)
        self.username_entry.insert(0, CONFIG['DEFAULT_PROXY_USER'])

        # Key Path
        ttk.Label(self, text="Key Path:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.key_path_entry = ttk.Entry(self, width=30)
        self.key_path_entry.grid(row=2, column=1, padx=5, pady=5)
        self.key_path_entry.insert(0, CONFIG['DEFAULT_KEY_PATH'])

        # Passphrase
        ttk.Label(self, text="Passphrase:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.passphrase_entry = ttk.Entry(self, width=30, show="*")
        self.passphrase_entry.grid(row=3, column=1, padx=5, pady=5)

        # Connect Button
        self.connect_button = ttk.Button(self, text="Connect", command=self.connect_callback)
        self.connect_button.grid(row=4, column=0, columnspan=2, pady=10)


class ControlFrame(ttk.LabelFrame):
    """Frame for controlling STB operations."""
    def __init__(self, parent, command_callback):
        super().__init__(parent, text="STB Control")
        self.command_callback = command_callback
        self._setup_ui()

    def _setup_ui(self):
        """Setup control frame UI elements."""
        # Client IP
        ttk.Label(self, text="Client IP:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.client_ip_entry = ttk.Entry(self, width=30)
        self.client_ip_entry.grid(row=0, column=1, padx=5, pady=5)

        # Command Selection
        ttk.Label(self, text="Command:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.command_var = tk.StringVar()
        self.command_dropdown = ttk.Combobox(
            self,
            textvariable=self.command_var,
            values=list(CONFIG['AVAILABLE_COMMANDS'].keys()),
            state="readonly"
        )
        self.command_dropdown.grid(row=1, column=1, padx=5, pady=5)
        self.command_dropdown.current(0)

        # Execute Button
        self.execute_button = ttk.Button(
            self,
            text="Execute",
            command=lambda: self.command_callback(
                self.client_ip_entry.get().strip(),
                self.command_var.get()
            )
        )
        self.execute_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Output Display
        self.output_text = scrolledtext.ScrolledText(self, width=70, height=20)
        self.output_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Configure grid weights
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def display_output(self, command_outputs, logclient_output):
        """Display command outputs in the text widget."""
        self.output_text.delete(1.0, tk.END)
        
        # Display command outputs
        self.output_text.insert(tk.END, "=== Command Outputs ===\n\n")
        for i, output in enumerate(command_outputs, 1):
            self.output_text.insert(tk.END, f"Command {i} Output:\n{output}\n\n")
        
        # Display logclient output
        self.output_text.insert(tk.END, "=== Logclient Output ===\n\n")
        self.output_text.insert(tk.END, logclient_output)
        
        # Scroll to top
        self.output_text.see("1.0")


if __name__ == "__main__":
    app = SSHApp()
    app.mainloop()
