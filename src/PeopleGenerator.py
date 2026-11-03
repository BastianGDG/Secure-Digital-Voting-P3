## LAV FOLK
import random
import sqlite3
from crypto import hashSha, hashBcr
import pyotp


voter = ["FirstName", "LastName", "PseudoCPR", "VoterID"]

## LAV FUNKTION, SOM GENERERER LISTER OVER VOTERS

## LAV ET INPUT-FELT, SOM MODTAGER, HVOR MANGE VOTERS, DER SKAL GENERERES

## LAV ET LOOP, SOM GENERERER DE FORSKELLIGE VÆRDIER FOR EN LISTE (VOTER)

## REPEAT LOOP DET ANTAL GANGE, SOM DER ER REQUESTED VOTERS

## RETURNÉR ALLE LISTER TIL DATABASEN

def makePeople():
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
    hasRegistered = input("Has registered?: ")
    hasRegistered = int(hasRegistered)
    otp = pyotp.random_base32()
    

    cursor.execute("""INSERT INTO Voters (voter_id,first_name,last_name,cpr_hash,eligible,password_hash,has_registered,otp) VALUES (?,?,?,?,?,?,?,?);""",(Id,firstName,lastName,cpr,eligible,password,hasRegistered,otp,))
    conn.commit()
    conn.close()

makePeople()