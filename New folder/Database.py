import sqlite3

conn = sqlite3.connect("trekking.db")
cur = conn.cursor()

# Enable foreign key support
cur.execute("PRAGMA foreign_keys = ON")

cur.execute("""
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
""")

cur.execute("""
INSERT OR IGNORE INTO admins(id, username, password)
VALUES (1, 'admin', 'admin123');
""")

# Users Table
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT,
    gender TEXT,
    status TEXT DEFAULT 'active'
);
""")

# Staff Table
cur.execute("""
CREATE TABLE IF NOT EXISTS staff(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT,
    gender TEXT,
    experience INTEGER,
    status TEXT DEFAULT 'pending'
);
""")

# Treks Table
cur.execute("""
CREATE TABLE IF NOT EXISTS treks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    cost INTEGER NOT NULL,
    available_slots INTEGER NOT NULL,
    assigned_staff_id INTEGER,
    status TEXT DEFAULT 'open',
    start_date TEXT,
    end_date TEXT,
    description TEXT,
    FOREIGN KEY (assigned_staff_id) REFERENCES staff(id)
);
""")

# Bookings Table
cur.execute("""
CREATE TABLE IF NOT EXISTS bookings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    trek_id INTEGER NOT NULL,
    booking_date TEXT NOT NULL,
    status TEXT DEFAULT 'booked',
    payment_status TEXT DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (trek_id) REFERENCES treks(id)
);
""")

conn.commit()
conn.close()

print("Database created successfully.")