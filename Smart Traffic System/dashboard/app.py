# dashboard/app.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tkinter as tk
from tkinter import ttk
from database.db import get_violations

COLUMNS = ("ID", "Vehicle ID", "Timestamp", "Evidence Image", "Plate Number")

def refresh_table(tree):
    for item in tree.get_children():
        tree.delete(item)
    violations = get_violations()
    for v in violations:
        # v = (id, vehicle_id, timestamp, image_path, plate_number)
        plate = v[4] if len(v) > 4 and v[4] else "—"
        tree.insert("", "end", values=(v[0], v[1], v[2], v[3], plate))
    count_var.set(f"Total violations: {len(violations)}")

def run_dashboard():
    global count_var
    root = tk.Tk()
    root.title("Smart Traffic Violation Dashboard")
    root.geometry("1000x500")

    # Header
    header = tk.Label(root, text="🚦 Smart Traffic Violation Dashboard",
                      font=("Helvetica", 16, "bold"), pady=10)
    header.pack()

    count_var = tk.StringVar(value="Total violations: 0")
    tk.Label(root, textvariable=count_var, font=("Helvetica", 11)).pack()

    # Table
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=10, pady=5)

    scrollbar = ttk.Scrollbar(frame, orient="vertical")
    tree = ttk.Treeview(frame, columns=COLUMNS, show="headings",
                        yscrollcommand=scrollbar.set)
    scrollbar.config(command=tree.yview)

    col_widths = [50, 90, 180, 280, 140]
    for col, width in zip(COLUMNS, col_widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")

    # Colour-code rows that have a plate reading
    tree.tag_configure("has_plate",   background="#d4edda")   # green tint
    tree.tag_configure("no_plate",    background="#fff3cd")   # amber tint

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="🔄  Refresh", width=15,
              command=lambda: refresh_table(tree)).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✖  Exit", width=10,
              command=root.destroy).pack(side="left", padx=5)

    refresh_table(tree)
    root.mainloop()


if __name__ == "__main__":
    # Also print to console for quick inspection
    violations = get_violations()
    print("🚨 Smart Traffic Violation Records")
    print("-" * 80)
    for v in violations:
        plate = v[4] if len(v) > 4 and v[4] else "unknown"
        print(f"ID:{v[0]:>4}  Vehicle:{v[1]:>4}  Time:{v[2]}  Plate:{plate:<12}  Img:{v[3]}")
    print(f"\nTotal: {len(violations)} violations")
    print("-" * 80)
    run_dashboard()
