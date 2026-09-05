import os
import tkinter as tk
from tkinter import messagebox


PASSWORD = os.environ.get("GST_RECONCILER_PASSWORD", "")


class PasswordNotSetError(Exception):
    pass


def _get_password() -> str:
    pw = os.environ.get("GST_RECONCILER_PASSWORD", "")
    if not pw:
        raise PasswordNotSetError(
            "GST_RECONCILER_PASSWORD environment variable is not set.\n\n"
            "To fix, create a .env file in the project root with:\n"
            "  GST_RECONCILER_PASSWORD=your_password_here\n\n"
            "Or export it before running:\n"
            "  export GST_RECONCILER_PASSWORD=your_password_here  # Linux/macOS\n"
            "  set GST_RECONCILER_PASSWORD=your_password_here     # Windows"
        )
    return pw


class LoginFrame(tk.Frame):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        self.setup_ui()
    
    def setup_ui(self):
        self.configure(bg="#f0f2f5")
        
        container = tk.Frame(self, bg="white", bd=0)
        container.place(relx=0.5, rely=0.5, anchor="center", width=400, height=300)
        
        tk.Label(
            container,
            text="GST Reconciler",
            font=("Segoe UI", 24, "bold"),
            fg="#2F5496",
            bg="white"
        ).pack(pady=(40, 10))
        
        tk.Label(
            container,
            text="Enter password to continue",
            font=("Segoe UI", 11),
            fg="#666",
            bg="white"
        ).pack(pady=(0, 30))
        
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            container,
            textvariable=self.password_var,
            show="*",
            font=("Segoe UI", 12),
            width=25,
            bd=1,
            relief="solid",
            justify="center"
        )
        self.password_entry.pack(pady=10, ipady=8)
        self.password_entry.bind("<Return>", lambda e: self.check_password())
        self.password_entry.focus()
        
        tk.Button(
            container,
            text="Login",
            command=self.check_password,
            font=("Segoe UI", 11, "bold"),
            bg="#2F5496",
            fg="white",
            bd=0,
            padx=40,
            pady=10,
            cursor="hand2",
            activebackground="#1e3d6f"
        ).pack(pady=20)
        
        self.error_label = tk.Label(
            container,
            text="",
            font=("Segoe UI", 9),
            fg="#C00000",
            bg="white"
        )
        self.error_label.pack()
    
    def check_password(self):
        try:
            required = _get_password()
        except PasswordNotSetError as e:
            messagebox.showerror("Password Not Configured", str(e))
            return

        if self.password_var.get() == required:
            self.on_success()
        else:
            self.error_label.config(text="Incorrect password")
            self.password_var.set("")
            self.password_entry.focus()