import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ..matcher import get_summary


class ResultsFrame(tk.Frame):
    def __init__(self, parent, on_detail, on_download, on_back):
        super().__init__(parent)
        self.on_detail = on_detail
        self.on_download = on_download
        self.on_back = on_back
        self.results = []
        self.summary = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.configure(bg="#f0f2f5")
        
        header = tk.Frame(self, bg="#f0f2f5")
        header.pack(fill="x", padx=30, pady=(20, 10))
        
        tk.Label(
            header,
            text="Reconciliation Results",
            font=("Segoe UI", 20, "bold"),
            fg="#2F5496",
            bg="#f0f2f5"
        ).pack(side="left")
        
        btn_frame = tk.Frame(header, bg="#f0f2f5")
        btn_frame.pack(side="right")
        
        tk.Button(
            btn_frame,
            text="← New Reconciliation",
            command=self.on_back,
            font=("Segoe UI", 10),
            bg="#6c757d",
            fg="white",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side="left", padx=5)
        
        self.download_btn = tk.Button(
            btn_frame,
            text="Download Report",
            command=self.on_download,
            font=("Segoe UI", 10, "bold"),
            bg="#28a745",
            fg="white",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            state="disabled"
        )
        self.download_btn.pack(side="left", padx=5)
        
        self.summary_frame = tk.Frame(self, bg="#f0f2f5")
        self.summary_frame.pack(fill="x", padx=30, pady=10)
        
        table_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        columns = ("Status", "Count")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("Status", text="Status")
        self.tree.heading("Count", text="Count")
        self.tree.column("Status", width=400, anchor="w")
        self.tree.column("Count", width=100, anchor="center")
        
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        
        self.tree.tag_configure("matched", background="#C6EFCE")
        self.tree.tag_configure("tally_only", background="#FFEB9C")
        self.tree.tag_configure("gst_only", background="#BDD7EE")
        self.tree.tag_configure("mismatch", background="#FFC7CE")
        self.tree.tag_configure("duplicate", background="#F4B084")
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Return>", self.on_double_click)
    
    def set_data(self, results: list, summary: dict):
        self.results = results
        self.summary = summary
        self.tree.delete(*self.tree.get_children())
        
        status_order = [
            "Matched",
            "In Tally but not in GSTR-2B",
            "In GSTR-2B but not in Tally",
            "Invoice Value Mismatch",
            "Taxable Value Mismatch",
            "Integrated Tax Mismatch",
            "Central Tax Mismatch",
            "State/UT Tax Mismatch",
            "Duplicate in Tally",
            "Duplicate in GSTR-2B"
        ]
        
        for status in status_order:
            count = summary.get(status, 0)
            if count > 0:
                tag = self.get_tag(status)
                self.tree.insert("", "end", values=(status, count), tags=(tag,))
        
        self.download_btn.config(state="normal")
    
    def get_tag(self, status: str) -> str:
        if status == "Matched":
            return "matched"
        elif "In Tally but not in GSTR-2B" in status:
            return "tally_only"
        elif "In GSTR-2B but not in Tally" in status:
            return "gst_only"
        elif "Duplicate" in status:
            return "duplicate"
        else:
            return "mismatch"
    
    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        status = item["values"][0]
        count = item["values"][1]
        if count > 0 and status != "Matched":
            self.on_detail(status)