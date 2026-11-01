from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)

conn = sqlite3.connect("voting.db")
cursor = conn.cursor()

cursor.execute("""SELECT * FROM PARTIES_VIEW""")

temp = []

for i in cursor:
    party = i[0] + " (" + i[1] + ")"
    temp.append(party)

parties={}

cursor.execute("""SELECT * FROM CANDIDATES_VIEW""")

for n in range(len(temp)):
    cand = []
    cursor.execute(f"""SELECT CANDIDATE_NAME FROM CANDIDATES_VIEW WHERE PARTY_ID = {n+1}""")
    for i in cursor:
         cand.append(i[0])
    parties[temp[n]] = cand

print(parties)

@app.get("/")
def index():

    return render_template(
        "index.html",
    )

@app.get("/login")
def loginscreen():

    return render_template(
        "Login.html",
    )

@app.get("/candidates")
def test():

    return render_template(
        "test.html",
        parties=parties
    )

@app.post("/login")
def login():
    cpr = request.form["CPR"]
    print(f"cpr: {cpr}")
    passwrd = request.form["Password"]
    print(f"password: {passwrd}")
    if cpr == "12345" and passwrd == "login":
        return render_template(
                "test.html",
                parties=parties
            )
    else:
        return render_template(
                "invalid.html",
            )
    

@app.post("/vote")
def vote():
    try:
        candidate = request.form["candidate"]
        print(f"Vote received for {candidate}")
        app.logger.debug('A value for debugging')
        return render_template(
                "confirmation.html",
                vote=candidate
            )
        #return {"status": "success", "candidate": candidate}
    except:
        party = request.form["party"]
        print(f"Vote received for {party}")
        app.logger.debug('A value for debugging')
        return render_template(
                "confirmation.html",
                vote=party
            )
        #return {"status": "success", "party": party}

app.run(
    host="0.0.0.0",
    port=5000,
    debug=True
)

cursor.execute("""DROP VIEW PARTIES_VIEW;""")

conn.commit()
conn.close()