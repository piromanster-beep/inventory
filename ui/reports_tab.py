import os
from tkinter import ttk, messagebox, simpledialog, filedialog
from core import utils
from core import database as db

class ReportsTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="📊 Отчеты")
        self.setup_ui()
    
    def setup_ui(self):
        frame = self.frame
        
        ttk.Button(frame, text="📊 Отчет за месяц", command=self.on_report_month).pack(pady=5)
        ttk.Button(frame, text="📈 Отчет за год", command=self.on_report_year).pack(pady=5)
        ttk.Button(frame, text="📋 Отчет по остаткам", command=self.on_report_stock).pack(pady=5)
        ttk.Button(frame, text="📄 Отчет по шаблону", command=self.on_custom_report).pack(pady=5)
        ttk.Button(frame, text="🏢 Расход по отделам", command=self.on_department_report).pack(pady=5)
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(frame, text="📤 Экспорт базы (бекап)", command=self.on_backup).pack(pady=5)
        ttk.Button(frame, text="📥 Восстановить из бекапа", command=self.on_restore).pack(pady=5)
    
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
        else:
            messagebox.showerror("Ошибка", msg)
            
    def on_department_report(self):
        """Генерирует отчёт по расходам по отделам"""
        # Спрашиваем период
        period = simpledialog.askstring(
            "Период",
            "Выберите период:\n"
            "1 - за месяц\n"
            "2 - за год\n\n"
            "Введите 1 или 2:"
        )
    
        if period not in ('1', '2'):
            messagebox.showinfo("Информация", "Отчёт отменён или выбран неверный период")
            return
    
        year = simpledialog.askinteger("Год", "Введите год:", minvalue=2000, maxvalue=2100)
        if year is None:
            return
    
        month = None
        if period == '1':  # За месяц
            month = simpledialog.askinteger("Месяц", "Введите месяц (1-12):", minvalue=1, maxvalue=12)
            if month is None:
                return
    
        filename = utils.generate_department_report(year, month)
        if filename:
            messagebox.showinfo("Успех", f"Отчёт сохранен:\n{filename}")
            os.startfile(filename)
        else:
            messagebox.showinfo("Информация", "Нет данных за указанный период")