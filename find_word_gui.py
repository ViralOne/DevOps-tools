# Requirement: pip install tk

import tkinter as tk
from tkinter import filedialog
import subprocess

def browse_directory():
    directory = filedialog.askdirectory()
    directory_entry.delete(0, tk.END)
    directory_entry.insert(0, directory)

def run_script():
    directory = directory_entry.get()
    word = word_entry.get()
    extensions = extensions_entry.get().split()
    recursive = recursive_var.get()
    context = context_var.get()
    save_to_file = save_to_file_var.get()
    output_file = output_file_entry.get()

    command = ["python3", "find_word.py", "-d", directory, "-w", word, "-e"] + extensions
    if recursive:
        command.append("-r")
    if context:
        command.append("-c")
    if save_to_file and output_file:
        command.extend(["-o", output_file])

    subprocess.run(command)

# Create the main window
root = tk.Tk()
root.title("Find Word Script")

# Create and place GUI elements
tk.Label(root, text="Directory:").grid(row=0, column=0, sticky="w")
directory_entry = tk.Entry(root, width=50)
directory_entry.grid(row=0, column=1)
tk.Button(root, text="Browse", command=browse_directory).grid(row=0, column=2)

tk.Label(root, text="Word or pattern:").grid(row=1, column=0, sticky="w")
word_entry = tk.Entry(root, width=50)
word_entry.grid(row=1, column=1)

tk.Label(root, text="Extensions (space-separated):").grid(row=2, column=0, sticky="w")
extensions_entry = tk.Entry(root, width=50)
extensions_entry.insert(0, ".html .txt")
extensions_entry.grid(row=2, column=1)

recursive_var = tk.BooleanVar()
tk.Checkbutton(root, text="Recursive search", variable=recursive_var).grid(row=3, column=0, sticky="w")

context_var = tk.BooleanVar()
tk.Checkbutton(root, text="Display context", variable=context_var).grid(row=4, column=0, sticky="w")

save_to_file_var = tk.BooleanVar()
save_to_file_checkbox = tk.Checkbutton(root, text="Save to file", variable=save_to_file_var)
save_to_file_checkbox.grid(row=5, column=0, sticky="w")

output_file_entry = tk.Entry(root, width=50)
output_file_entry.grid(row=5, column=1)

tk.Button(root, text="Run Script", command=run_script).grid(row=6, column=0, columnspan=3)

# Start the Tkinter event loop
root.mainloop()
