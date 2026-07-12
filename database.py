import sqlite3
from datetime import datetime

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---

def init_db():
    """Создает пустую базу данных без тестовых данных"""
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    
    cur.execute('''CREATE TABLE IF NOT EXISTS departments 
                   (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS employees 
                   (id INTEGER PRIMARY KEY, name TEXT, department_id INTEGER,
                    FOREIGN KEY(department_id) REFERENCES departments(id))''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS models 
                   (id INTEGER PRIMARY KEY, model TEXT UNIQUE)''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS incoming 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER,
                    quantity INTEGER,
                    receive_date TEXT,
                    notes TEXT,
                    FOREIGN KEY(model_id) REFERENCES models(id))''')
    
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
    
    conn.commit()
    conn.close()

# --- ПОЛУЧЕНИЕ ДАННЫХ ---

def get_departments():
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM departments ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_employees(department=None):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    if department:
        cur.execute("""
            SELECT e.name FROM employees e
            JOIN departments d ON e.department_id = d.id
            WHERE d.name = ?
            ORDER BY e.name
        """, (department,))
    else:
        cur.execute("SELECT name FROM employees ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_models():
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    cur.execute("SELECT model FROM models ORDER BY model")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_stock(model=None):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    if model:
        filter_sql = "WHERE m.model = ?"
        params = (model,)
    else:
        filter_sql = ""
        params = ()
    query = f"""
        SELECT 
            m.model,
            COALESCE(SUM(inc.quantity), 0) AS total_in,
            COALESCE(SUM(iss.quantity), 0) AS total_out,
            COALESCE(SUM(inc.quantity), 0) - COALESCE(SUM(iss.quantity), 0) AS stock
        FROM models m
        LEFT JOIN incoming inc ON m.id = inc.model_id
        LEFT JOIN issues iss ON m.id = iss.model_id AND iss.status = 'issued'
        {filter_sql}
        GROUP BY m.id
        ORDER BY m.model
    """
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# --- ДОБАВЛЕНИЕ ---

def add_incoming(model, quantity, notes=''):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    cur.execute("SELECT id FROM models WHERE model=?", (model,))
    model_id = cur.fetchone()[0]
    cur.execute("INSERT INTO incoming (model_id, quantity, receive_date, notes) VALUES (?, ?, ?, ?)",
                (model_id, quantity, datetime.now().strftime("%Y-%m-%d"), notes))
    conn.commit()
    conn.close()

def add_issue(model, department, employee, quantity, issue_date, notes=''):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    cur.execute("SELECT id FROM models WHERE model=?", (model,))
    model_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM departments WHERE name=?", (department,))
    dept_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM employees WHERE name=?", (employee,))
    emp_id = cur.fetchone()[0]
    cur.execute("""INSERT INTO issues 
                   (model_id, department_id, employee_id, quantity, issue_date, notes) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (model_id, dept_id, emp_id, quantity, issue_date, notes))
    conn.commit()
    conn.close()

def add_department(name):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO departments (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Отдел уже существует!"

def add_employee(name, department):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    cur.execute("SELECT id FROM departments WHERE name=?", (department,))
    dept_id = cur.fetchone()[0]
    try:
        cur.execute("INSERT INTO employees (name, department_id) VALUES (?, ?)", (name, dept_id))
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Сотрудник уже существует!"

def add_model(name):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO models (model) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Модель уже существует!"

# --- УДАЛЕНИЕ ---

def delete_issue(issue_id):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM issues WHERE id=?", (issue_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

def delete_department(name):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM issues i JOIN departments d ON i.department_id = d.id WHERE d.name = ?", (name,))
        if cur.fetchone()[0] > 0:
            conn.close()
            return False, "Есть выданные картриджи. Сначала верните их."
        cur.execute("DELETE FROM departments WHERE name=?", (name,))
        conn.commit()
        conn.close()
        return True, ""
    except Exception as e:
        conn.close()
        return False, str(e)

def delete_employee(name):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM issues i JOIN employees e ON i.employee_id = e.id WHERE e.name = ?", (name,))
        if cur.fetchone()[0] > 0:
            conn.close()
            return False, "У сотрудника есть выданные картриджи. Сначала верните их."
        cur.execute("DELETE FROM employees WHERE name=?", (name,))
        conn.commit()
        conn.close()
        return True, ""
    except Exception as e:
        conn.close()
        return False, str(e)

def delete_model(name):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM incoming WHERE model_id IN (SELECT id FROM models WHERE model=?)", (name,))
        if cur.fetchone()[0] > 0:
            conn.close()
            return False, "По этой модели есть приходы. Удалите их сначала."
        cur.execute("SELECT COUNT(*) FROM issues WHERE model_id IN (SELECT id FROM models WHERE model=?)", (name,))
        if cur.fetchone()[0] > 0:
            conn.close()
            return False, "По этой модели есть выдачи. Сначала верните их."
        cur.execute("DELETE FROM models WHERE model=?", (name,))
        conn.commit()
        conn.close()
        return True, ""
    except Exception as e:
        conn.close()
        return False, str(e)

# --- РЕДАКТИРОВАНИЕ ---

def rename_department(old_name, new_name):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("UPDATE departments SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Отдел с таким именем уже существует!"

def rename_employee(old_name, new_name, department):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM departments WHERE name=?", (department,))
        dept_id = cur.fetchone()[0]
        cur.execute("UPDATE employees SET name=?, department_id=? WHERE name=?", (new_name, dept_id, old_name))
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Сотрудник с таким именем уже существует!"

def rename_model(old_name, new_name):
    conn = sqlite3.connect('inventory.db')
    cur = conn.cursor()
    try:
        cur.execute("UPDATE models SET model=? WHERE model=?", (new_name, old_name))
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Модель с таким именем уже существует!"