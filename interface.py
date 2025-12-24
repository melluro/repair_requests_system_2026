import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import urllib.request
import io
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from services import UserService, RequestService, PartService, ImportService, STATUS_NEW, STATUS_REGISTERED, STATUS_IN_PROGRESS, STATUS_WAITING_PARTS, STATUS_COMPLETED, STATUS_OVERDUE
from stats_module import calculate_statistics
from tkinter import filedialog

# Constants
FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdhZcExx6LSIXxk0ub55mSu-WIh23WYdGG9HY5EZhLDo7P8eA/viewform"

def setup_styles():
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
        
    # Modern Palette
    BG_COLOR = "#F8F9FA"    # Light Gray Background
    SIDEBAR_BG = "#FFFFFF"  # White Sidebar
    CARD_BG = "#FFFFFF"     # White Cards
    
    PRIMARY = "#0D6EFD"     # Bootstrap Blue
    SECONDARY = "#6C757D"   # Gray
    SUCCESS = "#198754"     # Green
    WARNING = "#FFC107"     # Yellow
    DANGER = "#DC3545"      # Red
    CREATE_BTN = "#E04F5F"  # Coral/Red from image
    
    TEXT_COLOR = "#212529"
    WHITE = "#FFFFFF"
    
    style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 10))
    style.configure("TFrame", background=BG_COLOR)
    style.configure("Sidebar.TFrame", background=SIDEBAR_BG)
    style.configure("Card.TFrame", background=CARD_BG, relief="solid", borderwidth=0)
    
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 10))
    style.configure("Sidebar.TLabel", background=SIDEBAR_BG, foreground=TEXT_COLOR, font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_COLOR)
    style.configure("CardHeader.TLabel", background=CARD_BG, foreground=TEXT_COLOR, font=("Segoe UI", 11, "bold"))
    style.configure("CardSub.TLabel", background=CARD_BG, foreground=SECONDARY, font=("Segoe UI", 9))
    
    # Buttons
    style.configure("TButton", background=PRIMARY, foreground=WHITE, borderwidth=0, focuscolor=PRIMARY, padding=(15, 8), font=("Segoe UI", 10, "bold"))
    style.map("TButton", background=[('active', "#0B5ED7")])
    
    style.configure("Create.TButton", background=CREATE_BTN, foreground=WHITE, borderwidth=0, focuscolor=CREATE_BTN, padding=(20, 10))
    style.map("Create.TButton", background=[('active', "#C0392B")])
    
    style.configure("Outline.TButton", background=WHITE, foreground=TEXT_COLOR, borderwidth=1, relief="solid")
    style.map("Outline.TButton", background=[('active', "#E9ECEF")], foreground=[('active', TEXT_COLOR)])
    
    style.configure("Sidebar.TButton", background=SIDEBAR_BG, foreground=TEXT_COLOR, borderwidth=0, anchor="w", padding=(20, 10), font=("Segoe UI", 11))
    style.map("Sidebar.TButton", background=[('active', "#E9ECEF")], foreground=[('active', PRIMARY)])

    style.configure("Header.TLabel", font=("Segoe UI", 24, "bold"), foreground="#212529", background=BG_COLOR)
    style.configure("SubHeader.TLabel", font=("Segoe UI", 12), foreground="#6C757D", background=BG_COLOR)
    
    return BG_COLOR

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Repair System - Вход")
        self.geometry("450x400")
        self.resizable(False, False)
        self.bg_color = setup_styles()
        self.configure(bg=self.bg_color)
        
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=30)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        ttk.Label(main_frame, text="Система Управления", style="Header.TLabel").pack(pady=(0, 5))
        ttk.Label(main_frame, text="Ремонтом Оборудования", style="SubHeader.TLabel").pack(pady=(0, 30))
        
        login_frame = ttk.Frame(main_frame)
        login_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(login_frame, text="Логин:").pack(anchor="w")
        self.username_entry = ttk.Entry(login_frame, font=("Segoe UI", 11))
        self.username_entry.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(login_frame, text="Пароль:").pack(anchor="w")
        self.password_entry = ttk.Entry(login_frame, show="*", font=("Segoe UI", 11))
        self.password_entry.pack(fill=tk.X, pady=(5, 20))
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Войти", command=self.login, style="TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(btn_frame, text="Регистрация", command=self.open_register, style="Outline.TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        user = UserService.login(username, password)
        if user:
            self.destroy()
            app = MainApp(user)
            app.mainloop()
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

    def open_register(self):
        RegistrationDialog(self)

class RegistrationDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Регистрация")
        self.geometry("350x450")
        self.configure(bg="#F3F4F6")
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Новый пользователь", style="Header.TLabel").pack(pady=(0, 20))

        ttk.Label(main_frame, text="Логин:").pack(anchor="w")
        self.u_entry = ttk.Entry(main_frame)
        self.u_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main_frame, text="Пароль:").pack(anchor="w")
        self.p_entry = ttk.Entry(main_frame, show="*")
        self.p_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main_frame, text="ФИО:").pack(anchor="w")
        self.n_entry = ttk.Entry(main_frame)
        self.n_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main_frame, text="Роль:").pack(anchor="w")
        self.role_var = tk.StringVar(value="Operator")
        roles = ["Administrator", "Operator", "Specialist", "Manager", "Quality Manager"]
        role_menu = ttk.OptionMenu(main_frame, self.role_var, roles[1], *roles)
        role_menu.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(main_frame, text="Зарегистрироваться", command=self.register, style="TButton").pack(fill=tk.X)

    def register(self):
        role_map = {
            "Administrator": 1, "Operator": 2, "Specialist": 3,
            "Manager": 4, "Quality Manager": 5
        }
        
        u = self.u_entry.get()
        p = self.p_entry.get()
        n = self.n_entry.get()
        r = self.role_var.get()

        if not all([u, p, n, r]):
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        if UserService.create_user(u, p, n, role_map[r]):
            messagebox.showinfo("Успех", "Пользователь зарегистрирован")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось создать пользователя (возможно, логин занят)")


