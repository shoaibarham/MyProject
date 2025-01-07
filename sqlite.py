import sqlite3
import os

# Verify the current working directory
print(f"Current working directory: {os.getcwd()}")

# SQLite connection (creates student.db in the current directory)
connection = sqlite3.connect("student.db")

# Create a cursor object to execute SQL queries
cursor = connection.cursor()
# Create the STUDENT table
table_info = """CREATE TABLE STUDENT(
    NAME VARCHAR(25), 
    CLASS VARCHAR(25), 
    SECTION VARCHAR(25), 
    MARKS INT
)"""
cursor.execute(table_info)

# Insert records into the STUDENT table
records = [
    ('Alice', 'Data Science', 'A', 95),
    ('Bob', 'Machine Learning', 'B', 88),
    ('Charlie', 'AI', 'A', 92),
    ('Diana', 'Cloud Computing', 'B', 77),
    ('Eve', 'Cybersecurity', 'C', 68),
    ('Frank', 'Big Data', 'A', 84),
    ('Grace', 'Web Development', 'B', 72),
    ('Hank', 'UI/UX Design', 'A', 89),
    ('Ivy', 'Blockchain', 'A', 91),
    ('Jack', 'Robotics', 'B', 65),
    ('Kim', 'IoT', 'C', 75),
    ('Liam', 'Game Development', 'A', 96),
    ('Mia', 'Data Engineering', 'A', 87),
    ('Noah', 'DevOps', 'C', 58),
    ('Olivia', 'Software Testing', 'B', 80),
    ('Paul', 'Mobile App Development', 'A', 73),
    ('Quinn', 'Natural Language Processing', 'A', 85),
    ('Rose', 'Artificial Intelligence', 'A', 90),
    ('Steve', 'Ethical Hacking', 'B', 78),
]
cursor.executemany('INSERT INTO STUDENT VALUES (?, ?, ?, ?)', records)

# Display all the records
print("The inserted records are:")
data = cursor.execute('SELECT * FROM STUDENT')
for row in data:
    print(row)

# Commit changes and close the database connection
connection.commit()
connection.close()

print("Database created successfully in the current folder.")