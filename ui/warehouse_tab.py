import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from core import database as db
from widgets.autocomplete import AutocompleteCombobox

class WarehouseTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="📦 Склад")
        self.setup_ui()
    
    def setup_ui(self):
        frame = self.frame
        frame.grid_rowconfigure(6, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        # Модель
        ttk.Label(frame, text="Модель:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.wh_model = AutocompleteCombobox(frame, values=db.get_models(), width=30)
        self.wh_model.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_model).grid(row=0, column=2, padx=2, pady=5)
        
        # Количество
        ttk.Label(frame, text="Количество:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.wh_qty = ttk.Entry(frame, width=10)
        self.wh_qty.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Примечание
        ttk.Label(frame, text="Примечание:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.wh_notes = ttk.Entry(frame, width=40)
        self.wh_notes.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        
        # Приход
        ttk.Button(frame, text="📥 Приход", command=self.on_receive).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Инвентаризация
        self.setup_inventory(frame)
        
        # Добавление модели с остатком
        self.setup_add_model_with_stock(frame)
        
        # Таблица остатков
        self.setup_stock_table(frame)
        
        self.refresh_stock()
    
    def setup_inventory(self, frame):
        inv_frame = ttk.LabelFrame(frame, text="🔧 Инвентаризация", padding=5)
        inv_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky='ew')
        inv_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(inv_frame, text="Модель:").grid(row=0, column=0, padx=5, pady=2, sticky='e')
        self.inv_model = AutocompleteCombobox(inv_frame, values=db.get_models(), width=25)
        self.inv_model.grid(row=0, column=1, padx=5, pady=2, sticky='ew')
        self.inv_model.bind('<<ComboboxSelected>>', self.on_inv_model_select)
        ttk.Button(inv_frame, text="➕", width=3, command=self.on_quick_add_model).grid(row=0, column=2, padx=2, pady=2)
        
        ttk.Label(inv_frame, text="Текущий остаток:").grid(row=1, column=0, padx=5, pady=2, sticky='e')
        self.inv_current_stock = ttk.Label(inv_frame, text="0", font=('Arial', 10, 'bold'))
        self.inv_current_stock.grid(row=1, column=1, padx=5, pady=2, sticky='w')
        
        ttk.Label(inv_frame, text="Фактический остаток:").grid(row=2, column=0, padx=5, pady=2, sticky='e')
        self.inv_new_stock = ttk.Entry(inv_frame, width=10)
        self.inv_new_stock.grid(row=2, column=1, padx=5, pady=2, sticky='w')
        
        ttk.Button(inv_frame, text="✅ Применить", command=self.on_inventory_correction).grid(row=3, column=0, columnspan=3, pady=5)
    
    def setup_add_model_with_stock(self, frame):
        add_frame = ttk.LabelFrame(frame, text="➕ Добавить модель с остатком", padding=5)
        add_frame.grid(row=5, column=0, columnspan=3, pady=5, sticky='ew')
        add_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(add_frame, text="Модель:").grid(row=0, column=0, padx=5, pady=2, sticky='e')
        self.new_model_entry = ttk.Entry(add_frame, width=30)
        self.new_model_entry.grid(row=0, column=1, padx=5, pady=2, sticky='ew')
        
        ttk.Label(add_frame, text="Количество:").grid(row=1, column=0, padx=5, pady=2, sticky='e')
        self.new_model_qty = ttk.Entry(add_frame, width=10)
        self.new_model_qty.grid(row=1, column=1, padx=5, pady=2, sticky='w')
        self.new_model_qty.insert(0, "0")
        
        ttk.Button(add_frame, text="➕ Добавить модель", command=self.on_add_model_with_stock).grid(row=2, column=0, columnspan=3, pady=5)
    
    def setup_stock_table(self, frame):
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.stock_tree = ttk.Treeview(tree_frame, columns=('model', 'in', 'out', 'stock'), show='headings', height=7)
        self.stock_tree.heading('model', text='Модель')
        self.stock_tree.heading('in', text='Приход')
        self.stock_tree.heading('out', text='Выдано')
        self.stock_tree.heading('stock', text='Остаток')
        self.stock_tree.column('model', width=200)
        self.stock_tree.column('in', width=80)
        self.stock_tree.column('out', width=80)
        self.stock_tree.column('stock', width=80)
        self.stock_tree.grid(row=0, column=0, sticky='nsew')
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient='vertical', command=self.stock_tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.stock_tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        self.stock_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.stock_tree.bind('<Double-1>', self.on_stock_double_click)
    
    # ---------- ОБРАБОТЧИКИ ----------
    
    def refresh_stock(self):
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        for row in db.get_stock():
            self.stock_tree.insert('', 'end', values=row)
        models = db.get_models()
        self.wh_model['values'] = models
        self.inv_model['values'] = models
    
    def on_receive(self):
        model = self.wh_model.get()
        try:
            qty = int(self.wh_qty.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество!")
            return
        if not model or qty <= 0:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        db.add_incoming(model, qty, self.wh_notes.get())
        messagebox.showinfo("Успех", f"Приход: {model} x{qty}")
        self.wh_qty.delete(0, 'end')
        self.wh_notes.delete(0, 'end')
        self.refresh_stock()
    
    def on_quick_add_model(self):
        from tkinter import simpledialog
        name = simpledialog.askstring("Новая модель", "Введите название модели:")
        if name and name.strip():
            success, msg = db.add_model(name.strip())
            if success:
                messagebox.showinfo("Успех", f"Модель '{name}' добавлена")
                self.refresh_stock()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def on_add_model_with_stock(self):
        name = self.new_model_entry.get().strip()
        try:
            qty = int(self.new_model_qty.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество!")
            return
        if not name:
            messagebox.showerror("Ошибка", "Введите название модели!")
            return
        success, msg = db.add_model(name)
        if not success:
            messagebox.showerror("Ошибка", msg)
            return
        if qty > 0:
            db.add_incoming(name, qty, "Начальный остаток")
        messagebox.showinfo("Успех", f"Модель '{name}' добавлена с остатком {qty} шт.")
        self.new_model_entry.delete(0, 'end')
        self.new_model_qty.delete(0, 'end')
        self.new_model_qty.insert(0, "0")
        self.refresh_stock()
    
    def on_inv_model_select(self, event):
        model = self.inv_model.get()
        if model:
            stock = db.get_stock(model)
            self.inv_current_stock.config(text=str(stock[0][3] if stock else 0))
    
    def on_inventory_correction(self):
        from tkinter import messagebox
        model = self.inv_model.get()
        try:
            new_stock = int(self.inv_new_stock.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество!")
            return
        if not model:
            messagebox.showerror("Ошибка", "Выберите модель!")
            return
        stock = db.get_stock(model)
        current_stock = stock[0][3] if stock else 0
        diff = new_stock - current_stock
        if diff == 0:
            messagebox.showinfo("Информация", "Остаток не изменился.")
            return
        if diff > 0:
            msg = f"Остаток увеличится на {diff} шт."
        else:
            msg = f"Остаток уменьшится на {abs(diff)} шт."
        if not messagebox.askyesno("Подтверждение", f"{msg}\n\nПродолжить?"):
            return
        if diff > 0:
            db.add_incoming(model, diff, f"Инвентаризация: +{diff} шт. (было {current_stock}, стало {new_stock})")
        else:
            departments = db.get_departments()
            employees = db.get_employees(departments[0] if departments else None)
            if not departments or not employees:
                messagebox.showerror("Ошибка", "Нет отделов или сотрудников!")
                return
            db.add_issue(model, departments[0], employees[0], abs(diff), 
                        datetime.now().strftime("%Y-%m-%d"),
                        f"Инвентаризация: -{abs(diff)} шт. (было {current_stock}, стало {new_stock})")
        messagebox.showinfo("Успех", f"Корректировка выполнена!\nОстаток: {current_stock} → {new_stock}")
        self.inv_new_stock.delete(0, 'end')
        self.inv_current_stock.config(text="0")
        self.refresh_stock()
    
    def on_stock_double_click(self, event):
        selected = self.stock_tree.selection()
        if not selected:
            return
        values = self.stock_tree.item(selected[0], 'values')
        old_name = values[0]
        self.edit_model_dialog(old_name)
    
    def edit_model_dialog(self, old_name):
        dialog = tk.Toplevel()
        dialog.title("Редактировать модель")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.grab_set()
        ttk.Label(dialog, text="Текущее название:").pack(pady=5)
        ttk.Label(dialog, text=old_name, font=('Arial', 10, 'bold')).pack()
        ttk.Label(dialog, text="Новое название:").pack(pady=5)
        new_name_entry = ttk.Entry(dialog, width=30)
        new_name_entry.pack()
        new_name_entry.focus()
        
        def save():
            new_name = new_name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Ошибка", "Введите название!")
                return
            success, msg = db.rename_model(old_name, new_name)
            if success:
                messagebox.showinfo("Успех", f"Модель переименована: {old_name} → {new_name}")
                dialog.destroy()
                self.refresh_stock()
            else:
                messagebox.showerror("Ошибка", msg)
        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=10)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack()