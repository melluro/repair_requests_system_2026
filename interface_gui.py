import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from services import (
    add_client, add_request, get_requests_by_user,
    update_request_status, assign_specialist,
    add_specialist, complete_request,
    register_user, login_user, get_connection
)
from stats_module import calculate_statistics
from datetime import datetime, timedelta

current_user = None

# -------------------- Вход и регистрация --------------------
def login_window(root):
    def do_login():
        global current_user
        username = entry_username.get()
        password = entry_password.get()
        user = login_user(username, password)
        if user:
            current_user = user
            messagebox.showinfo("Успех", f"Вход выполнен! Роль: {user['role']}")
            root.destroy()
            main_menu_gui()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    root.title("Вход в систему")
    root.geometry("400x250")
    root.resizable(False, False)

    tk.Label(root, text="Вход в систему", font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(root, text="Логин").pack(pady=5)
    entry_username = tk.Entry(root, width=30)
    entry_username.pack()
    tk.Label(root, text="Пароль").pack(pady=5)
    entry_password = tk.Entry(root, show="*", width=30)
    entry_password.pack()
    tk.Button(root, text="Вход", width=20, bg="#4CAF50", fg="white", command=do_login).pack(pady=10)
    tk.Button(root, text="Регистрация", width=20, bg="#2196F3", fg="white",
              command=lambda: [root.destroy(), register_window()]).pack()

def register_window():
    def do_register():
        username = entry_username.get()
        password = entry_password.get()
        role = role_var.get()
        user_id = register_user(username, password, role)
        if user_id:
            messagebox.showinfo("Успех", "Регистрация выполнена")
            win.destroy()
            start_gui()
        else:
            messagebox.showerror("Ошибка", "Регистрация не удалась (логин может быть занят)")

    win = tk.Tk()
    win.title("Регистрация")
    win.geometry("400x300")
    win.resizable(False, False)

    tk.Label(win, text="Регистрация нового пользователя", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(win, text="Логин").pack(pady=5)
    entry_username = tk.Entry(win, width=30)
    entry_username.pack()
    tk.Label(win, text="Пароль").pack(pady=5)
    entry_password = tk.Entry(win, show="*", width=30)
    entry_password.pack()
    tk.Label(win, text="Роль").pack(pady=5)
    role_var = tk.StringVar(value="operator")
    tk.OptionMenu(win, role_var, "admin", "operator", "specialist").pack(pady=5)
    tk.Button(win, text="Зарегистрироваться", width=20, bg="#4CAF50", fg="white", command=do_register).pack(pady=10)
    win.mainloop()

# -------------------- Главное меню --------------------
def main_menu_gui():
    global current_user
    win = tk.Tk()
    win.title(f"Главное меню - {current_user['role']}")
    win.geometry("900x600")
    win.resizable(True, True)

    tk.Label(win, text=f"Добро пожаловать! Роль: {current_user['role']}", font=("Arial", 14, "bold")).pack(pady=10)

    # -------------------- Таблица заявок --------------------
    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    columns = ("Номер", "Оборудование", "Модель", "Описание", "Статус", "Клиент", "Специалист")
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")
    tree.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    # -------------------- Функции --------------------
    def refresh_tree():
        for row in tree.get_children():
            tree.delete(row)
        requests = get_requests_by_user(current_user)
        for r in requests:
            specialist = r[7] if len(r) > 7 and r[7] else "-"
            tree.insert("", tk.END, values=(r[1], r[2], r[3], r[4], r[5], r[6], specialist))

    refresh_tree()

    def get_selected_request_number():
        selected = tree.focus()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите заявку")
            return None
        return tree.item(selected)["values"][0]

    def logout():
        global current_user
        current_user = None
        win.destroy()
        start_gui()

    # -------------------- Действия --------------------
    def add_client_gui():
        if current_user['role'] not in ['admin', 'operator']:
            messagebox.showerror("Ошибка", "Нет прав")
            return
        name = simpledialog.askstring("Клиент", "ФИО клиента:")
        phone = simpledialog.askstring("Клиент", "Телефон:")
        if name and phone:
            add_client(name, phone)
            messagebox.showinfo("Успех", "Клиент добавлен")
            refresh_tree()

    def add_request_gui():
        if current_user['role'] not in ['admin', 'operator']:
            messagebox.showerror("Ошибка", "Нет прав")
            return
        client_id = simpledialog.askinteger("Заявка", "ID клиента:")
        req_number = simpledialog.askstring("Заявка", "Номер заявки:")
        eq_type = simpledialog.askstring("Заявка", "Тип оборудования:")
        eq_model = simpledialog.askstring("Заявка", "Модель:")
        problem = simpledialog.askstring("Заявка", "Описание проблемы:")
        if None not in [client_id, req_number, eq_type, eq_model, problem]:
            add_request(req_number, eq_type, eq_model, problem, client_id)
            messagebox.showinfo("Успех", "Заявка добавлена")
            refresh_tree()

    def update_status_gui():
        if current_user['role'] not in ['admin', 'operator', 'specialist']:
            messagebox.showerror("Ошибка", "Нет прав")
            return
        req_number = get_selected_request_number()
        if not req_number:
            return
        new_status = simpledialog.askstring("Статус", f"Новый статус для заявки {req_number}:")
        if new_status:
            update_request_status(req_number, new_status)
            messagebox.showinfo("Успех", "Статус обновлён")
            refresh_tree()

    def complete_request_gui():
        if current_user['role'] not in ['admin', 'operator', 'specialist']:
            messagebox.showerror("Ошибка", "Нет прав")
            return
        req_number = get_selected_request_number()
        if not req_number:
            return
        days = simpledialog.askinteger("Завершение", "Сколько дней длился ремонт?")
        if days:
            start = datetime.now() - timedelta(days=days)
            end = datetime.now()
            complete_request(req_number, start.isoformat(), end.isoformat())
            messagebox.showinfo("Успех", "Заявка завершена")
            refresh_tree()

    def assign_specialist_gui():
        if current_user['role'] not in ['admin', 'operator']:
            messagebox.showerror("Ошибка", "Нет прав")
            return
        req_number = get_selected_request_number()
        if not req_number:
            return
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, full_name FROM specialists")
        specialists = cursor.fetchall()
        connection.close()
        if not specialists:
            messagebox.showwarning("Специалисты", "Нет специалистов для назначения")
            return
        win_assign = tk.Toplevel()
        win_assign.title("Назначение специалиста")
        tk.Label(win_assign, text="Выберите специалиста:", font=("Arial", 12, "bold")).pack(pady=5)
        specialist_var = tk.StringVar()
        specialist_var.set(f"{specialists[0][0]} - {specialists[0][1]}")
        options = [f"{s[0]} - {s[1]}" for s in specialists]
        tk.OptionMenu(win_assign, specialist_var, *options).pack(pady=5)
        def assign():
            specialist_id = int(specialist_var.get().split(" - ")[0])
            assign_specialist(req_number, specialist_id)
            messagebox.showinfo("Успех", "Специалист назначен")
            win_assign.destroy()
            refresh_tree()
        tk.Button(win_assign, text="Назначить", bg="#4CAF50", fg="white", width=25, height=2,
                  command=assign).pack(pady=10)

    def add_specialist_gui():
        if current_user['role'] != 'admin':
            messagebox.showerror("Ошибка", "Только администратор")
            return
        name = simpledialog.askstring("Специалист", "ФИО специалиста:")
        spec = simpledialog.askstring("Специалист", "Специализация (необязательно):")
        if name:
            add_specialist(name, spec)
            messagebox.showinfo("Успех", "Специалист добавлен")
            refresh_tree()

    def show_statistics_gui():
        if current_user['role'] not in ['admin', 'operator']:
            messagebox.showerror("Ошибка", "Нет прав")
            return
        stats = calculate_statistics()
        msg = f"Количество выполненных заявок: {stats['completed_count']}\n"
        msg += f"Среднее время ремонта (дней): {stats['average_days']:.2f}\n"
        msg += "Статистика по типам неисправностей:\n"
        for problem, count in stats['problem_types'].items():
            msg += f"  {problem}: {count}\n"
        messagebox.showinfo("Статистика", msg)

    # -------------------- Кнопки по ролям --------------------
    role_buttons = {
        "admin": [
            ("Добавить клиента", add_client_gui, "#4CAF50"),
            ("Добавить заявку", add_request_gui, "#4CAF50"),
            ("Изменить статус заявки", update_status_gui, "#FF9800"),
            ("Завершить заявку", complete_request_gui, "#795548"),
            ("Назначить специалиста", assign_specialist_gui, "#9C27B0"),
            ("Добавить специалиста", add_specialist_gui, "#607D8B"),
            ("Показать статистику", show_statistics_gui, "#E91E63"),
            ("Выйти из аккаунта", logout, "#F44336")
        ],
        "operator": [
            ("Добавить клиента", add_client_gui, "#4CAF50"),
            ("Добавить заявку", add_request_gui, "#4CAF50"),
            ("Изменить статус заявки", update_status_gui, "#FF9800"),
            ("Завершить заявку", complete_request_gui, "#795548"),
            ("Назначить специалиста", assign_specialist_gui, "#9C27B0"),
            ("Показать статистику", show_statistics_gui, "#E91E63"),
            ("Выйти из аккаунта", logout, "#F44336")
        ],
        "specialist": [
            ("Изменить статус заявки", update_status_gui, "#FF9800"),
            ("Завершить заявку", complete_request_gui, "#795548"),
            ("Выйти из аккаунта", logout, "#F44336")
        ]
    }

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    for text, func, color in role_buttons.get(current_user['role'], []):
        tk.Button(btn_frame, text=text, width=25, height=2, bg=color, fg="white", command=func).pack(pady=3)

    win.mainloop()


# -------------------- Запуск --------------------
def start_gui():
    root = tk.Tk()
    login_window(root)
    root.mainloop()


if __name__ == "__main__":
    start_gui()
