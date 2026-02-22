import sqlite3

# Подключаемся к файлу базы (если нет — создастся users.db)
conn = sqlite3.connect("users.db", check_same_thread=False)

# Cursor — "рука", чтобы работать с базой
cursor = conn.cursor()

# Создаем таблицу пользователей, если еще нет
cursor.execute('''
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    goal TEXT,
    streak INTEGER,
    last_check TEXT
)
''')

# Сохраняем изменения
conn.commit()

# Функция для добавления нового пользователя
def add_user(user_id, goal):
    cursor.execute(
        "INSERT OR IGNORE INTO users(user_id, streak, last_check, goal) VALUES (?, ?, ?, ?)",
        (user_id, 0, "", goal)
    )
    conn.commit()

# Функция для обновления streak
from datetime import date

def update_streak(user_id, done_today):
    cursor.execute("SELECT streak, last_check FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row:
        streak, last_check = row
        if done_today:
            # Если задача выполнена и последний отчет не сегодня
            if last_check != str(date.today()):
                streak += 1
                cursor.execute(
                    "UPDATE users SET streak=?, last_check=? WHERE user_id=?",
                    (streak, str(date.today()), user_id)
                )
        else:
            # Если пользователь пропустил день
            streak = max(0, streak - 2)
            cursor.execute(
                "UPDATE users SET streak=? WHERE user_id=?",
                (streak, user_id)
            )
        cursor.execute(
            "INSERT INTO history(user_id, date, done) VALUES (?, ?, ?)",
            (user_id, str(date.today()), int(done_today))
            )
        conn.commit()
        
def get_top_users(limit = 10):
    cursor.execute("SELECT user_id, streak FROM users ORDER BY streak DESC LIMIT ?", (limit,))
    return cursor.fetchall()

cursor.execute('''CREATE TABLE IF NOT EXISTS history(user_id INTEGER, date TEXT, done INTEGER)''')
conn.commit()

from datetime import timedelta

def get_week_stats(user_id):
    today = date.today()
    week_ago = today - timedelta(days=7)

    cursor.execute(
        """SELECT COUNT(*) FROM history
           WHERE user_id=? AND done=1 AND date>=?""",
        (user_id, str(week_ago))
    )

    done_days = cursor.fetchone()[0]
    return done_days

def get_user_info(user_id):
    cursor.execute(
        "SELECT goal, streak FROM user WHERE user_id=?", (user_id)
    )
    return cursor.fetchone()

def get_user_rank(user_id):
    cursor.execute("""
        SELECT COUNT(*) + 1
        FROM users
        WHERE streak > (
            SELECT streak FROM users WHERE user_id=?
        )
    """, (user_id,))

    return cursor.fetchone()[0]

def get_last_days(user_id, limit=7):
    cursor.execute("""
        SELECT date, done
        FROM history
        WHERE user_id=?
        ORDER BY date DESC
        LIMIT ?
    """, (user_id, limit))

    return cursor.fetchall()