import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
from datetime import datetime
import sqlite3

import database as db
import utils

# ---------- КЛАСС ДЛЯ АВТОДОПОЛНЕНИЯ ----------
class AutocompleteCombobox(ttk.Combobox):
    """Combobox с автодополнением — работает без зависаний"""
    def __init__(self, master, values=None, **kwargs):
        super().__init__(master, **kwargs)
        self._values = values or []
        self.set('')
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusIn>', self._on_focus)
    
    def _on_focus(self, event):
        """При фокусе показываем список, но не перехватываем ввод"""
        self['values'] = self._values
    
    def _on_keyrelease(self, event):
        """Фильтруем список при вводе, но не мешаем печатать"""
        # Игнорируем служебные клавиши
        if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Shift_L', 'Shift_R', 
                            'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Caps_Lock',
                            'Left', 'Right', 'Home', 'End', 'BackSpace', 'Delete'):
            return
        
        # Получаем текущий введённый текст
        typed = self.get().lower()
        
        # Если текст пустой — показываем весь список
        if typed == '':
            self['values'] = self._values
            return
        
        # Фильтруем значения (оставляем только те, что содержат введённый текст)
        filtered = [item for item in self._values if typed in item.lower()]
        self['values'] = filtered
        
        # Показываем список вниз, но не перехватываем курсор
        if filtered:
            self.event_generate('<Down>')

