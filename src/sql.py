import sqlite3

conn = sqlite3.connect("voting.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS Parties (
party_id INTEGER PRIMARY KEY,
party_name TEXT NOT NULL,
abbreviation TEXT NOT NULL
)
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Candidates (
Candidate_id INTEGER PRIMARY KEY,
party_id TEXT NOT NULL, 
Candidate_name TEXT NOT NULL,
CONSTRAINT fk_Party
FOREIGN KEY(party_id)
REFERENCES Parties(party_id)
)
""")

cursor.execute("""CREATE TABLE Voters (
    voter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    cpr_hash CHAR(32) UNIQUE NOT NULL,
    eligible BOOLEAN NOT NULL,
    password_hash VARCHAR(60) NOT NULL UNIQUE,
    has_registered BOOLEAN NOT NULL DEFAULT 0,
    OTP CHAR(32) UNIQUE
)""")

def party_count():
    cursor.execute("""SELECT COUNT(party_id) FROM Parties""")

    for i in cursor:
        print(i[0])

cursor.execute("""SELECT party_name FROM Parties""")

cursor.execute("""DROP VIEW IF EXISTS PARTIES_VIEW;""")
cursor.execute("""DROP VIEW IF EXISTS CANDIDATES_VIEW;""")
cursor.execute("""CREATE VIEW PARTIES_VIEW AS SELECT PARTY_NAME, ABBREVIATION FROM Parties;""")
cursor.execute("""CREATE VIEW CANDIDATES_VIEW AS SELECT Candidate_name,Party_id FROM Candidates;""")
cursor.execute("""SELECT * FROM PARTIES_VIEW""")
parties=[]

for i in cursor:
        print(i)
        parties.append(i)

print(parties)


conn.commit()
conn.close()