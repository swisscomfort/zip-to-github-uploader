import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

def deploy_zip():
    zip_path = filedialog.askopenfilename(filetypes=[("ZIP-Dateien", "*.zip")])
    if not zip_path:
        return

    try:
        subprocess.run(["bash", "./deploy.sh", zip_path], check=True)
        messagebox.showinfo("Erfolg", "✅ Upload abgeschlossen!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler", f"❌ deploy.sh ist fehlgeschlagen:\n{e}")

root = tk.Tk()
root.title("GitHub Uploader")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

label = tk.Label(frame, text="📦 Wähle dein ZIP-Projekt zur Analyse & GitHub-Upload")
label.pack(pady=(0, 10))

btn = tk.Button(frame, text="🔼 ZIP auswählen und deployen", command=deploy_zip)
btn.pack()

root.mainloop()
