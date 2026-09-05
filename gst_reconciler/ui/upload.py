import tkinter as tk
from tkinter import filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD


class UploadFrame(tk.Frame):
    def __init__(self, parent, on_reconcile):
        super().__init__(parent)
        self.on_reconcile = on_reconcile
        self.tally_path = None
        self.gst_path = None
        self.setup_ui()
    
    def setup_ui(self):
        self.configure(bg="#f0f2f5")
        
        title = tk.Label(
            self,
            text="Upload Files for Reconciliation",
            font=("Segoe UI", 20, "bold"),
            fg="#2F5496",
            bg="#f0f2f5"
        )
        title.pack(pady=(30, 20))
        
        card_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        card_frame.pack(fill="x", padx=60, pady=10)
        
        self.tally_card = self.create_file_card(card_frame, "Tally Voucher Register (.xlsx)", 
                                                 "Select the Tally export file (CGST Input sheet)", 
                                                 self.on_tally_select)
        self.tally_card.pack(fill="x", padx=20, pady=15)
        
        self.gst_card = self.create_file_card(card_frame, "GSTR-2B from GST Portal (.xlsx)", 
                                               "Select the GSTR-2B downloaded from GST portal (B2B sheet)", 
                                               self.on_gst_select)
        self.gst_card.pack(fill="x", padx=20, pady=15)
        
        self.reconcile_btn = tk.Button(
            self,
            text="Start Reconciliation",
            command=self.start_reconciliation,
            font=("Segoe UI", 12, "bold"),
            bg="#2F5496",
            fg="white",
            bd=0,
            padx=40,
            pady=14,
            cursor="hand2",
            state="disabled",
            activebackground="#1e3d6f"
        )
        self.reconcile_btn.pack(pady=30)
        
        self.progress_frame = tk.Frame(self, bg="#f0f2f5")
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="indeterminate",
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 10),
            fg="#666",
            bg="#f0f2f5"
        )
        self.progress_label.pack()
    
    def create_file_card(self, parent, title, subtitle, callback):
        card = tk.Frame(parent, bg="#f8f9fa", bd=1, relief="solid")
        
        left = tk.Frame(card, bg="#f8f9fa")
        left.pack(side="left", fill="x", expand=True, padx=20, pady=15)
        
        tk.Label(left, text=title, font=("Segoe UI", 11, "bold"), fg="#333", bg="#f8f9fa").pack(anchor="w")
        tk.Label(left, text=subtitle, font=("Segoe UI", 9), fg="#666", bg="#f8f9fa").pack(anchor="w", pady=(2, 0))
        
        self.file_label = tk.Label(left, text="No file selected", font=("Segoe UI", 9), fg="#999", bg="#f8f9fa")
        self.file_label.pack(anchor="w", pady=(5, 0))
        
        right = tk.Frame(card, bg="#f8f9fa")
        right.pack(side="right", padx=20, pady=15)
        
        btn = tk.Button(
            right,
            text="Browse",
            command=callback,
            font=("Segoe UI", 10),
            bg="#2F5496",
            fg="white",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        btn.pack()
        
        card.file_label = self.file_label
        card.btn = btn
        card.callback = callback
        
        card.drop_target_register(DND_FILES)
        card.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, card))
        
        return card
    
    def on_drop(self, event, card):
        filepath = event.data.strip('{}')
        if filepath.lower().endswith(('.xlsx', '.xls')):
            if card == self.tally_card:
                self.set_tally(filepath)
            else:
                self.set_gst(filepath)
    
    def on_tally_select(self):
        filepath = filedialog.askopenfilename(
            title="Select Tally Voucher Register",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if filepath:
            self.set_tally(filepath)
    
    def on_gst_select(self):
        filepath = filedialog.askopenfilename(
            title="Select GSTR-2B File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if filepath:
            self.set_gst(filepath)
    
    def set_tally(self, filepath):
        self.tally_path = filepath
        self.tally_card.file_label.config(text=filepath.split("/")[-1], fg="#2F5496")
        self.check_ready()
    
    def set_gst(self, filepath):
        self.gst_path = filepath
        self.gst_card.file_label.config(text=filepath.split("/")[-1], fg="#2F5496")
        self.check_ready()
    
    def check_ready(self):
        if self.tally_path and self.gst_path:
            self.reconcile_btn.config(state="normal")
        else:
            self.reconcile_btn.config(state="disabled")
    
    def start_reconciliation(self):
        self.reconcile_btn.config(state="disabled")
        self.tally_card.btn.config(state="disabled")
        self.gst_card.btn.config(state="disabled")
        self.progress_frame.pack(pady=20)
        self.progress_bar.start(10)
        self.progress_label.config(text="Processing files...")
        self.on_reconcile(self.tally_path, self.gst_path)
    
    def show_progress(self, message):
        self.progress_label.config(text=message)
    
    def hide_progress(self):
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.reconcile_btn.config(state="normal")
        self.tally_card.btn.config(state="normal")
        self.gst_card.btn.config(state="normal")
    
    def reset(self):
        self.tally_path = None
        self.gst_path = None
        self.tally_card.file_label.config(text="No file selected", fg="#999")
        self.gst_card.file_label.config(text="No file selected", fg="#999")
        self.check_ready()