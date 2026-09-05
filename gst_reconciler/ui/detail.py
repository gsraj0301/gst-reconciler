import tkinter as tk
from tkinter import ttk
from ..matcher import MatchResult


class DetailFrame(tk.Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent)
        self.on_back = on_back
        self.all_results = []
        self.current_filter = ""
        self.setup_ui()
    
    def setup_ui(self):
        self.configure(bg="#f0f2f5")
        
        header = tk.Frame(self, bg="#f0f2f5")
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        tk.Button(
            header,
            text="← Back to Summary",
            command=self.on_back,
            font=("Segoe UI", 10),
            bg="#6c757d",
            fg="white",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side="left")
        
        self.title_label = tk.Label(
            header,
            text="",
            font=("Segoe UI", 16, "bold"),
            fg="#2F5496",
            bg="#f0f2f5"
        )
        self.title_label.pack(side="left", padx=20)
        
        self.count_label = tk.Label(
            header,
            text="",
            font=("Segoe UI", 11),
            fg="#666",
            bg="#f0f2f5"
        )
        self.count_label.pack(side="left", padx=10)
        
        table_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = (
            "GSTIN", "Party Name", "Invoice No", "Invoice Date",
            "Tally Value", "GSTR-2B Value", "Value Diff",
            "Tally Taxable", "GSTR-2B Taxable", "Tax Diff",
            "Tally IGST", "GSTR-2B IGST", "IGST Diff",
            "Tally CGST", "GSTR-2B CGST", "CGST Diff",
            "Tally SGST", "GSTR-2B SGST", "SGST Diff"
        )
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            width = 120 if "Value" in col or "Tax" in col or "IGST" in col or "CGST" in col or "SGST" in col else 160
            if col in ("Party Name", "GSTIN"):
                width = 200
            elif col == "Invoice No":
                width = 150
            self.tree.column(col, width=width, anchor="center")
        
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        
        self.tree.tag_configure("mismatch", background="#FFC7CE")
        self.tree.tag_configure("tally_only", background="#FFEB9C")
        self.tree.tag_configure("gst_only", background="#BDD7EE")
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def set_data(self, results: list[MatchResult], filter_status: str):
        self.all_results = results
        self.current_filter = filter_status
        self.tree.delete(*self.tree.get_children())
        
        self.title_label.config(text=filter_status)
        
        filtered = [r for r in results if filter_status in r.status]
        self.count_label.config(text=f"{len(filtered)} entries")
        
        for result in filtered:
            t = result.tally_row
            g = result.gst_row
            
            gstin = t.gstin if t else (g.gstin if g else "")
            party = t.particulars if t else (g.trade_name if g else "")
            inv_no = t.voucher_ref_no if t else (g.invoice_no if g else "")
            inv_date = t.voucher_ref_date if t else (g.invoice_date if g else None)
            
            tally_inv_val = t.gross_total if t else 0.0
            gst_inv_val = g.invoice_value if g else 0.0
            tally_tax_val = t.taxable_value if t else 0.0
            gst_tax_val = g.taxable_value if g else 0.0
            tally_igst = t.igst if t else 0.0
            gst_igst = g.igst if g else 0.0
            tally_cgst = t.cgst if t else 0.0
            gst_cgst = g.cgst if g else 0.0
            tally_sgst = t.sgst if t else 0.0
            gst_sgst = g.sgst if g else 0.0
            
            tag = ""
            if "In Tally but not in GSTR-2B" in result.status:
                tag = "tally_only"
            elif "In GSTR-2B but not in Tally" in result.status:
                tag = "gst_only"
            else:
                tag = "mismatch"
            
            values = [
                gstin,
                party,
                inv_no,
                inv_date.strftime("%d/%m/%Y") if inv_date and not hasattr(inv_date, 'isna') else str(inv_date)[:10] if inv_date else "",
                f"{tally_inv_val:,.2f}",
                f"{gst_inv_val:,.2f}",
                f"{result.invoice_value_diff:,.2f}",
                f"{tally_tax_val:,.2f}",
                f"{gst_tax_val:,.2f}",
                f"{result.taxable_value_diff:,.2f}",
                f"{tally_igst:,.2f}",
                f"{gst_igst:,.2f}",
                f"{result.igst_diff:,.2f}",
                f"{tally_cgst:,.2f}",
                f"{gst_cgst:,.2f}",
                f"{result.cgst_diff:,.2f}",
                f"{tally_sgst:,.2f}",
                f"{gst_sgst:,.2f}",
                f"{result.sgst_diff:,.2f}"
            ]
            
            self.tree.insert("", "end", values=values, tags=(tag,))