"""
Импорт CSV в БД SQLite в ПРАВИЛЬНОМ порядке:
1) clients.csv → clients
2) specialists.csv → specialists
3) requests.csv → НЕ напрямую (через staging requests_import)
4) comments.csv → comments (через staging comments_import)
5) users.csv → users

В текущем учебном датасете файлы лежат так:
- Кондиционеры_данные/Пользователи/inputDataUsers.csv
- Кондиционеры_данные/Заявки/inputDataRequests.csv
- Кондиционеры_данные/Комментарии/inputDataComments.csv

Важно:
- таблица requests хранит ссылки client_id и assigned_specialist_id (а не ФИО)
- в CSV заявок у нас есть clientID и masterID (внешние ключи), их нужно корректно переложить
"""

import csv
import sqlite3
from pathlib import Path

from models import create_tables
from database import get_connection


DATA_DIR = Path("Кондиционеры_данные")
USERS_CSV = DATA_DIR / "Пользователи" / "inputDataUsers.csv"
REQUESTS_CSV = DATA_DIR / "Заявки" / "inputDataRequests.csv"
COMMENTS_CSV = DATA_DIR / "Комментарии" / "inputDataComments.csv"

# Если True — импорт работает как “полная загрузка”: очищает таблицы и загружает заново.
# Это делает скрипт идемпотентным (повторный запуск не создаёт дубликаты).
FULL_RELOAD = True


def _norm_null(value):
    if value is None:
        return None
    v = str(value).strip()
    if v == "" or v.lower() == "null":
        return None
    return v


def _ensure_staging_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # staging для заявок (1 в 1 повторяет CSV inputDataRequests.csv)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests_import (
            requestID TEXT,
            startDate TEXT,
            climateTechType TEXT,
            climateTechModel TEXT,
            problemDescryption TEXT,
            requestStatus TEXT,
            completionDate TEXT,
            repairParts TEXT,
            masterID TEXT,
            clientID TEXT
        )
    """)
    # staging для комментариев (1 в 1 повторяет CSV inputDataComments.csv)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments_import (
            commentID TEXT,
            message TEXT,
            masterID TEXT,
            requestID TEXT
        )
    """)
    conn.commit()


