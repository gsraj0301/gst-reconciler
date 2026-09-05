import tkinter as tk
from tkinter import messagebox, filedialog
from tkinterdnd2 import TkinterDnD
import threading
import os
import sys

from .parser import parse_tally_file, parse_gstr2b_file
from .matcher import match_rows, get_summary
from .writer import write_reconciliation_report
from .ui.login import LoginFrame
from .ui.upload import UploadFrame
from .ui.results import ResultsFrame
from .ui.detail import DetailFrame


class GSTReconcilerApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("GST Reconciler")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg="#f0f2f5")
        
        self.results = []
        self.summary = {}
        self.output_filepath = None
        
        self.show_login()
    
    def show_login(self):
        self.clear_window()
        self.login_frame = LoginFrame(self, self.on_login_success)
        self.login_frame.pack(fill="both", expand=True)
    
    def on_login_success(self):
        self.show_upload()
    
    def show_upload(self):
        self.clear_window()
        self.upload_frame = UploadFrame(self, self.start_reconciliation_thread)
        self.upload_frame.pack(fill="both", expand=True)
    
    def show_results(self):
        self.clear_window()
        self.results_frame = ResultsFrame(
            self,
            self.show_detail,
            self.download_report,
            self.show_upload
        )
        self.results_frame.pack(fill="both", expand=True)
        self.results_frame.set_data(self.results, self.summary)
    
    def show_detail(self, filter_status: str):
        self.clear_window()
        self.detail_frame = DetailFrame(self, self.show_results)
        self.detail_frame.pack(fill="both", expand=True)
        self.detail_frame.set_data(self.results, filter_status)
    
    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
    
    def start_reconciliation_thread(self, tally_path: str, gst_path: str):
        thread = threading.Thread(target=self.run_reconciliation, args=(tally_path, gst_path), daemon=True)
        thread.start()
    
    def run_reconciliation(self, tally_path: str, gst_path: str):
        try:
            self.after(0, lambda: self.upload_frame.show_progress("Reading Tally file..."))
            tally_rows = parse_tally_file(tally_path)
            
            self.after(0, lambda: self.upload_frame.show_progress("Reading GSTR-2B file..."))
            gst_rows = parse_gstr2b_file(gst_path)
            
            self.after(0, lambda: self.upload_frame.show_progress(f"Matching {len(tally_rows)} Tally entries with {len(gst_rows)} GSTR-2B entries..."))
            self.results = match_rows(tally_rows, gst_rows)
            
            self.after(0, lambda: self.upload_frame.show_progress("Generating summary..."))
            self.summary = get_summary(self.results)
            
            self.after(0, lambda: self.upload_frame.show_progress("Writing report to GSTR-2B file..."))
            base, ext = os.path.splitext(gst_path)
            self.output_filepath = f"{base}-reconciled{ext}"
            write_reconciliation_report(gst_path, self.output_filepath, self.results, self.summary)
            
            self.after(0, self.on_reconciliation_complete)
            
        except Exception as e:
            self.after(0, lambda: self.on_reconciliation_error(str(e)))
    
    def on_reconciliation_complete(self):
        self.upload_frame.hide_progress()
        self.show_results()
        messagebox.showinfo(
            "Success",
            f"Reconciliation complete!\n\n"
            f"Matched: {self.summary.get('Matched', 0)}\n"
            f"In Tally only: {self.summary.get('In Tally but not in GSTR-2B', 0)}\n"
            f"In GSTR-2B only: {self.summary.get('In GSTR-2B but not in Tally', 0)}\n"
            f"Value mismatches: {self.summary.get('Invoice Value Mismatch', 0)}\n"
            f"Tax mismatches: {self.summary.get('Taxable Value Mismatch', 0)}\n"
            f"IGST mismatches: {self.summary.get('Integrated Tax Mismatch', 0)}\n"
            f"CGST mismatches: {self.summary.get('Central Tax Mismatch', 0)}\n"
            f"SGST mismatches: {self.summary.get('State/UT Tax Mismatch', 0)}"
        )
    
    def on_reconciliation_error(self, error: str):
        self.upload_frame.hide_progress()
        messagebox.showerror("Error", f"Reconciliation failed:\n{error}")
    
    def download_report(self):
        if not self.output_filepath or not os.path.exists(self.output_filepath):
            messagebox.showerror("Error", "Report file not found")
            return
        
        save_path = filedialog.asksaveasfilename(
            title="Save Reconciliation Report",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=os.path.basename(self.output_filepath)
        )
        
        if save_path:
            try:
                import shutil
                shutil.copy2(self.output_filepath, save_path)
                messagebox.showinfo("Success", f"Report saved to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")


def main():
    app = GSTReconcilerApp()
    app.mainloop()


if __name__ == "__main__":
    main()