class MainApp(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"ООО БытСервис - {user.full_name}")
        self.geometry("1200x800")
        self.configure(bg="#F8F9FA")
        
        self.create_layout()
        self.load_data()

    def create_layout(self):
        # Main Container (Sidebar + Content)
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # --- Sidebar (Left) ---
        sidebar = ttk.Frame(container, width=250, style="Sidebar.TFrame")
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # User Profile in Sidebar
        profile_frame = ttk.Frame(sidebar, style="Sidebar.TFrame", padding=20)
        profile_frame.pack(fill=tk.X)
        
        ttk.Label(profile_frame, text="👤", font=("Segoe UI", 30), style="Sidebar.TLabel").pack(anchor="w")
        ttk.Label(profile_frame, text=self.user.full_name, font=("Segoe UI", 12, "bold"), style="Sidebar.TLabel", wraplength=200).pack(anchor="w", pady=(10, 0))
        ttk.Label(profile_frame, text=f"Роль: {self.user.role_name}", font=("Segoe UI", 10), style="Sidebar.TLabel", foreground="#6C757D").pack(anchor="w")
        
        ttk.Separator(sidebar, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Navigation Buttons
        nav_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        nav_frame.pack(fill=tk.X, pady=10)
        
        self.create_nav_btn(nav_frame, "📋 Все заявки", self.load_data)
        
        if self.user.role_name in ['Administrator', 'Manager']:
            self.create_nav_btn(nav_frame, "📊 Статистика", self.show_statistics)
            
        if self.user.role_name == 'Administrator':
            self.create_nav_btn(nav_frame, "👥 Управление пользователями", self.manage_users)
            self.create_nav_btn(nav_frame, "📥 Импорт пользователей", self.import_users)
            
        # Spacer to push logout to bottom
        ttk.Frame(sidebar, style="Sidebar.TFrame").pack(fill=tk.BOTH, expand=True)
        
        self.create_nav_btn(sidebar, "🚪 Выйти", self.logout)
        
        # --- Content Area (Right) ---
        content = ttk.Frame(container, padding=30)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(content)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Управление заявками", style="Header.TLabel").pack(side=tk.LEFT)
        
        if self.user.role_name in ['Operator', 'Administrator']:
            ttk.Button(header_frame, text="+ Создать новую заявку", command=self.new_request, style="Create.TButton").pack(side=tk.RIGHT)
            
        # Filters
        filter_frame = ttk.Frame(content)
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status Filter
        ttk.Label(filter_frame, text="Фильтр по статусу", font=("Segoe UI", 9, "bold"), foreground="#6C757D").pack(anchor="w")
        self.status_filter = ttk.Combobox(filter_frame, values=["Все", "Новая", "Зарегистрирована", "В работе", "Выполнена", "Просрочена"], state="readonly", font=("Segoe UI", 10))
        self.status_filter.current(0)
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        self.status_filter.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        
        # Search
        ttk.Label(filter_frame, text="Поиск по номеру:", font=("Segoe UI", 9, "bold"), foreground="#6C757D").pack(anchor="w", pady=(10, 0))
        self.search_entry = ttk.Entry(filter_frame, font=("Segoe UI", 10))
        self.search_entry.pack(fill=tk.X, pady=(5, 0))
        self.search_entry.bind('<KeyRelease>', lambda e: self.load_data())
        
        # Request List Area (Scrollable)
        ttk.Label(content, text="Список заявок:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 10))
        
        self.canvas = tk.Canvas(content, bg="#F8F9FA", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=880) # Width adjustment needed on resize
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind resize to adjust inner frame width
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Mousewheel scrolling
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def create_nav_btn(self, parent, text, command):
        btn = ttk.Button(parent, text=text, command=command, style="Sidebar.TButton")
        btn.pack(fill=tk.X, padx=10, pady=2)

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def load_data(self):
        # Clear existing cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        status_map = {
            "Новая": STATUS_NEW,
            "Зарегистрирована": STATUS_REGISTERED,
            "В работе": STATUS_IN_PROGRESS,
            "Ожидание запчастей": STATUS_WAITING_PARTS,
            "Выполнена": STATUS_COMPLETED,
            "Просрочена": STATUS_OVERDUE
        }
        
        filter_val = self.status_filter.get()
        status_id = status_map.get(filter_val)
        
        requests = RequestService.get_requests(self.user.role_name, self.user.id, status_id)
        
        # Filter by Search
        search_query = self.search_entry.get().lower().strip()
        if search_query:
            requests = [r for r in requests if search_query in r.request_number.lower()]
            
        print(f"Loaded {len(requests)} requests")
        
        if not requests:
            ttk.Label(self.scrollable_frame, text="Заявок не найдено", font=("Segoe UI", 12), foreground="#6C757D").pack(pady=20)
            return
            
        for req in requests:
            self.create_request_card(req)

    def create_request_card(self, req):
        # Status Display Logic
        status_colors = {
            "New": "#DC3545",       # Red
            "Registered": "#0DCAF0",# Cyan
            "In Progress": "#FFC107",# Yellow
            "Waiting for Parts": "#FD7E14", # Orange
            "Completed": "#198754", # Green
            "Overdue": "#212529"    # Black
        }
        status_rus = {
            "New": "Новая заявка",
            "Registered": "Зарегистрирована",
            "In Progress": "В процессе ремонта",
            "Waiting for Parts": "Ожидание запчастей",
            "Completed": "Выполнена",
            "Overdue": "Просрочена"
        }
        
        color = status_colors.get(req.status_name, "#6C757D")
        display_status = status_rus.get(req.status_name, req.status_name)
        
        # Card Frame
        card = ttk.Frame(self.scrollable_frame, style="Card.TFrame", padding=20)
        card.pack(fill=tk.X, pady=10, padx=5)
        
        # Grid Layout for Card
        card.columnconfigure(1, weight=1)
        
        # Header Row: ID + Status Dot
        header_frame = ttk.Frame(card, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        id_lbl = ttk.Label(header_frame, text=f"REQ-{datetime.now().year}-{req.id:04d}", style="CardHeader.TLabel") # Mock ID format
        id_lbl.pack(side=tk.LEFT)
        
        # Status Dot
        dot = tk.Label(header_frame, text="●", fg=color, bg="#FFFFFF", font=("Arial", 16))
        dot.pack(side=tk.LEFT, padx=5)
        
        # Help Needed Badge
        if req.help_needed:
            help_lbl = tk.Label(header_frame, text=" SOS ", fg="white", bg="#DC3545", font=("Segoe UI", 8, "bold"))
            help_lbl.pack(side=tk.LEFT, padx=5)
        
        # Content Row
        content_frame = ttk.Frame(card, style="Card.TFrame")
        content_frame.pack(fill=tk.X)
        
        # Left Column (Client & Equipment)
        left_col = ttk.Frame(content_frame, style="Card.TFrame")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_col, text=f"👤 {req.client_name} | 📞 {req.client_phone}", style="Card.TLabel").pack(anchor="w", pady=2)
        ttk.Label(left_col, text=f"🔧 {req.equipment_model}", style="CardSub.TLabel").pack(anchor="w", pady=2)
        
        # Right Column (Status & Specialist & Date)
        right_col = ttk.Frame(content_frame, style="Card.TFrame")
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_col, text=f"Статус: {display_status}", style="Card.TLabel").pack(anchor="w", pady=2)
        
        spec_text = "Не назначен"
        if req.assigned_specialists:
            spec_text = ", ".join(req.assigned_specialists)
        ttk.Label(right_col, text=f"👨‍🔧 {spec_text}", style="CardSub.TLabel").pack(anchor="w", pady=2)
        
        ttk.Label(right_col, text=f"📅 {req.creation_date}", style="CardSub.TLabel").pack(anchor="w", pady=2)
        
        # Action Buttons Column
        action_col = ttk.Frame(content_frame, style="Card.TFrame")
        action_col.pack(side=tk.RIGHT)
        
        ttk.Button(action_col, text="👁️ Подробнее", style="Outline.TButton", command=lambda: self.open_details(req.id)).pack(pady=2, fill=tk.X)
        if self.user.role_name in ['Operator', 'Administrator', 'Manager']:
             ttk.Button(action_col, text="✏️ Редактировать", style="Outline.TButton", command=lambda: self.open_details(req.id)).pack(pady=2, fill=tk.X)

    def open_details(self, req_id):
        RequestDetailDialog(self, req_id, self.user)

    def logout(self):
        self.destroy()
        LoginWindow().mainloop()

    def new_request(self):
        NewRequestDialog(self)

    def show_statistics(self):
        stats = calculate_statistics()
        msg = f"Выполнено заявок: {stats['completed_count']}\n"
        msg += f"Среднее время ремонта: {stats['average_days']} дней\n\n"
        msg += "По типам неисправностей:\n"
        for problem, count in stats['problem_types'].items():
            msg += f"- {problem}: {count}\n"
        
        messagebox.showinfo("Статистика", msg)
        
    def manage_users(self):
        UserManagementDialog(self)
        
    def import_users(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filename:
            success, msg = ImportService.import_users_from_csv(filename)
            if success:
                messagebox.showinfo("Импорт", msg)
            else:
                messagebox.showerror("Ошибка импорта", msg)

class NewRequestDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Новая заявка")
        self.geometry("400x500")
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Новая заявка", style="Header.TLabel").pack(pady=(0, 20))
        
        ttk.Label(main_frame, text="Данные клиента", style="SubHeader.TLabel").pack(pady=(10, 5), anchor="w")
        
        ttk.Label(main_frame, text="Телефон:").pack(anchor="w")
        self.phone_entry = ttk.Entry(main_frame)
        self.phone_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(main_frame, text="ФИО:").pack(anchor="w")
        self.name_entry = ttk.Entry(main_frame)
        self.name_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(main_frame, text="Оборудование", style="SubHeader.TLabel").pack(pady=(15, 5), anchor="w")
        
        ttk.Label(main_frame, text="Серийный номер:").pack(anchor="w")
        self.serial_entry = ttk.Entry(main_frame)
        self.serial_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(main_frame, text="Модель:").pack(anchor="w")
        self.model_entry = ttk.Entry(main_frame)
        self.model_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(main_frame, text="Тип:").pack(anchor="w")
        self.type_entry = ttk.Entry(main_frame)
        self.type_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(main_frame, text="Описание проблемы:").pack(anchor="w", pady=(10, 0))
        self.problem_text = tk.Text(main_frame, height=5, width=40, font=("Segoe UI", 10))
        self.problem_text.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(main_frame, text="Создать", command=self.submit, style="TButton").pack(fill=tk.X)
        
    def submit(self):
        phone = self.phone_entry.get()
        name = self.name_entry.get()
        serial = self.serial_entry.get()
        model = self.model_entry.get()
        eq_type = self.type_entry.get()
        problem = self.problem_text.get("1.0", tk.END).strip()
        
        if not all([phone, name, serial, model, eq_type, problem]):
            messagebox.showerror("Ошибка", "Все поля обязательны")
            return
            
        req_num = RequestService.create_request((name, phone), (serial, model, eq_type), problem)
        if req_num:
            messagebox.showinfo("Успех", f"Заявка {req_num} создана!")
            self.parent.load_data()
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось создать заявку")

class RequestDetailDialog(tk.Toplevel):
    def __init__(self, parent, request_id, user):
        super().__init__(parent)
        self.parent = parent
        self.request_id = request_id
        self.user = user
        self.title(f"Детали заявки #{request_id}")
        self.geometry("600x600")
        
        self.load_request_data()
        self.create_widgets()
        
    def load_request_data(self):
        requests = RequestService.get_requests("Admin", self.user.id) # Admin sees all
        self.request = next((r for r in requests if str(r.id) == str(self.request_id)), None)
        
    def create_widgets(self):
        if not self.request:
            ttk.Label(self, text="Заявка не найдена").pack()
            return
            
        # Status Display Map
        status_display_map = {
            "New": "Новая",
            "Registered": "Зарегистрирована",
            "In Progress": "В работе",
            "Waiting for Parts": "Ожидание запчастей",
            "Completed": "Выполнена",
            "Overdue": "Просрочена"
        }
        display_status = status_display_map.get(self.request.status_name, self.request.status_name)

        # Main Frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Info Frame
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        grid_opts = {'padx': 5, 'pady': 2, 'sticky': 'w'}
        ttk.Label(info_frame, text=f"Номер: {self.request.request_number}").grid(row=0, column=0, **grid_opts)
        ttk.Label(info_frame, text=f"Статус: {display_status}").grid(row=0, column=1, **grid_opts)
        ttk.Label(info_frame, text=f"Клиент: {self.request.client_name}").grid(row=1, column=0, **grid_opts)
        ttk.Label(info_frame, text=f"Оборудование: {self.request.equipment_model}").grid(row=1, column=1, **grid_opts)
        ttk.Label(info_frame, text=f"Срок: {self.request.deadline_date}").grid(row=2, column=0, **grid_opts)
        
        if self.request.help_needed:
            ttk.Label(info_frame, text="⚠️ ТРЕБУЕТСЯ ПОМОЩЬ", foreground="red", font=("Segoe UI", 10, "bold")).grid(row=2, column=1, **grid_opts)

        ttk.Label(info_frame, text="Проблема:").grid(row=3, column=0, **grid_opts)
        ttk.Label(info_frame, text=self.request.problem_description, wraplength=400).grid(row=3, column=1, **grid_opts)
        
        ttk.Label(info_frame, text=f"Специалисты: {', '.join(self.request.assigned_specialists)}").grid(row=4, column=0, columnspan=2, **grid_opts)

        # Actions Frame
        action_frame = ttk.LabelFrame(main_frame, text="Действия", padding=10)
        action_frame.pack(fill=tk.X, pady=5)
        
        # Status Change (Specialist, Operator, Admin)
        if self.user.role_name in ['Specialist', 'Operator', 'Administrator']:
            ttk.Label(action_frame, text="Изменить статус:").pack(side=tk.LEFT)
            self.status_var = tk.StringVar(value=display_status)
            status_opts = ["В работе", "Ожидание запчастей", "Выполнена"]
            self.status_menu = ttk.OptionMenu(action_frame, self.status_var, status_opts[0], *status_opts, command=self.update_status)
            self.status_menu.pack(side=tk.LEFT, padx=5)

        # Help Request (Specialist)
        if self.user.role_name == 'Specialist':
             help_text = "Отменить запрос помощи" if self.request.help_needed else "Запросить помощь"
             ttk.Button(action_frame, text=help_text, command=self.toggle_help, style="Outline.TButton").pack(side=tk.LEFT, padx=5)

        # Assign Specialist (Manager, Quality Manager, Admin, Operator)
        if self.user.role_name in ['Manager', 'Quality Manager', 'Administrator', 'Operator']:
            ttk.Button(action_frame, text="Назначить спец.", command=self.assign_specialist_dialog, style="TButton").pack(side=tk.LEFT, padx=5)
            
        # Quality Manager Actions
        if self.user.role_name == 'Quality Manager':
            ttk.Button(action_frame, text="Продлить срок", command=self.extend_deadline_dialog, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
            if self.request.help_needed:
                ttk.Button(action_frame, text="Помощь оказана", command=lambda: self.toggle_help(force_off=True), style="TButton").pack(side=tk.LEFT, padx=5)
            
        # QR Code (Always visible for testing, typically for Completed)
        ttk.Button(action_frame, text="Показать QR-код", command=self.show_qr, style="TButton").pack(side=tk.LEFT, padx=5)

        # Parts Section
        parts_frame = ttk.LabelFrame(main_frame, text="Запчасти", padding=10)
        parts_frame.pack(fill=tk.X, pady=5)
        
        self.parts_list = tk.Listbox(parts_frame, height=3, font=("Segoe UI", 10), borderwidth=1, relief="solid")
        self.parts_list.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.load_parts()
        
        if self.user.role_name in ['Specialist', 'Administrator']:
            ttk.Button(parts_frame, text="+", command=self.add_part_dialog, width=3, style="TButton").pack(side=tk.LEFT, padx=5)

        # Comments Section
        comment_frame = ttk.LabelFrame(main_frame, text="Комментарии", padding=10)
        comment_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.comment_list = tk.Listbox(comment_frame, height=5, font=("Segoe UI", 10), borderwidth=1, relief="solid")
        self.comment_list.pack(fill=tk.BOTH, expand=True)
        self.load_comments()
        
        # Add Comment
        add_comment_frame = ttk.Frame(comment_frame)
        add_comment_frame.pack(fill=tk.X, pady=5)
        self.new_comment_entry = ttk.Entry(add_comment_frame)
        self.new_comment_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(add_comment_frame, text="Добавить", command=self.add_comment, style="TButton").pack(side=tk.LEFT, padx=(5, 0))

    def load_comments(self):
        self.comment_list.delete(0, tk.END)
        comments = RequestService.get_comments(self.request.id)
        for c in comments:
            self.comment_list.insert(tk.END, f"{c.created_at} - {c.user_name}: {c.text}")

    def load_parts(self):
        self.parts_list.delete(0, tk.END)
        parts = PartService.get_parts_for_request(self.request.id)
        for p in parts:
            self.parts_list.insert(tk.END, f"{p.name} (x{p.quantity_used}) - {p.price * p.quantity_used} руб.")

    def add_part_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Добавить запчасть")
        dialog.geometry("300x300")
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        all_parts = PartService.get_all_parts()
        
        ttk.Label(frame, text="Выберите запчасть:").pack(pady=(0, 5), anchor="w")
        part_var = tk.StringVar(dialog)
        
        part_map = {f"{p.name} (Остаток: {p.stock_quantity})": p.id for p in all_parts}
        if not part_map:
            ttk.Label(frame, text="Нет запчастей на складе").pack()
            return

        first_key = list(part_map.keys())[0]
        part_var.set(first_key)
        ttk.OptionMenu(frame, part_var, first_key, *part_map.keys()).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Количество:").pack(pady=(0, 5), anchor="w")
        qty_entry = ttk.Entry(frame)
        qty_entry.insert(0, "1")
        qty_entry.pack(fill=tk.X, pady=(0, 20))
        
        def do_add():
            p_id = part_map[part_var.get()]
            try:
                qty = int(qty_entry.get())
                if qty <= 0: raise ValueError
            except:
                messagebox.showerror("Ошибка", "Некорректное количество")
                return
                
            success, msg = PartService.assign_part_to_request(self.request.id, p_id, qty)
            if success:
                messagebox.showinfo("Успех", msg)
                self.load_parts()
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", msg)
                
        ttk.Button(frame, text="Добавить", command=do_add, style="TButton").pack(fill=tk.X)

    def add_comment(self):
        text = self.new_comment_entry.get()
        if text:
            RequestService.add_comment(self.request.id, self.user.id, text)
            self.new_comment_entry.delete(0, tk.END)
            self.load_comments()
            
    def update_status(self, new_status_name):
        status_map = {
            "Новая": STATUS_NEW,
            "Зарегистрирована": STATUS_REGISTERED,
            "В работе": STATUS_IN_PROGRESS,
            "Ожидание запчастей": STATUS_WAITING_PARTS,
            "Выполнена": STATUS_COMPLETED,
            "Просрочена": STATUS_OVERDUE
        }
        new_id = status_map.get(new_status_name)
        if new_id:
            RequestService.update_status(self.request.id, new_id)
            messagebox.showinfo("Успех", "Статус обновлен")
            self.parent.load_data()
            self.destroy() # Close to refresh or reload data
            
    def assign_specialist_dialog(self):
        specs = UserService.get_specialists() # Returns list of (id, name)
        if not specs:
            messagebox.showwarning("Внимание", "Специалисты не найдены")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Назначить специалиста")
        dialog.geometry("300x400")
        
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        lb = tk.Listbox(frame, font=("Segoe UI", 10), borderwidth=1, relief="solid")
        lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for s in specs:
            lb.insert(tk.END, f"{s[0]} - {s[1]}")
            
        def do_assign():
            sel = lb.curselection()
            if sel:
                spec_str = lb.get(sel[0])
                spec_id = int(spec_str.split(' - ')[0])
                RequestService.assign_specialist(self.request.id, spec_id)
                messagebox.showinfo("Успех", "Специалист назначен")
                self.parent.load_data()
                dialog.destroy()
                
        ttk.Button(frame, text="Назначить", command=do_assign, style="TButton").pack(fill=tk.X, pady=5)

    def extend_deadline_dialog(self):
        days = simpledialog.askinteger("Продлить срок", "Введите количество дней:")
        if days:
            RequestService.extend_deadline(self.request.id, days)
            messagebox.showinfo("Успех", "Срок продлен")
            self.parent.load_data()
            self.destroy()

    def toggle_help(self, force_off=False):
        new_state = False if force_off else not self.request.help_needed
        
        if RequestService.toggle_help_needed(self.request.id, new_state):
            msg = "Помощь запрошена" if new_state else "Запрос помощи отменен"
            if force_off: msg = "Помощь отмечена как оказанная"
            messagebox.showinfo("Успех", msg)
            self.parent.load_data()
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось изменить статус помощи")

    def show_qr(self):
        data = f"{FEEDBACK_URL}?request_id={self.request.request_number}"
        
        if not HAS_PIL:
            messagebox.showwarning("Внимание", "Библиотека PIL (Pillow) не установлена. QR-код не может быть отображен.")
            return

        try:
            # Local generation using qrcode library
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to PhotoImage
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)
            
            image = Image.open(bio)
            photo = ImageTk.PhotoImage(image)
            
            qr_win = tk.Toplevel(self)
            qr_win.title("QR-код для отзыва")
            qr_win.geometry("350x400")
            
            frame = ttk.Frame(qr_win, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            lbl = ttk.Label(frame, image=photo)
            lbl.image = photo
            lbl.pack(padx=10, pady=10)
            
            ttk.Label(frame, text=f"Заявка: {self.request.request_number}", font=("Segoe UI", 10, "bold")).pack(pady=(5,0))
            ttk.Label(frame, text="Отсканируйте для отзыва", foreground="#6C757D").pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сгенерировать QR: {e}")

class UserManagementDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Управление пользователями")
        self.geometry("600x500")
        self.configure(bg="#F8F9FA")
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text="Сотрудники", style="Header.TLabel").pack(anchor="w", pady=(0, 20))
        
        # Table Frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Treeview
        columns = ("login", "name", "role")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("login", text="Логин")
        self.tree.heading("name", text="ФИО")
        self.tree.heading("role", text="Роль")
        
        self.tree.column("login", width=100)
        self.tree.column("name", width=200)
        self.tree.column("role", width=150)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.load_users()
        
        ttk.Button(main_frame, text="+ Добавить пользователя", command=self.add_user_dialog, style="Create.TButton").pack(anchor="e")
        
    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        users = UserService.get_all_users()
        for u in users:
            self.tree.insert("", tk.END, values=(u.username, u.full_name, u.role_name))
            
    def add_user_dialog(self):
        d = tk.Toplevel(self)
        d.title("Добавить пользователя")
        d.geometry("400x500")
        d.configure(bg="#F8F9FA")
        
        frame = ttk.Frame(d, padding=30)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Новый сотрудник", style="Header.TLabel").pack(pady=(0, 20))
        
        ttk.Label(frame, text="Логин:").pack(anchor="w")
        u_entry = ttk.Entry(frame)
        u_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Пароль:").pack(anchor="w")
        p_entry = ttk.Entry(frame, show="*")
        p_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="ФИО:").pack(anchor="w")
        n_entry = ttk.Entry(frame)
        n_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Роль:").pack(anchor="w")
        role_var = tk.StringVar(value="Operator")
        roles = ["Administrator", "Operator", "Specialist", "Manager", "Quality Manager"]
        
        role_menu = ttk.OptionMenu(frame, role_var, roles[1], *roles)
        role_menu.pack(fill=tk.X, pady=(0, 30))
        
        def submit():
            role_map = {
                "Administrator": 1, "Operator": 2, "Specialist": 3,
                "Manager": 4, "Quality Manager": 5
            }
            if not all([u_entry.get(), p_entry.get(), n_entry.get()]):
                 messagebox.showerror("Ошибка", "Заполните все поля")
                 return

            if UserService.create_user(u_entry.get(), p_entry.get(), n_entry.get(), role_map[role_var.get()]):
                messagebox.showinfo("Успех", "Пользователь добавлен")
                self.load_users()
                d.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось (возможно, логин занят)")
                
        ttk.Button(frame, text="Создать", command=submit, style="TButton").pack(fill=tk.X)

if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
