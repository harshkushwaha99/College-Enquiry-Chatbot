import sqlite3


def create_database():

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # =========================
    # USERS / STUDENTS TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)


    # =========================
    # ADMIN TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)


    # =========================
    # CHATBOT DATA TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chatbot_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)


    # =========================
    # SUGGESTIONS TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            user_email TEXT,
            message TEXT NOT NULL
        )
    """)


    # =========================
    # COURSES TABLE
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            duration TEXT,
            fees TEXT,
            description TEXT
        )
    """)


    # =========================
    # DEFAULT ADMIN
    # =========================

    cursor.execute("""
        INSERT OR IGNORE INTO admins (username, password)
        VALUES (?, ?)
    """, ("admin", "admin123"))


    connection.commit()
    connection.close()

    print("Database created successfully!")
    print("Default Admin Username: admin")
    print("Default Admin Password: admin123")


if __name__ == "__main__":
    create_database()