# ---------- ГЛАВНОЕ ПРИЛОЖЕНИЕ ----------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет картриджей v3.5")
        self.root.geometry("950x780")
        self.root.resizable(True, True)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tab_warehouse = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_warehouse, text="📦 Склад")
        self.setup_warehouse_tab()
        
        self.tab_issue = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_issue, text="📤 Выдача")
        self.setup_issue_tab()
        
        self.tab_reports = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reports, text="📊 Отчеты")
        self.setup_reports_tab()
        
        self.status = ttk.Label(root, text="✅ Готов к работе", relief='sunken')
        self.status.pack(fill='x', padx=10, pady=5)
    
    def setup_warehouse_tab(self):
        frame = self.tab_warehouse
        frame.grid_rowconfigure(6, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(frame, text="Модель:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.wh_model = AutocompleteCombobox(frame, values=db.get_models(), width=30)
        self.wh_model.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_model).grid(row=0, column=2, padx=2, pady=5)
        
        ttk.Label(frame, text="Количество:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.wh_qty = ttk.Entry(frame, width=10)
        self.wh_qty.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(frame, text="Примечание:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.wh_notes = ttk.Entry(frame, width=40)
        self.wh_notes.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        
        ttk.Button(frame, text="📥 Приход", command=self.on_receive).grid(row=3, column=0, columnspan=2, pady=5)
        
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
        
        # ---- ТАБЛИЦА ОСТАТКОВ С ПРОКРУТКОЙ ----
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
        
        self.refresh_stock()
    
    def setup_issue_tab(self):
        frame = self.tab_issue
        frame.grid_rowconfigure(8, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        # ----- ОТДЕЛ -----
        ttk.Label(frame, text="Отдел:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.issue_dept = AutocompleteCombobox(frame, values=db.get_departments(), width=25)
        self.issue_dept.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.issue_dept.bind('<<ComboboxSelected>>', self.update_employees)
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_department).grid(row=0, column=2, padx=2, pady=5)
        ttk.Button(frame, text="✏️", width=3, command=self.edit_department_dialog).grid(row=0, column=3, padx=1, pady=5)
        ttk.Button(frame, text="🗑️", width=3, command=self.delete_department_dialog).grid(row=0, column=4, padx=1, pady=5)
        
        # ----- СОТРУДНИК -----
        ttk.Label(frame, text="Сотрудник:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.issue_emp = ttk.Combobox(frame, width=25)   # <--- ОБЫЧНЫЙ COMBOBOX
        self.issue_emp.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_employee).grid(row=1, column=2, padx=2, pady=5)
        ttk.Button(frame, text="✏️", width=3, command=self.edit_employee_dialog).grid(row=1, column=3, padx=1, pady=5)
        ttk.Button(frame, text="🗑️", width=3, command=self.delete_employee_dialog).grid(row=1, column=4, padx=1, pady=5)
        
        # ----- МОДЕЛЬ -----
        ttk.Label(frame, text="Модель:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.issue_model = AutocompleteCombobox(frame, values=db.get_models(), width=25)
        self.issue_model.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_model).grid(row=2, column=2, padx=2, pady=5)
        
        # ----- КОЛИЧЕСТВО -----
        ttk.Label(frame, text="Количество:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.issue_qty = ttk.Entry(frame, width=10)
        self.issue_qty.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.issue_qty.insert(0, "1")
        
        # ----- ДАТА -----
        ttk.Label(frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.issue_date = ttk.Entry(frame, width=15)
        self.issue_date.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        self.issue_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # ----- ПРИМЕЧАНИЕ -----
        ttk.Label(frame, text="Примечание:").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        self.issue_notes = ttk.Entry(frame, width=40)
        self.issue_notes.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        
        # ----- КНОПКИ ДЕЙСТВИЙ -----
        btn_action_frame = ttk.Frame(frame)
        btn_action_frame.grid(row=6, column=0, columnspan=5, pady=10)
        ttk.Button(btn_action_frame, text="📤 Выдать", command=self.on_issue).pack(side='left', padx=5)
        ttk.Button(btn_action_frame, text="↩️ Отменить выдачу", command=self.on_undo_issue).pack(side='left', padx=5)
        
        # ----- ДОБАВЛЕНИЕ СПРАВОЧНИКОВ -----
        add_frame = ttk.LabelFrame(frame, text="➕ Добавление справочников", padding=5)
        add_frame.grid(row=7, column=0, columnspan=5, pady=5, sticky='ew')
        
        ttk.Label(add_frame, text="Отдел:").grid(row=0, column=0, padx=5, pady=2, sticky='e')
        self.new_dept_entry = ttk.Entry(add_frame, width=15)
        self.new_dept_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(add_frame, text="➕", width=3, command=self.on_add_department).grid(row=0, column=2, padx=2, pady=2)
        
        ttk.Label(add_frame, text="Сотрудник:").grid(row=0, column=3, padx=5, pady=2, sticky='e')
        self.new_emp_entry = ttk.Entry(add_frame, width=15)
        self.new_emp_entry.grid(row=0, column=4, padx=5, pady=2)
        self.new_emp_dept = ttk.Combobox(add_frame, values=db.get_departments(), width=12)
        self.new_emp_dept.grid(row=0, column=5, padx=5, pady=2)
        ttk.Button(add_frame, text="➕", width=3, command=self.on_add_employee).grid(row=0, column=6, padx=2, pady=2)
        
        # ----- ТАБЛИЦА ВЫДАЧ С ПРОКРУТКОЙ -----
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=8, column=0, columnspan=5, padx=5, pady=5, sticky='nsew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.issue_tree = ttk.Treeview(tree_frame, columns=('id', 'dept', 'emp', 'model', 'qty', 'date'), 
                                        show='headings', height=6)
        self.issue_tree.heading('id', text='ID')
        self.issue_tree.heading('dept', text='Отдел')
        self.issue_tree.heading('emp', text='Сотрудник')
        self.issue_tree.heading('model', text='Модель')
        self.issue_tree.heading('qty', text='Кол-во')
        self.issue_tree.heading('date', text='Дата')
        self.issue_tree.column('id', width=0, stretch=False)
        self.issue_tree.column('dept', width=120)
        self.issue_tree.column('emp', width=120)
        self.issue_tree.column('model', width=120)
        self.issue_tree.column('qty', width=60)
        self.issue_tree.column('date', width=80)
        self.issue_tree.grid(row=0, column=0, sticky='nsew')
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient='vertical', command=self.issue_tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.issue_tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        self.issue_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Контекстное меню для таблицы выдач
        self.context_menu = tk.Menu(self.issue_tree, tearoff=0)
        self.context_menu.add_command(label="↩️ Отменить выдачу", command=self.on_undo_issue)
        self.issue_tree.bind("<Button-3>", self.show_context_menu)
        
        self.refresh_issues()
    
    def setup_reports_tab(self):
        frame = self.tab_reports
        ttk.Button(frame, text="📊 Отчет за месяц", command=self.on_report_month).pack(pady=5)
        ttk.Button(frame, text="📈 Отчет за год", command=self.on_report_year).pack(pady=5)
        ttk.Button(frame, text="📋 Отчет по остаткам", command=self.on_report_stock).pack(pady=5)
        ttk.Button(frame, text="📄 Отчет по шаблону", command=self.on_custom_report).pack(pady=5)
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(frame, text="📤 Экспорт базы (бекап)", command=self.on_backup).pack(pady=5)
        ttk.Button(frame, text="📥 Восстановить из бекапа", command=self.on_restore).pack(pady=5)
    
    # ---------- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ----------
    
    def show_context_menu(self, event):
        """Показывает контекстное меню для таблицы выдач"""
        item = self.issue_tree.identify_row(event.y)
        if item:
            self.issue_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def update_employees(self, event):
        dept = self.issue_dept.get()
        if dept:
            self.issue_emp['values'] = db.get_employees(dept)
            self.issue_emp.set('')
    
    def refresh_stock(self):
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        for row in db.get_stock():
            self.stock_tree.insert('', 'end', values=row)
        
        models = db.get_models()
        self.wh_model['values'] = models
        self.inv_model['values'] = models
        # issue_model обновляется в refresh_issues
    
    def refresh_issues(self):
        for item in self.issue_tree.get_children():
            self.issue_tree.delete(item)
        conn = sqlite3.connect('inventory.db')
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id, d.name, e.name, m.model, i.quantity, i.issue_date
            FROM issues i
            JOIN departments d ON i.department_id = d.id
            JOIN employees e ON i.employee_id = e.id
            JOIN models m ON i.model_id = m.id
            WHERE i.status = 'issued'
            ORDER BY i.issue_date DESC LIMIT 20
        """)
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            self.issue_tree.insert('', 'end', values=row)
        
        depts = db.get_departments()
        self.issue_dept['values'] = depts
        self.new_emp_dept['values'] = depts
        self.issue_model['values'] = db.get_models()
    
    # ---------- БЫСТРОЕ ДОБАВЛЕНИЕ ----------
    
    def on_quick_add_model(self):
        """Быстрое добавление модели через простой диалог"""
        name = simpledialog.askstring("Новая модель", "Введите название модели:")
        if name and name.strip():
            success, msg = db.add_model(name.strip())
            if success:
                messagebox.showinfo("Успех", f"Модель '{name}' добавлена")
                self.refresh_stock()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def on_quick_add_department(self):
        """Быстрое добавление отдела через простой диалог"""
        name = simpledialog.askstring("Новый отдел", "Введите название отдела:")
        if name and name.strip():
            success, msg = db.add_department(name.strip())
            if success:
                messagebox.showinfo("Успех", f"Отдел '{name}' добавлен")
                self.refresh_issues()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def on_quick_add_employee(self):
        """Быстрое добавление сотрудника через простой диалог"""
        dept = self.issue_dept.get()
        if not dept:
            messagebox.showerror("Ошибка", "Сначала выберите отдел!")
            return
        name = simpledialog.askstring("Новый сотрудник", f"Введите имя сотрудника (отдел: {dept}):")
        if name and name.strip():
            success, msg = db.add_employee(name.strip(), dept)
            if success:
                messagebox.showinfo("Успех", f"Сотрудник '{name}' добавлен")
                self.refresh_issues()
                self.update_employees(None)
            else:
                messagebox.showerror("Ошибка", msg)
    
    # ---------- ДОБАВЛЕНИЕ МОДЕЛИ С ОСТАТКОМ ----------
    
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
            db.add_incoming(name, qty, "Начальный остаток при создании модели")
        
        messagebox.showinfo("Успех", f"Модель '{name}' добавлена с остатком {qty} шт.")
        self.new_model_entry.delete(0, 'end')
        self.new_model_qty.delete(0, 'end')
        self.new_model_qty.insert(0, "0")
        self.refresh_stock()
    
    # ---------- ДВОЙНОЙ КЛИК ПО ТАБЛИЦЕ ОСТАТКОВ ----------
    
    def on_stock_double_click(self, event):
        """При двойном клике по таблице остатков открывается редактирование модели"""
        selected = self.stock_tree.selection()
        if not selected:
            return
        values = self.stock_tree.item(selected[0], 'values')
        model_name = values[0]
        self.edit_model_name_dialog(model_name)
    
    def edit_model_name_dialog(self, old_name):
        """Диалог переименования модели"""
        dialog = tk.Toplevel(self.root)
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
    
    # ---------- ОСТАЛЬНЫЕ МЕТОДЫ ----------
    
    def on_receive(self):
        model = self.wh_model.get()
        try:
            qty = int(self.wh_qty.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество!")
            return
        notes = self.wh_notes.get()
        if not model or qty <= 0:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        db.add_incoming(model, qty, notes)
        messagebox.showinfo("Успех", f"Приход: {model} x{qty}")
        self.wh_qty.delete(0, 'end')
        self.wh_notes.delete(0, 'end')
        self.refresh_stock()
    
    def on_issue(self):
        dept = self.issue_dept.get()
        emp = self.issue_emp.get()
        model = self.issue_model.get()
        try:
            qty = int(self.issue_qty.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество!")
            return
        issue_date = self.issue_date.get().strip()
        if not issue_date:
            issue_date = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(issue_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты!")
                return
        notes = self.issue_notes.get()
        if not dept or not emp or not model or qty <= 0:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        stock = db.get_stock(model)
        if stock and stock[0][3] < qty:
            messagebox.showerror("Ошибка", f"Недостаточно картриджей!\nОстаток: {stock[0][3]}")
            return
        db.add_issue(model, dept, emp, qty, issue_date, notes)
        messagebox.showinfo("Успех", f"Выдано: {model} отделу {dept}\nДата: {issue_date}")
        self.issue_qty.delete(0, 'end')
        self.issue_qty.insert(0, "1")
        self.issue_notes.delete(0, 'end')
        self.refresh_issues()
        self.refresh_stock()
    
    def on_undo_issue(self):
        selected = self.issue_tree.selection()
        if not selected:
            messagebox.showinfo("Информация", "Выберите выдачу в списке!")
            return
        values = self.issue_tree.item(selected[0], 'values')
        issue_id = values[0]
        dept = values[1]
        emp = values[2]
        model = values[3]
        qty = values[4]
        date = values[5]
        if not messagebox.askyesno("Подтверждение", 
                                   f"Отменить выдачу?\n"
                                   f"Отдел: {dept}\n"
                                   f"Сотрудник: {emp}\n"
                                   f"Модель: {model}\n"
                                   f"Количество: {qty}\n"
                                   f"Дата: {date}"):
            return
        if db.delete_issue(issue_id):
            messagebox.showinfo("Успех", f"Выдача отменена!\n{model} x{qty} возвращены на склад.")
            self.refresh_issues()
            self.refresh_stock()
        else:
            messagebox.showerror("Ошибка", "Не удалось отменить выдачу!")
    
    def on_inv_model_select(self, event):
        model = self.inv_model.get()
        if model:
            stock = db.get_stock(model)
            if stock:
                self.inv_current_stock.config(text=str(stock[0][3]))
            else:
                self.inv_current_stock.config(text="0")
    
    def on_inventory_correction(self):
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
    
    def on_add_department(self):
        name = self.new_dept_entry.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название отдела!")
            return
        success, msg = db.add_department(name)
        if success:
            messagebox.showinfo("Успех", f"Отдел '{name}' добавлен")
            self.new_dept_entry.delete(0, 'end')
            self.refresh_issues()
        else:
            messagebox.showerror("Ошибка", msg)
    
    def on_add_employee(self):
        name = self.new_emp_entry.get().strip()
        dept = self.new_emp_dept.get()
        if not name or not dept:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        success, msg = db.add_employee(name, dept)
        if success:
            messagebox.showinfo("Успех", f"Сотрудник '{name}' добавлен")
            self.new_emp_entry.delete(0, 'end')
            self.new_emp_dept.set('')
            self.refresh_issues()
            self.update_employees(None)
        else:
            messagebox.showerror("Ошибка", msg)
    
    def delete_department_dialog(self):
        dept = self.issue_dept.get()
        if not dept:
            messagebox.showinfo("Информация", "Выберите отдел в списке!")
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить отдел '{dept}'?"):
            return
        success, msg = db.delete_department(dept)
        if success:
            messagebox.showinfo("Успех", f"Отдел '{dept}' удален")
            self.refresh_issues()
        else:
            messagebox.showerror("Ошибка", msg)
    
    def delete_employee_dialog(self):
        emp = self.issue_emp.get()
        if not emp:
            messagebox.showinfo("Информация", "Выберите сотрудника в списке!")
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить сотрудника '{emp}'?"):
            return
        success, msg = db.delete_employee(emp)
        if success:
            messagebox.showinfo("Успех", f"Сотрудник '{emp}' удален")
            self.refresh_issues()
            self.update_employees(None)
        else:
            messagebox.showerror("Ошибка", msg)
    
    def edit_department_dialog(self):
        dept = self.issue_dept.get()
        if not dept:
            messagebox.showinfo("Информация", "Выберите отдел в списке!")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактировать отдел")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.grab_set()
        ttk.Label(dialog, text=f"Редактирование: {dept}").pack(pady=5)
        ttk.Label(dialog, text="Новое название:").pack(pady=5)
        new_name_entry = ttk.Entry(dialog, width=30)
        new_name_entry.pack()
        new_name_entry.insert(0, dept)
        new_name_entry.focus()
        
        def save():
            new_name = new_name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Ошибка", "Введите название!")
                return
            success, msg = db.rename_department(dept, new_name)
            if success:
                messagebox.showinfo("Успех", f"Отдел переименован: {dept} → {new_name}")
                dialog.destroy()
                self.refresh_issues()
            else:
                messagebox.showerror("Ошибка", msg)
        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=10)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack()
    
    def edit_employee_dialog(self):
        emp = self.issue_emp.get()
        if not emp:
            messagebox.showinfo("Информация", "Выберите сотрудника в списке!")
            return
        dept = self.issue_dept.get()
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактировать сотрудника")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        ttk.Label(dialog, text=f"Редактирование: {emp}").pack(pady=5)
        ttk.Label(dialog, text="Новое имя:").pack(pady=5)
        new_name_entry = ttk.Entry(dialog, width=30)
        new_name_entry.pack()
        new_name_entry.insert(0, emp)
        ttk.Label(dialog, text="Новый отдел:").pack(pady=5)
        dept_combo = ttk.Combobox(dialog, values=db.get_departments(), width=28)
        dept_combo.pack()
        dept_combo.set(dept)
        
        def save():
            new_name = new_name_entry.get().strip()
            new_dept = dept_combo.get()
            if not new_name or not new_dept:
                messagebox.showerror("Ошибка", "Заполните все поля!")
                return
            success, msg = db.rename_employee(emp, new_name, new_dept)
            if success:
                messagebox.showinfo("Успех", f"Сотрудник обновлен: {emp} → {new_name} ({new_dept})")
                dialog.destroy()
                self.refresh_issues()
                self.update_employees(None)
            else:
                messagebox.showerror("Ошибка", msg)
        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=10)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack()
    
    def delete_model_dialog(self):
        selected = self.stock_tree.selection()
        if not selected:
            messagebox.showinfo("Информация", "Выберите модель в таблице!")
            return
        values = self.stock_tree.item(selected[0], 'values')
        name = values[0]
        if not messagebox.askyesno("Подтверждение", f"Удалить модель '{name}'?"):
            return
        success, msg = db.delete_model(name)
        if success:
            messagebox.showinfo("Успех", f"Модель '{name}' удалена")
            self.refresh_stock()
        else:
            messagebox.showerror("Ошибка", msg)
    
    # ---------- ОТЧЕТЫ ----------
    
    def on_report_month(self):
        month = simpledialog.askinteger("Месяц", "Введите месяц (1-12):", minvalue=1, maxvalue=12)
        if month is None:
            return
        year = simpledialog.askinteger("Год", "Введите год:", minvalue=2000, maxvalue=2100)
        if year is None:
            return
        filename = utils.generate_report('month', year, month)
        if filename:
            messagebox.showinfo("Успех", f"Отчет сохранен:\n{filename}")
            os.startfile(filename)
        else:
            messagebox.showinfo("Информация", "Нет данных")
    
    def on_report_year(self):
        year = simpledialog.askinteger("Год", "Введите год:", minvalue=2000, maxvalue=2100)
        if year is None:
            return
        filename = utils.generate_report('year', year)
        if filename:
            messagebox.showinfo("Успех", f"Отчет сохранен:\n{filename}")
            os.startfile(filename)
        else:
            messagebox.showinfo("Информация", "Нет данных")
    
    def on_report_stock(self):
        filename = utils.generate_report('stock')
        if filename:
            messagebox.showinfo("Успех", f"Отчет сохранен:\n{filename}")
            os.startfile(filename)
        else:
            messagebox.showinfo("Информация", "Нет данных")
    
    def on_custom_report(self):
        month = simpledialog.askinteger("Месяц", "Введите месяц (1-12):", minvalue=1, maxvalue=12)
        if month is None:
            return
        year = simpledialog.askinteger("Год", "Введите год:", minvalue=2000, maxvalue=2100)
        if year is None:
            return
        filename = utils.generate_custom_report(month, year)
        if filename:
            messagebox.showinfo("Успех", f"Отчет сохранен:\n{filename}")
            os.startfile(filename)
        else:
            messagebox.showinfo("Информация", "Нет данных за указанный период или шаблон не найден.")
    
    def on_backup(self):
        try:
            filename = utils.backup_database()
            messagebox.showinfo("Успех", f"Бэкап создан:\n{filename}")
            os.startfile('backups')
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать бэкап:\n{str(e)}")
    
    def on_restore(self):
        if not messagebox.askyesno("Внимание!", 
                                   "Восстановление ЗАМЕНИТ все текущие данные на данные из бэкапа!\n"
                                   "Сделайте бэкап текущей базы перед восстановлением.\n\n"
                                   "Продолжить?"):
            return
        
        filepath = filedialog.askopenfilename(
            title="Выберите файл бэкапа",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        success, msg = utils.restore_from_backup(filepath)
        if success:
            messagebox.showinfo("Успех", msg)
            self.refresh_stock()
            self.refresh_issues()
        else:
            messagebox.showerror("Ошибка", msg)

if __name__ == "__main__":
    db.init_db()
    root = tk.Tk()
    app = App(root)
    root.mainloop()