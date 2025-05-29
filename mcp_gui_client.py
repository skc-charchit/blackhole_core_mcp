#!/usr/bin/env python3
"""
MCP GUI Client
Professional desktop application for MCP server interaction
"""

import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server_client import MCPServerClient, create_mcp_client, ConnectionState

class MCPGUIClient:
    """Professional GUI client for MCP server."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.client: Optional[MCPServerClient] = None
        self.connection_status = "Disconnected"
        self.server_url = "http://localhost:8000"
        
        # Setup GUI
        self.setup_gui()
        self.setup_styles()
        
        # Start async loop in separate thread
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()
        
        # Auto-connect on startup
        self.schedule_async(self.connect_to_server())
    
    def setup_gui(self):
        """Setup the GUI layout."""
        self.root.title("MCP Server Client - Professional Interface")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        conn_frame.columnconfigure(1, weight=1)
        
        # Server URL
        ttk.Label(conn_frame, text="Server URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.url_var = tk.StringVar(value=self.server_url)
        self.url_entry = ttk.Entry(conn_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Connection buttons
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.on_connect)
        self.connect_btn.grid(row=0, column=2, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.on_disconnect, state="disabled")
        self.disconnect_btn.grid(row=0, column=3)
        
        # Status
        self.status_var = tk.StringVar(value="Status: Disconnected")
        self.status_label = ttk.Label(conn_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Left panel - Controls
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.grid_propagate(False)
        
        # Command frame
        cmd_frame = ttk.LabelFrame(left_frame, text="Commands", padding="5")
        cmd_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Quick commands
        ttk.Button(cmd_frame, text="Get Server Status", command=lambda: self.send_quick_command("status")).pack(fill=tk.X, pady=2)
        ttk.Button(cmd_frame, text="List Agents", command=lambda: self.send_quick_command("agents")).pack(fill=tk.X, pady=2)
        ttk.Button(cmd_frame, text="Test Connection", command=lambda: self.send_quick_command("hello")).pack(fill=tk.X, pady=2)
        ttk.Button(cmd_frame, text="Gmail Status", command=lambda: self.send_quick_command("get gmail status")).pack(fill=tk.X, pady=2)
        ttk.Button(cmd_frame, text="Reload Agents", command=lambda: self.send_quick_command("reload")).pack(fill=tk.X, pady=2)
        
        # Document analysis frame
        doc_frame = ttk.LabelFrame(left_frame, text="Document Analysis", padding="5")
        doc_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(doc_frame, text="Select File", command=self.select_file).pack(fill=tk.X, pady=2)
        
        self.file_var = tk.StringVar(value="No file selected")
        ttk.Label(doc_frame, textvariable=self.file_var, wraplength=250).pack(fill=tk.X, pady=2)
        
        ttk.Label(doc_frame, text="Query:").pack(anchor=tk.W)
        self.query_entry = ttk.Entry(doc_frame)
        self.query_entry.pack(fill=tk.X, pady=2)
        self.query_entry.insert(0, "who is the author and what is the summary")
        
        ttk.Button(doc_frame, text="Analyze Document", command=self.analyze_document).pack(fill=tk.X, pady=2)
        
        # Performance frame
        perf_frame = ttk.LabelFrame(left_frame, text="Performance", padding="5")
        perf_frame.pack(fill=tk.X)
        
        self.perf_text = tk.Text(perf_frame, height=8, width=30)
        self.perf_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(perf_frame, text="Refresh Stats", command=self.update_performance).pack(fill=tk.X, pady=(5, 0))
        
        # Right panel - Communication
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        
        # Communication frame
        comm_frame = ttk.LabelFrame(right_frame, text="Communication", padding="5")
        comm_frame.pack(fill=tk.BOTH, expand=True)
        comm_frame.rowconfigure(0, weight=1)
        comm_frame.columnconfigure(0, weight=1)
        
        # Response area
        self.response_text = scrolledtext.ScrolledText(comm_frame, wrap=tk.WORD, height=20)
        self.response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Command input frame
        input_frame = ttk.Frame(comm_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        # Command input
        ttk.Label(input_frame, text="Command:").grid(row=0, column=0, sticky=tk.W)
        self.command_entry = ttk.Entry(input_frame, width=50)
        self.command_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.command_entry.bind('<Return>', lambda e: self.send_command())
        
        self.send_btn = ttk.Button(input_frame, text="Send", command=self.send_command)
        self.send_btn.grid(row=1, column=1)
        
        # Clear button
        ttk.Button(input_frame, text="Clear", command=self.clear_response).grid(row=1, column=2, padx=(5, 0))
        
        # Initial message
        self.add_response("🤖 MCP GUI Client Ready\n" + "="*50 + "\n")
        self.add_response("Welcome to the MCP Server GUI Client!\n")
        self.add_response("Connecting to server automatically...\n\n")
    
    def setup_styles(self):
        """Setup custom styles."""
        style = ttk.Style()
        
        # Configure button styles
        style.configure('Success.TButton', foreground='green')
        style.configure('Error.TButton', foreground='red')
    
    def _run_async_loop(self):
        """Run async event loop in separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def schedule_async(self, coro):
        """Schedule async coroutine."""
        asyncio.run_coroutine_threadsafe(coro, self.loop)
    
    def add_response(self, text: str, tag: str = None):
        """Add text to response area."""
        self.response_text.insert(tk.END, text)
        if tag:
            # Add tags for styling if needed
            pass
        self.response_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_response(self):
        """Clear response area."""
        self.response_text.delete(1.0, tk.END)
    
    def update_status(self, status: str, color: str = "black"):
        """Update connection status."""
        self.status_var.set(f"Status: {status}")
        self.connection_status = status
        
        # Update button states
        if status == "Connected":
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.send_btn.config(state="normal")
        else:
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.send_btn.config(state="disabled")
    
    async def connect_to_server(self):
        """Connect to MCP server."""
        try:
            self.server_url = self.url_var.get()
            self.client = create_mcp_client(self.server_url)
            
            self.root.after(0, lambda: self.update_status("Connecting..."))
            self.root.after(0, lambda: self.add_response(f"🔗 Connecting to {self.server_url}...\n"))
            
            if await self.client.connect():
                self.root.after(0, lambda: self.update_status("Connected"))
                self.root.after(0, lambda: self.add_response("✅ Connected successfully!\n\n"))
                
                # Get server info
                try:
                    status = await self.client.get_server_status()
                    if status.status == "success":
                        info = f"Server: {status.data.get('status', 'Unknown')}\n"
                        info += f"Modular System: {status.data.get('modular_system', 'Unknown')}\n\n"
                        self.root.after(0, lambda: self.add_response(info))
                except:
                    pass
                
                # Update performance
                self.root.after(0, self.update_performance)
            else:
                self.root.after(0, lambda: self.update_status("Connection Failed"))
                self.root.after(0, lambda: self.add_response("❌ Connection failed!\n\n"))
        except Exception as e:
            self.root.after(0, lambda: self.update_status("Error"))
            self.root.after(0, lambda: self.add_response(f"❌ Connection error: {e}\n\n"))
    
    async def disconnect_from_server(self):
        """Disconnect from MCP server."""
        if self.client:
            await self.client.disconnect()
            self.client = None
        
        self.root.after(0, lambda: self.update_status("Disconnected"))
        self.root.after(0, lambda: self.add_response("🔌 Disconnected from server\n\n"))
    
    async def send_command_async(self, command: str):
        """Send command to server asynchronously."""
        if not self.client or self.client.connection_state != ConnectionState.CONNECTED:
            self.root.after(0, lambda: self.add_response("❌ Not connected to server\n\n"))
            return
        
        try:
            self.root.after(0, lambda: self.add_response(f"📤 Sending: {command}\n"))
            
            response = await self.client.send_command(command)
            
            result = f"📥 Response:\n"
            result += f"   Status: {response.status}\n"
            
            if response.status == "success":
                data = response.data
                if 'message' in data:
                    result += f"   Message: {data['message']}\n"
                if 'comprehensive_answer' in data:
                    result += f"   Answer: {data['comprehensive_answer']}\n"
                if 'agents_involved' in data:
                    result += f"   Agents: {', '.join(data['agents_involved'])}\n"
                if 'total_agents' in data:
                    result += f"   Total Agents: {data['total_agents']}\n"
            else:
                result += f"   Error: {response.error}\n"
            
            result += f"   Processing Time: {response.processing_time:.3f}s\n\n"
            
            self.root.after(0, lambda: self.add_response(result))
            self.root.after(0, self.update_performance)
            
        except Exception as e:
            self.root.after(0, lambda: self.add_response(f"❌ Error: {e}\n\n"))
    
    async def analyze_document_async(self, file_path: str, query: str):
        """Analyze document asynchronously."""
        if not self.client or self.client.connection_state != ConnectionState.CONNECTED:
            self.root.after(0, lambda: self.add_response("❌ Not connected to server\n\n"))
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.root.after(0, lambda: self.add_response(f"📄 Analyzing: {file_path}\n"))
            self.root.after(0, lambda: self.add_response(f"🔍 Query: {query}\n"))
            
            response = await self.client.analyze_document(file_path, content, query)
            
            result = f"📥 Analysis Result:\n"
            result += f"   Status: {response.status}\n"
            
            if response.status == "success":
                data = response.data
                if 'comprehensive_answer' in data:
                    result += f"   Answer: {data['comprehensive_answer']}\n"
                if 'agents_involved' in data:
                    result += f"   Agents: {', '.join(data['agents_involved'])}\n"
            else:
                result += f"   Error: {response.error}\n"
            
            result += f"   Processing Time: {response.processing_time:.3f}s\n\n"
            
            self.root.after(0, lambda: self.add_response(result))
            self.root.after(0, self.update_performance)
            
        except Exception as e:
            self.root.after(0, lambda: self.add_response(f"❌ Error: {e}\n\n"))
    
    def on_connect(self):
        """Handle connect button click."""
        self.schedule_async(self.connect_to_server())
    
    def on_disconnect(self):
        """Handle disconnect button click."""
        self.schedule_async(self.disconnect_from_server())
    
    def send_command(self):
        """Send command from input field."""
        command = self.command_entry.get().strip()
        if command:
            self.command_entry.delete(0, tk.END)
            self.schedule_async(self.send_command_async(command))
    
    def send_quick_command(self, command: str):
        """Send predefined quick command."""
        self.schedule_async(self.send_command_async(command))
    
    def select_file(self):
        """Select file for analysis."""
        file_path = filedialog.askopenfilename(
            title="Select Document",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.selected_file = file_path
            filename = file_path.split('/')[-1]
            self.file_var.set(f"Selected: {filename}")
    
    def analyze_document(self):
        """Analyze selected document."""
        if not hasattr(self, 'selected_file'):
            messagebox.showwarning("No File", "Please select a file first")
            return
        
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("No Query", "Please enter a query")
            return
        
        self.schedule_async(self.analyze_document_async(self.selected_file, query))
    
    def update_performance(self):
        """Update performance metrics."""
        if not self.client:
            self.perf_text.delete(1.0, tk.END)
            self.perf_text.insert(tk.END, "Not connected")
            return
        
        info = self.client.get_connection_info()
        metrics = info['performance_metrics']
        
        perf_info = f"Connection: {info['state']}\n"
        perf_info += f"Server: {info['server_url']}\n"
        perf_info += f"Active Requests: {info['active_requests']}\n\n"
        
        perf_info += f"Total Requests: {metrics['total_requests']}\n"
        perf_info += f"Successful: {metrics['successful_requests']}\n"
        perf_info += f"Failed: {metrics['failed_requests']}\n"
        
        if metrics['total_requests'] > 0:
            success_rate = (metrics['successful_requests'] / metrics['total_requests']) * 100
            perf_info += f"Success Rate: {success_rate:.1f}%\n"
        
        perf_info += f"Avg Response: {metrics['average_response_time']:.3f}s\n"
        
        self.perf_text.delete(1.0, tk.END)
        self.perf_text.insert(tk.END, perf_info)
    
    def run(self):
        """Run the GUI application."""
        try:
            self.root.mainloop()
        finally:
            # Cleanup
            if self.client:
                self.schedule_async(self.client.disconnect())
            self.loop.call_soon_threadsafe(self.loop.stop)

def main():
    """Main entry point."""
    app = MCPGUIClient()
    app.run()

if __name__ == "__main__":
    main()
