# dashboard/app.py
import tkinter as tk
from tkinter import ttk
from database.db import get_violations

def refresh_table(tree):
    for item in tree.get_children():
        tree.delete(item)
    violations = get_violations()
    for v in violations:
        tree.insert("", "end", values=v)

def run_dashboard():
    root = tk.Tk()
    root.title("Smart Traffic Violation Dashboard")
    
    tree = ttk.Treeview(root, columns=("ID", "VehicleID", "Time", "Image"), show="headings")
    tree.heading("ID", text="DB ID")
    tree.heading("VehicleID", text="Vehicle ID")
    tree.heading("Time", text="Timestamp")
    tree.heading("Image", text="Evidence Path")
    tree.pack(fill="both", expand=True)
    
    btn = tk.Button(root, text="Refresh", command=lambda: refresh_table(tree))
    btn.pack()
    
    refresh_table(tree)
    root.mainloop()

if __name__ == "__main__":
    # Print violations to console for visibility
    violations = get_violations()
    print("🚨 Smart Traffic Violation Records:")
    print("-" * 60)
    for v in violations:
        print(f"ID: {v[0]} | Vehicle: {v[1]} | Time: {v[2]} | Image: {v[3]}")
    print(f"\nTotal violations: {len(violations)}")
    
    # Then run GUI
    run_dashboard()