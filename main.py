import tkinter as tk
from ui.main_window import MainWindow
from core.database import init_db

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()