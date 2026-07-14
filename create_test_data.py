"""
Скрипт для создания тестовой базы данных с демонстрационными данными.
Запускается отдельно, не влияет на основную программу.
"""

import sqlite3
import random
from datetime import datetime, timedelta

# --- Конфигурация ---
DB_NAME = 'inventory_test.db'  # Отдельный файл, не трогает основную базу

# --- Тестовые данные ---
DEPARTMENTS = [
    "Бухгалтерия",
    "Отдел продаж",
    "IT отдел",
    "Служба Информации",
    "Отдел кадров",
    "Лаборатория",
    "СОС"
]

EMPLOYEES = {
    "Бухгалтерия": ["Иванов И.И.", "Петрова П.П.", "Сидорова С.С."],
    "Отдел продаж": ["Козлов К.К.", "Михайлов М.М.", "Федоров Ф.Ф."],
    "IT отдел": ["Свешникова А.А.", "Шторц И.И.", "Карпухин И.С."],
    "Служба Информации": ["Якимович С.А.", "Громов Г.Г."],
    "Отдел кадров": ["Морозова М.М.", "Веснина В.В."],
    "Лаборатория": ["Лабораторный Л.Л.", "Тестов Т.Т."],
    "СОС": ["Соснов С.С.", "Осипов О.О."]
}

MODELS = [
    "CF283A", "CE285A", "Q7553A", "505X", "1106а",
    "HP 85A", "HP 80A", "Samsung MLT-D101S", "Canon 728",
    "Xerox 106R", "Brother TN-241", "Epson T6641"
]

SUPPLIERS = ["ООО 'Компьютер-Сервис'", "ИП Иванов", "ООО 'ТехноСнаб'", "ООО 'Офис-Торг'"]

# --- Функции ---

def random_date(start_date, end_date):
    """Генерирует случайную дату между start_date и end_date"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def create_test_db():
    """Создает тестовую базу с демонстрационными данными"""
    
    # Удаляем старую тестовую базу, если есть
    import os
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # --- Создаем структуру ---
    
    # Отделы
    cur.execute('''CREATE TABLE IF NOT EXISTS departments 
                   (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    
    # Сотрудники
    cur.execute('''CREATE TABLE IF NOT EXISTS employees 
                   (id INTEGER PRIMARY KEY, name TEXT, department_id INTEGER,
                    FOREIGN KEY(department_id) REFERENCES departments(id))''')
    
    # Модели
    cur.execute('''CREATE TABLE IF NOT EXISTS models 
                   (id INTEGER PRIMARY KEY, model TEXT UNIQUE)''')
    
    # Приход
    cur.execute('''CREATE TABLE IF NOT EXISTS incoming 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER,
                    quantity INTEGER,
                    receive_date TEXT,
                    supplier TEXT,
                    price REAL,
                    notes TEXT,
                    FOREIGN KEY(model_id) REFERENCES models(id))''')
    
    # Выдачи
    cur.execute('''CREATE TABLE IF NOT EXISTS issues 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER,
                    department_id INTEGER,
                    employee_id INTEGER,
                    quantity INTEGER,
                    issue_date TEXT,
                    status TEXT DEFAULT 'issued',
                    notes TEXT,
                    FOREIGN KEY(model_id) REFERENCES models(id),
                    FOREIGN KEY(department_id) REFERENCES departments(id),
                    FOREIGN KEY(employee_id) REFERENCES employees(id))''')
    
    # --- Заполняем данными ---
    
    # 1. Отделы
    dept_ids = {}
    for dept in DEPARTMENTS:
        cur.execute("INSERT INTO departments (name) VALUES (?)", (dept,))
        dept_ids[dept] = cur.lastrowid
    
    # 2. Сотрудники
    emp_ids = {}
    for dept, employees in EMPLOYEES.items():
        dept_id = dept_ids[dept]
        for emp in employees:
            cur.execute("INSERT INTO employees (name, department_id) VALUES (?, ?)", (emp, dept_id))
            emp_ids[emp] = cur.lastrowid
    
    # 3. Модели
    model_ids = {}
    for model in MODELS:
        cur.execute("INSERT INTO models (model) VALUES (?)", (model,))
        model_ids[model] = cur.lastrowid
    
    # 4. Приходы (за последние 12 месяцев)
    today = datetime.now().date()
    start_date = today - timedelta(days=365)
    
    for model, model_id in model_ids.items():
        # Каждая модель поступала 3-5 раз
        num_orders = random.randint(3, 6)
        for _ in range(num_orders):
            qty = random.randint(3, 15)
            date = random_date(start_date, today)
            supplier = random.choice(SUPPLIERS)
            price = round(random.uniform(500, 3000), 2)
            notes = random.choice(["", "Срочный заказ", "По договору", "Акция"])
            
            cur.execute("""INSERT INTO incoming 
                           (model_id, quantity, receive_date, supplier, price, notes) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (model_id, qty, date.strftime("%Y-%m-%d"), supplier, price, notes))
    
    # 5. Выдачи (за последние 12 месяцев)
    for _ in range(120):  # 120 случайных выдач
        model = random.choice(MODELS)
        model_id = model_ids[model]
        
        dept = random.choice(DEPARTMENTS)
        dept_id = dept_ids[dept]
        
        # Сотрудник из этого отдела
        dept_employees = EMPLOYEES[dept]
        emp = random.choice(dept_employees)
        emp_id = emp_ids[emp]
        
        qty = random.randint(1, 3)
        date = random_date(start_date, today)
        notes = random.choice(["", "Срочно", "Замена", "Для нового сотрудника"])
        
        cur.execute("""INSERT INTO issues 
                       (model_id, department_id, employee_id, quantity, issue_date, notes) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (model_id, dept_id, emp_id, qty, date.strftime("%Y-%m-%d"), notes))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Тестовая база создана: {DB_NAME}")
    print(f"   - Отделов: {len(DEPARTMENTS)}")
    print(f"   - Сотрудников: {sum(len(emps) for emps in EMPLOYEES.values())}")
    print(f"   - Моделей: {len(MODELS)}")
    print(f"   - Приходов: ~{len(MODELS) * 4}")
    print(f"   - Выдач: 120")
    print("\nСкопируйте файл и переименуйте в inventory.db, чтобы использовать в программе.")

if __name__ == "__main__":
    create_test_db()