def _truncate_staging(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM requests_import")
    cur.execute("DELETE FROM comments_import")
    conn.commit()


def _truncate_targets(conn: sqlite3.Connection) -> None:
    """Очищает целевые таблицы и сбрасывает автоинкремент (SQLite)."""
    cur = conn.cursor()
    # Порядок удаления: сначала зависимые таблицы
    cur.execute("DELETE FROM comments")
    cur.execute("DELETE FROM requests")
    cur.execute("DELETE FROM clients")
    cur.execute("DELETE FROM specialists")
    cur.execute("DELETE FROM users")

    # Сбрасываем счётчики AUTOINCREMENT, если таблица sqlite_sequence существует
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    if cur.fetchone():
        cur.execute(
            "DELETE FROM sqlite_sequence WHERE name IN ('comments','requests','clients','specialists','users')"
        )

    conn.commit()


def import_users_clients_specialists(conn: sqlite3.Connection, users_csv: Path) -> None:
    """
    Шаг clients → specialists делаем на основании inputDataUsers.csv:
    - type == 'Заказчик'   → clients (id = userID для совпадения с clientID в заявках)
    - type == 'Специалист' → specialists (id = userID для совпадения с masterID в заявках)

    Важно: users (логины) импортируем ПОСЛЕ comments, согласно требуемому порядку.
    """
    cur = conn.cursor()
    with users_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            user_id = _norm_null(row.get("userID"))
            fio = _norm_null(row.get("fio"))
            phone = _norm_null(row.get("phone"))
            user_type = _norm_null(row.get("type"))

            if not user_id or not fio:
                continue

            if user_type == "Заказчик":
                cur.execute(
                    "INSERT OR IGNORE INTO clients (id, full_name, phone) VALUES (?, ?, ?)",
                    (int(user_id), fio, phone or ""),
                )
            elif user_type == "Специалист":
                cur.execute(
                    "INSERT OR IGNORE INTO specialists (id, full_name, specialization) VALUES (?, ?, ?)",
                    (int(user_id), fio, None),
                )

    conn.commit()


def import_requests_via_staging(conn: sqlite3.Connection, requests_csv: Path) -> None:
    """
    Импорт requests.csv НЕ напрямую:
    1) грузим CSV в requests_import
    2) переносим в requests, заполняя client_id и assigned_specialist_id
    """
    cur = conn.cursor()

    # 1) CSV → staging
    with requests_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            cur.execute(
                """
                INSERT INTO requests_import (
                    requestID, startDate, climateTechType, climateTechModel,
                    problemDescryption, requestStatus, completionDate, repairParts,
                    masterID, clientID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _norm_null(row.get("requestID")),
                    _norm_null(row.get("startDate")),
                    _norm_null(row.get("climateTechType")),
                    _norm_null(row.get("climateTechModel")),
                    _norm_null(row.get("problemDescryption")),
                    _norm_null(row.get("requestStatus")),
                    _norm_null(row.get("completionDate")),
                    _norm_null(row.get("repairParts")),
                    _norm_null(row.get("masterID")),
                    _norm_null(row.get("clientID")),
                ),
            )

    # 2) staging → requests
    # В базе может быть либо specialist_id (старый вариант), либо assigned_specialist_id (новый вариант).
    cur.execute("PRAGMA table_info(requests)")
    cols = {row[1] for row in cur.fetchall()}
    specialist_col = "assigned_specialist_id" if "assigned_specialist_id" in cols else "specialist_id"

    insert_sql = f"""
        INSERT OR IGNORE INTO requests (
            request_number,
            created_date,
            equipment_type,
            equipment_model,
            problem_description,
            status,
            client_id,
            {specialist_col},
            start_repair_date,
            end_repair_date
        )
        SELECT
            r.requestID,
            r.startDate,
            r.climateTechType,
            r.climateTechModel,
            r.problemDescryption,
            r.requestStatus,
            CAST(r.clientID AS INTEGER),
            CASE
                WHEN lower(r.masterID) = 'null' OR r.masterID IS NULL OR r.masterID = '' THEN NULL
                ELSE CAST(r.masterID AS INTEGER)
            END,
            NULL,
            CASE
                WHEN lower(r.completionDate) = 'null' OR r.completionDate IS NULL OR r.completionDate = '' THEN NULL
                ELSE r.completionDate
            END
        FROM requests_import r
    """
    cur.execute(insert_sql)

    conn.commit()


def import_comments_via_staging(conn: sqlite3.Connection, comments_csv: Path) -> None:
    """
    comments.csv → НЕ напрямую:
    - грузим в comments_import
    - переносим в comments через JOIN на requests по request_number=requestID
    """
    cur = conn.cursor()

    with comments_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            cur.execute(
                """
                INSERT INTO comments_import (commentID, message, masterID, requestID)
                VALUES (?, ?, ?, ?)
                """,
                (
                    _norm_null(row.get("commentID")),
                    _norm_null(row.get("message")),
                    _norm_null(row.get("masterID")),
                    _norm_null(row.get("requestID")),
                ),
            )

    # переносим в comments (created_at возьмём текущей датой/временем, т.к. в CSV нет)
    cur.execute(
        """
        INSERT INTO comments (request_id, comment_text, created_at)
        SELECT
            r.id,
            ci.message,
            datetime('now')
        FROM comments_import ci
        JOIN requests r
            ON r.request_number = ci.requestID
        """
    )

    conn.commit()


def import_users(conn: sqlite3.Connection, users_csv: Path) -> None:
    """
    users.csv → users (в конце, согласно требуемому порядку).

    Маппинг type → role (под текущие роли системы):
    - Менеджер   → admin
    - Оператор   → operator
    - Специалист → specialist
    - Заказчик   → НЕ импортируем в users (это клиент, а не аккаунт системы)
    """
    cur = conn.cursor()

    type_to_role = {
        "Менеджер": "admin",
        "Оператор": "operator",
        "Специалист": "specialist",
    }

    with users_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            login = _norm_null(row.get("login"))
            password = _norm_null(row.get("password"))
            user_type = _norm_null(row.get("type"))
            role = type_to_role.get(user_type)

            if not role or not login or not password:
                continue

            cur.execute(
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                (login, password, role),
            )

    conn.commit()


def run_import() -> None:
    create_tables()
    conn = get_connection()
    try:
        _ensure_staging_tables(conn)
        _truncate_staging(conn)
        if FULL_RELOAD:
            _truncate_targets(conn)

        # ВАЖНО: порядок строго такой
        import_users_clients_specialists(conn, USERS_CSV)  # clients → specialists
        import_requests_via_staging(conn, REQUESTS_CSV)    # requests (через staging)
        import_comments_via_staging(conn, COMMENTS_CSV)    # comments (через staging)
        import_users(conn, USERS_CSV)                      # users (в конце)

    finally:
        conn.close()

    print("Импорт завершён: clients -> specialists -> requests(via staging) -> comments -> users")


if __name__ == "__main__":
    run_import()
