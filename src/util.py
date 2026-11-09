import random
import sqlite3
from crypto import hashSha, hashBcr
import pyotp
import secrets

# This file is purely utility and not part of the main logic

def registerPerson():
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    Id = input("ID: ")
    Id = int(Id)
    firstName = input("First name: ")
    lastName = input("Last name: ")
    cpr = input("CPR: ")
    cpr = hashSha(cpr)
    eligible = input("Eligible?: ")
    eligible = int(eligible)
    password = input("Password: ")
    password = hashBcr(password,None)
    password = password.decode()

    hasRegistered = input("Has registered?: ")
    hasRegistered = int(hasRegistered)
    otp = pyotp.random_base32()
    

    cursor.execute("""INSERT INTO Voters (voter_id,first_name,last_name,cpr_hash,eligible,password_hash,has_registered,otp) VALUES (?,?,?,?,?,?,?,?);""",(Id,firstName,lastName,cpr,eligible,password,hasRegistered,otp,))
    conn.commit()
    conn.close()


first_names = [
    "Nicolaj", "Mohammed", "Alice", "Anna", "Bob", "Askepot", "Ariel", "Baloo", 
    "Bambi", "Boo", "Bell", "Quandale", "Dolly", "Dumble", "Darling", "Elsa", 
    "Theodor", "Annika", "Esmarelda", "Gamma", "Hades", "Hercules", "Hades", 
    "Jafar", "David", "Carl", "Joe", "Peter", "Quagmire", "Klokkeblomst", 
    "Kala", "Lady", "Nikolaj", "Nicolai", "Nikolai", "Simba", "Windy", "Max", 
    "Merlin", "Mowgli", "Nala", "O'malley", "Olaf", "Pluto", "Pongo", "Pumba", 
    "Quasimodo", "Robin", "Mauga", "Biggus", "Benjamin",
    
    "Søren", "Mads", "Freja", "Astrid", "Valdemar", "Holger", "Bente", "Egon", 
    "Benny", "Kjeld", "Yvonne", "Kasper", "Lærke", "Torben", "Jørgen", "Børge", 
    "Viggo", "Ingrid", "Signe", "Rasmus", "Flemming", "Uffe",

    "Shrek", "Goku", "Doomfist", "Geralt", "Kratos", "SpongeBob", "Squidward", 
    "Walter", "Jesse", "Saul", "Gandalf", "Frodo", "Anakin", "Obi-Wan", 
    "Waluigi", "Wario", "Trevor", "GLaDOS", "Cortana", "Morbius", "Johnny", 
    "Arthur", "Solid", "Master", "Leeroy", "Kermit", "Boba", "Sheev", "Hugh", 
    "Ben", "Mike", "Seymour", "Freddy",

    "Emily", "Jack", "Sarah", "Connor", "Chloe", "Ethan", "Liam", "Olivia", 
    "Noah", "Grace", "Lucas", "Mason", "Zoe", "Hannah", "Nathan", "Caleb", 
    "Chloe", "Wyatt", "Victoria", "Samuel"
]

last_names = [
    "Nielsen", "Jensen", "Dingle", "Andersen", "Pedersen", "Lurger", "Alan", 
    "Koyuncu", "Khan", "Lurger", "Brunn", "Von Schnitzel", "Adams", "Jakobsen", 
    "Nagahavi", "Macdonald", "Olsen", "Jabba", "Dickus", "Gustaf", "Zeta", 
    "Harker",

    "Hansen", "Møller", "Christensen", "Larsen", "Sørensen", "Rasmussen", 
    "Jørgensen", "Petersen", "Madsen", "Kristensen", "Thomsen", "Poulsen", 
    "Johansen", "Knudsen", "Mortensen", "Vestergaard", "Lindberg", "Østergaard", 
    "Kjær", "Skov", "Nørgaard", "Dahl", "Kragh",

    "Baggins", "Skywalker", "Kenobi", "White", "Pinkman", "Goodman", "Freeman", 
    "Auditore", "Croft", "of Rivia", "SquarePants", "Tentacles", "Fazbear", 
    "Griffin", "Simpson", "Sanchez", "Flanders", "Doofenshmirtz", "Silverhand", 
    "Smasher", "Morgan", "Snake", "Chief", "Jenkins", "Fett", "Palpatine", 
    "Mungus", "Dover", "Oxlong", "Butts", "Chungus", "McLovin",

    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", 
    "Wilson", "Taylor", "Clark", "Hall", "Young", "King", "Wright", "Baker", 
    "Carter", "Mitchell", "Turner", "Collins", "Steele"
]

def makePeople(amount):
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()
    first_names_len = len(first_names) - 1
    last_names_len = len(last_names) - 1

    for i in range(amount):
        print(f"Making person {i}")
        s = secrets.token_hex(16)
        random.seed(s)

        print(s)
        
        n = random.randint(0,first_names_len)
        first_name = first_names[n]

        n = random.randint(0,last_names_len)
        last_name = last_names[n]

        d = str(random.randint(101,131))
        m = str(random.randint(101,112))
        y = random.randint(1950,2026)

        if y <= 2007:
            eligible = 1
        else:
            eligible = 0

        y = str(y)

        cpr = d[1:] + m[1:] + y[2:] + str(random.randint(1001,9999))
        cpr = hashSha(cpr)

        print(cpr)

        has_registered = random.randint(0,1)
        password = first_name + y + "!"
        password = hashBcr(password,None)
        password = password.decode()
        
        if has_registered == 0:
            otp = None
        else: 
            otp = pyotp.random_base32()
            
        cursor.execute("""INSERT INTO Voters (first_name,last_name,cpr_hash,eligible,password_hash,has_registered,otp,has_voted) VALUES (?,?,?,?,?,?,?,0);""",(first_name,last_name,cpr,eligible,password,has_registered,otp,))
        cursor.execute("""INSERT INTO seeds (seed,VoterID) VALUES (?,(SELECT last_insert_rowid() FROM Voters))""",(s,))   
        

    conn.commit()
    conn.close()

def lookupSeed(id):
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    cursor.execute("""SELECT seed FROM seeds WHERE VoterID = ?""",(id,))
    s = cursor.fetchone()[0]

    print(f"Seed: {s}")
    
    first_names_len = len(first_names) - 1
    last_names_len = len(last_names) - 1

    random.seed(s)
    
    n = random.randint(0,first_names_len)
    first_name = first_names[n]

    n = random.randint(0,last_names_len)
    last_name = last_names[n]

    d = str(random.randint(101,131))
    m = str(random.randint(101,112))
    y = random.randint(1950,2026)
    y = str(y)

    cpr = d[1:] + m[1:] + y[2:] + str(random.randint(1001,9999))

    password = first_name + y + "!"

    print(f"CPR: {cpr}")
    print(f"CPR HASH: {hashSha(cpr)}")
    print(f"Password: {password}")



registerPerson()