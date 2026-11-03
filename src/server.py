from flask import Flask, request, render_template, redirect, url_for, make_response
import sqlite3
import pyotp
from crypto import hashBcr, hashSha
import secrets

# ---- Setup ------

app = Flask(__name__)

# ----- Setup ------

def getCandidates():
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    cursor.execute("""SELECT * FROM PARTIES_VIEW;""")

    temp = []

    for i in cursor:
        party = i[0] + " (" + i[1] + ")"
        temp.append(party)

    parties={}

    cursor.execute("""SELECT * FROM CANDIDATES_VIEW;""")

    for n in range(len(temp)):
        cand = []
        cursor.execute(f"""SELECT CANDIDATE_NAME FROM CANDIDATES_VIEW WHERE PARTY_ID = {n+1};""")
        for i in cursor:
            cand.append(i[0])
        parties[temp[n]] = cand

    return parties

def updateToken(result,response):
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()
    token = secrets.token_urlsafe(32)
    cursor.execute("""UPDATE Sessions SET session_token = ? WHERE voter_id = ?;""", (token,result,))
    conn.commit()

    response = response

    response.set_cookie(
            "session_token",
            token,
             httponly=True,
            #secure=True,
            samesite="Lax"
             )
    
    return response

@app.route("/",methods=['GET'])
def main():
    return render_template(
            "index.html"
            )


@app.route("/login",methods=['GET','POST'])
def handle_method():
    if request.method == 'GET': 
        return render_template(
        "login.html"
        )

    elif request.method == 'POST':
        with sqlite3.connect("voting.db") as conn:
            cursor = conn.cursor()

            cpr_hash = request.form["CPR"]
            password = request.form["Password"]

            cpr_hash = hashSha(cpr_hash)

            cursor.execute("""SELECT password_hash FROM Voters_view WHERE (CPR_HASH = ? AND ELIGIBLE = TRUE) LIMIT 1;""",(cpr_hash,))
            password_user = cursor.fetchone()

            if password_user == None:
                return {"Status": "Acess denied", "Error": "500"}

            password_user = password_user[0]    

            salt = password_user[:29]

            password_input = (hashBcr(password,salt.encode('utf-8')))
            password_input = password_input.decode()

            cursor.execute("""SELECT Voter_id FROM Voters_view WHERE (CPR_HASH = ? AND PASSWORD_HASH = ? AND ELIGIBLE = TRUE) LIMIT 1;""",(cpr_hash,password_input,))
            result = cursor.fetchone()

            if(result):
                result = result[0]
                
                cursor.execute("""SELECT Has_registered FROM VOTERS_VIEW WHERE Voter_id = ? LIMIT 1;""",(result,))
                registered = cursor.fetchone()[0]

                if(registered == True):
                    response = make_response(redirect("/voting"))
                else:
                    response = make_response(redirect("/register"))

                response = updateToken(result,response)

                return response

            else:
                return {"Status": "Acess denied", "Error": "500"}

    else:
        return {"Status": "Not found", "Error": "404"}


@app.get("/voting")
def get_voting_sheet():
    parties = getCandidates()

    return render_template(
        "voting.html",
        parties = parties
        )

@app.post("/submit_vote")
def submit_vote():
        with sqlite3.connect("voting.db") as conn:
            cursor = conn.cursor() 

        try:
            candidate = request.form["candidate"]
            cursor.execute("""SELECT Candidate_id FROM Candidates WHERE Candidate_name = ?""", (candidate,))
            candidate = cursor.fetchone()
            vote = candidate[0] # for at sikre os det er en kandidat
            
            cursor.execute(
            "INSERT INTO votes (candidate_id,party_id) VALUES (?,(SELECT party_id FROM Candidates WHERE Candidate_id = ?))",
            (vote,vote,)
            )   
        except:
            party = request.form["party"]
            cursor.execute("""SELECT Party_id FROM Parties WHERE Party_name = ?""", (party,))
            party = cursor.fetchone() # fetchone() kalder funktionen og henter resultatet fra SQL.
            vote = party[0]
            cursor.execute(
            "INSERT INTO votes (party_id) VALUES (?)",
                (vote,)
                )
        finally:
            conn.commit()
            if vote is None:
                return{"status": "error"} # her ser vi lige om de har gemt
            else:
                return render_template(
                "confirmation.html",
                    vote = vote
                    )

@app.get("/register")

def register():
    token = request.cookies.get("session_token")

    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    cursor.execute("""SELECT Voter_ID FROM Session_view WHERE session_token = ? LIMIT 1;""",(token,))
    voterId = cursor.fetchone()
    
    if token is None or voterId is None:
        return redirect("/login")

    VoterId = VoterId[0]

    cursor.execute("""SELECT First_name FROM Voters WHERE VoterID = ? LIMIT 1""",(VoterId,))
    name = cursor.fetchone[0]
    
    otp = pyotp.random_base32()
    cursor.execute

    otp = (pyotp.totp.TOTP(otp).provisioning_uri(name=f'{name}@google.com', issuer_name='MitID'))

    return render_template(
        "otp.html",
        onetimepass = otp
    )

app.run(
    host="127.0.0.1",
    port=5000,
    debug=True
)


with sqlite3.connect("voting.db") as conn:
    cursor = conn.cursor()
    conn.commit()
    conn.close()