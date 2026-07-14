import tkinter as tk
from tkinter import ttk
from ui.warehouse_tab import WarehouseTab
from ui.issue_tab import IssueTab
from ui.reports_tab import ReportsTab

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("TrackMate — учёт материалов")
        self.root.geometry("950x780")
        self.root.resizable(True, True)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладки
        self.warehouse_tab = WarehouseTab(self.notebook)
        self.issue_tab = IssueTab(self.notebook)
        self.reports_tab = ReportsTab(self.notebook)
        
        # Статус-бар
        self.status = ttk.Label(root, text="✅ Готов к работе", relief='sunken')
        self.status.pack(fill='x', padx=10, pady=5)