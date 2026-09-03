"""
PE00 - Expression Evaluation
Graphical user interface.

Responsibilities of this module:
  - Build the UI (editable input area, read-only output area, two buttons)
  - Load external .in files from any directory into the input area
  - Guard the Process action so it only runs on non-empty input
  - Stay running until the user closes the window

Expression parsing and evaluation live in evaluator.py.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

import evaluator


# --------------------------------------------------------------------------
# Appearance constants
# --------------------------------------------------------------------------

BG = "#f4f5f7"
INPUT_BG = "#ffffff"
OUTPUT_BG = "#fbfbfc"
TEXT_COLOR = "#3c4149"


# --------------------------------------------------------------------------
# Window
# --------------------------------------------------------------------------

root = tk.Tk()
root.title("PE00 - Expression Evaluation")
root.geometry("980x560")
root.minsize(700, 400)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background=BG)
style.configure("TLabel", background=BG, foreground=TEXT_COLOR,
                font=("Segoe UI", 10))
style.configure("Action.TButton", font=("Segoe UI Semibold", 10),
                padding=(0, 10))

# The root holds a single padded frame; everything else lives inside it.
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

container = ttk.Frame(root, padding=16)
container.grid(row=0, column=0, sticky="nsew")

# Two equal columns; the middle row absorbs all spare vertical space.
container.columnconfigure(0, weight=1, uniform="col")
container.columnconfigure(1, weight=1, uniform="col")
container.rowconfigure(1, weight=1)


# --------------------------------------------------------------------------
# Widgets
# --------------------------------------------------------------------------

ttk.Label(container, text="Input lines").grid(
    row=0, column=0, sticky="w", padx=(2, 8), pady=(0, 6))

ttk.Label(container, text="Output").grid(
    row=0, column=1, sticky="w", padx=(8, 2), pady=(0, 6))

text_opts = {
    "wrap": "none",
    "font": ("Consolas", 11),
    "relief": "solid",
    "borderwidth": 1,
    "highlightthickness": 0,
    "padx": 10,
    "pady": 8,
}

input_area = scrolledtext.ScrolledText(container, bg=INPUT_BG, **text_opts)
input_area.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

output_area = scrolledtext.ScrolledText(container, bg=OUTPUT_BG, **text_opts)
output_area.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
output_area.config(state="disabled")   # read-only from the very start

load_btn = ttk.Button(container, text="Load File", style="Action.TButton")
load_btn.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=(12, 0))

process_btn = ttk.Button(container, text="Process", style="Action.TButton")
process_btn.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(12, 0))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def get_input_text():
    """Return the input area's contents without the automatic trailing newline."""
    return input_area.get("1.0", "end-1c")


def set_output(text):
    """Replace the output area's contents.

    The widget is kept disabled so the user cannot type into it, so it has to
    be unlocked for the duration of the write and locked again afterwards.
    """
    output_area.config(state="normal")
    output_area.delete("1.0", tk.END)
    output_area.insert("1.0", text)
    output_area.config(state="disabled")


def refresh_process_state(event=None):
    """Enable Process only while the input area holds something meaningful."""
    has_text = bool(get_input_text().strip())
    process_btn.config(state="normal" if has_text else "disabled")


# --------------------------------------------------------------------------
# Button actions
# --------------------------------------------------------------------------

def load_file():
    """Open a .in file from anywhere on the machine and show it in the input area."""
    path = filedialog.askopenfilename(
        title="Open input file",
        filetypes=[("Input files", "*.in"), ("All files", "*.*")],
    )

    if not path:
        return                                  # user cancelled the dialog

    if not path.lower().endswith(".in"):
        messagebox.showerror(
            "Wrong file type",
            "Only .in files can be loaded.\n\nPlease choose a file with a .in extension.",
        )
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        messagebox.showerror("Could not open file", str(e))
        return

    input_area.delete("1.0", tk.END)
    input_area.insert("1.0", content)
    set_output("")
    refresh_process_state()


def process():
    """Hand the input lines to the evaluator and display the result."""
    raw = get_input_text()

    if not raw.strip():
        messagebox.showwarning("Empty input", "There is nothing to process.")
        return

    lines = raw.splitlines()

    try:
        result = evaluator.run(lines)
    except Exception as e:
        # A crash in the evaluator must not take the whole program down.
        messagebox.showerror("Processing error", f"{type(e).__name__}: {e}")
        return

    set_output(result)


# --------------------------------------------------------------------------
# Wiring
# --------------------------------------------------------------------------

load_btn.config(command=load_file)
process_btn.config(command=process)

input_area.bind("<KeyRelease>", refresh_process_state)
input_area.bind("<<Paste>>", lambda e: input_area.after(1, refresh_process_state))
input_area.bind("<<Cut>>", lambda e: input_area.after(1, refresh_process_state))

refresh_process_state()          # correct state before the window appears

root.mainloop()
