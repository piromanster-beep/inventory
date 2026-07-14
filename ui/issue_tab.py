import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
from core import database as db
from widgets.autocomplete import AutocompleteCombobox

class IssueTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="📤 Выдача")
        self.setup_ui()
        self.refresh_issues()
    
    def setup_ui(self):
        frame = self.frame
        frame.grid_rowconfigure(8, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        # ---- ОТДЕЛ ----
        ttk.Label(frame, text="Отдел:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.issue_dept = AutocompleteCombobox(frame, values=db.get_departments(), width=25)
        self.issue_dept.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.issue_dept.bind('<<ComboboxSelected>>', self.update_employees)
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_department).grid(row=0, column=2, padx=2, pady=5)
        ttk.Button(frame, text="✏️", width=3, command=self.edit_department_dialog).grid(row=0, column=3, padx=1, pady=5)
        ttk.Button(frame, text="🗑️", width=3, command=self.delete_department_dialog).grid(row=0, column=4, padx=1, pady=5)
        
        # ---- СОТРУДНИК (ОБЫЧНЫЙ СПИСОК) ----
        ttk.Label(frame, text="Сотрудник:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.issue_emp = ttk.Combobox(frame, width=25)
        self.issue_emp.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_employee).grid(row=1, column=2, padx=2, pady=5)
        ttk.Button(frame, text="✏️", width=3, command=self.edit_employee_dialog).grid(row=1, column=3, padx=1, pady=5)
        ttk.Button(frame, text="🗑️", width=3, command=self.delete_employee_dialog).grid(row=1, column=4, padx=1, pady=5)
        
        # ---- МОДЕЛЬ ----
        ttk.Label(frame, text="Модель:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.issue_model = AutocompleteCombobox(frame, values=db.get_models(), width=25)
        self.issue_model.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(frame, text="➕", width=3, command=self.on_quick_add_model).grid(row=2, column=2, padx=2, pady=5)
        
        # ---- КОЛИЧЕСТВО ----
        ttk.Label(frame, text="Количество:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.issue_qty = ttk.Entry(frame, width=10)
        self.issue_qty.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.issue_qty.insert(0, "1")
        
        # ---- ДАТА ----
        ttk.Label(frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.issue_date = ttk.Entry(frame, width=15)
        self.issue_date.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        self.issue_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # ---- ПРИМЕЧАНИЕ ----
        ttk.Label(frame, text="Примечание:").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        self.issue_notes = ttk.Entry(frame, width=40)
        self.issue_notes.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        
        # ---- КНОПКИ ----
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=5, pady=10)
        ttk.Button(btn_frame, text="📤 Выдать", command=self.on_issue).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="↩️ Отменить выдачу", command=self.on_undo_issue).pack(side='left', padx=5)
        
        # ---- ДОБАВЛЕНИЕ СПРАВОЧНИКОВ ----
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
        
        # ---- ТАБЛИЦА ВЫДАЧ ----
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
        
        self.context_menu = tk.Menu(self.issue_tree, tearoff=0)
        self.context_menu.add_command(label="↩️ Отменить выдачу", command=self.on_undo_issue)
        self.issue_tree.bind("<Button-3>", self.show_context_menu)
    
    # ---------- ВСПОМОГАТЕЛЬНЫЕ ----------
    
    def show_context_menu(self, event):
        item = self.issue_tree.identify_row(event.y)
        if item:
            self.issue_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def update_employees(self, event):
        dept = self.issue_dept.get()
        if dept:
            self.issue_emp['values'] = db.get_employees(dept)
            self.issue_emp.set('')
    
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
    
    # ---------- ОБРАБОТЧИКИ ----------
    
    def on_quick_add_model(self):
        from tkinter import simpledialog
        name = simpledialog.askstring("Новая модель", "Введите название модели:")
        if name and name.strip():
            success, msg = db.add_model(name.strip())
            if success:
                messagebox.showinfo("Успех", f"Модель '{name}' добавлена")
                self.refresh_issues()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def on_quick_add_department(self):
        from tkinter import simpledialog
        name = simpledialog.askstring("Новый отдел", "Введите название отдела:")
        if name and name.strip():
            success, msg = db.add_department(name.strip())
            if success:
                messagebox.showinfo("Успех", f"Отдел '{name}' добавлен")
                self.refresh_issues()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def on_quick_add_employee(self):
        from tkinter import simpledialog
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
        else:
            messagebox.showerror("Ошибка", "Не удалось отменить выдачу!")
    
    # ---------- ДИАЛОГИ УПРАВЛЕНИЯ СПРАВОЧНИКАМИ ----------
    
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
    
    def edit_department_dialog(self):
        dept = self.issue_dept.get()
        if not dept:
            messagebox.showinfo("Информация", "Выберите отдел в списке!")
            return
        dialog = tk.Toplevel()
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
        dialog = tk.Toplevel()
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