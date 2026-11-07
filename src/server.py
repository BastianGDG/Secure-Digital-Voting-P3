from flask import Flask, request, render_template, redirect, url_for, make_response
import sqlite3
import pyotp
from crypto import hashBcr, hashSha
import secrets
from datetime import datetime, timezone

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

    cursor.execute("""SELECT * FROM session_view WHERE voter_id = ?""",(result,))

    if(cursor.fetchone()):
        cursor.execute("""UPDATE Sessions SET session_token = ?, created_at = datetime('now'), expires_at = datetime('now', '+1 hour') WHERE voter_id = ?;""", (token,result,))
    else:
        cursor.execute("""INSERT INTO Sessions (voter_id,session_token,has_voted,mfa_verified) VALUES (?,?,0,0)""",(result,token))

    conn.commit()

    response = response

    response.set_cookie(
            "session_token",
            token,
             httponly=True,
            #secure=True,
            samesite="Strict"
             )
    
    return response

def register(token,totp):
    print(f"Token: {token}")

    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    try:
        cursor.execute("""SELECT Voter_ID FROM Session_view WHERE ((session_token = ?) AND (has_voted = 0)) LIMIT 1;""",(token,))
        voterID = cursor.fetchone()
    except:
        voterID = None
    
    if (token is None) or (voterID is None):
        return redirect("/login")

    print(f"Voter ID: {voterID}")
    voterID = voterID[0]

    cursor.execute("""SELECT First_name, Last_name FROM Voters WHERE Voter_ID = ? LIMIT 1""",(voterID,))
    names = cursor.fetchone()

    first_name = names[0]
    last_name = names[1]

    totp = (pyotp.totp.TOTP(str(totp)).provisioning_uri(name=f'{first_name+last_name}123@google.com', issuer_name='MitID'))

    conn.commit()
    conn.close()
    
    return render_template(
        "otp.html",
        onetimepass = totp
    )

def chk_perms(token,level):
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()
    if level > 0:
        cursor.execute("SELECT Voter_ID FROM Session_view WHERE ((session_token = ?) AND (has_voted = 0) AND (MFA_VERIFIED = ?))",(token,level))
    else:
        cursor.execute("SELECT Voter_ID FROM Session_view WHERE ((session_token = ?) AND (has_voted = 0))",(token,))
    result = cursor.fetchone()
    conn.close()
    return result

def chk_expiry(token):
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    cursor.execute("""SELECT expires_at from SESSION_VIEW WHERE session_token = ?""",(token,))
    expires_at = cursor.fetchone()

    if(not expires_at):
        # session doesnt exist
        return True

    expires_at = expires_at[0]

    expiry = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if now >= expiry:
        cursor.execute("""UPDATE Voters SET MFA_VERIFIED = 0 WHERE voter_id = (SELECT Voter_ID from Session_view WHERE session_token = ?);""", (token,))
        return True
    else:
        # sesion not expired
        return False

@app.route("/",methods=['GET'])
def main():
    return render_template(
            "index.html"
            )

@app.route("/login",methods=['GET','POST'])
def handle_method_login():
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
                return {"Status": "Acess denied"}

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
                    response = make_response(redirect("/two_fac"))
                else:
                    response = make_response(redirect("/register"))

                response = updateToken(result,response)

                return response

            else:
                return {"Status": "Acess denied"}

    else:
        return {"Status": "Not found", "Error": "404"}

@app.route("/register",methods=['GET','POST'])
def handle_method_register():
    token = request.cookies.get("session_token")

    if(chk_expiry(token) == True):
        return(make_response(redirect("/login")))

    if(not chk_perms(token,0)):
        return(make_response(redirect("/")))

    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    cursor.execute("""SELECT voter_id FROM session_view WHERE ((session_token = ?) AND (mfa_verified = 1));""",(token,))
    if(cursor.fetchone()):
        return(make_response(redirect("/two_fac")))

    cursor.execute("""SELECT voter_id FROM session_view WHERE session_token = ? LIMIT 1;""",(token,))
    VoterId = cursor.fetchone()

    if(not VoterId):
        return(make_response(redirect("/login")))

    VoterId = VoterId[0]

    print(VoterId)

    cursor.execute("""SELECT OTP FROM Voters_view WHERE Voter_id = ?""",(VoterId,))
    totp = cursor.fetchone()[0]

    print(totp)

    if totp is None:
        totp = pyotp.random_base32()
        print(totp)
        cursor.execute("""UPDATE Voters SET OTP = ? WHERE voter_id = ?;""", (totp,VoterId))
        conn.commit()
    else:
        pass

    if request.method == 'GET':
        print(totp)
        response = register(token,totp)
        return(response)
    
    elif request.method == 'POST':
        otp = request.form["OTP"]
        print(f"OTP: {otp}")
        print(f"TOTP: {totp}")
        print(pyotp.TOTP(totp).now())

        if(pyotp.TOTP(totp).verify(otp)):
            cursor.execute("""UPDATE Sessions SET mfa_verified = 1 WHERE voter_id = ?""", (VoterId))
            conn.commit()
        else:
            conn.close()
            return{"Error": "Wrong OTP"}
    else:
        conn.close()
        return {"Status": "Not found", "Error": "404"}

@app.route("/two_fac",methods=['GET','POST'])
def handle_method_twofac():
    token = request.cookies.get("session_token")

    if(chk_expiry(token) == True):
        return(make_response(redirect("/login")))

    if(not chk_perms(token,1)):
        return(make_response(redirect("/register")))

    with sqlite3.connect("voting.db") as conn:
            cursor = conn.cursor()
    cursor.execute("SELECT Voter_ID FROM Session_view WHERE ((session_token = ?) AND (has_voted = 0) AND (mfa_verified = 1))",(token,))
        
    if(cursor.fetchone() == None):
            return(make_response(redirect("/login")))

    voterID = cursor.fetchone()
    voterID = voterID[0]

    if request.method == 'GET':
        conn.close()
        return render_template(
            "twofac.html"
        )
    
    elif request.method == 'POST':
        totp = request.form["TOTP"]
        totp = int(totp)

        cursor.execute("""SELECT OTP From Voters_view WHERE((Voter_id = ?) AND (Has_voted = 0))""",(voterID,))
        otp = cursor.fetchone()
        otp = otp[0]

        if(otp.verify(totp)):
            cursor.execute("""UPDATE Sessions SET mfa_verified = 1 WHERE voter_id = ?""", (voterID,))
            response = make_response(redirect("/voting"))

            return(updateToken(voterID,response))
        
        else:
            return render_template(
            "twofac.html"
        )
            
    else:
        return {"Status": "Not found", "Error": "404"}
    
@app.get("/voting")
def get_voting_sheet():
    token = request.cookies.get("session_token")

    if(chk_expiry(token) == True):
        return(make_response(redirect("/login")))
    
    if(not chk_perms(token,1)):
        return(make_response(redirect("/register")))

    parties = getCandidates()

    return render_template(
        "voting.html",
        parties = parties
        )

@app.post("/submit_vote")
def submit_vote():
        with sqlite3.connect("voting.db") as conn:
            cursor = conn.cursor() 

        token = request.cookies.get("session_token")

        if(chk_expiry(token) == True):
            return(make_response(redirect("/login")))
         
        if(cursor.fetchone() == None):
            return(make_response(redirect("/")))
        
        try:
            candidate = request.form["candidate"]
            cursor.execute("""SELECT Candidate_id FROM Candidates WHERE Candidate_name = ?""", (candidate,))
            candidate = cursor.fetchone()
            vote = candidate[0] # for at sikre os det er en kandidat
            
            cursor.execute(
            "INSERT INTO votes (candidate_id,party_id) VALUES (?,(SELECT party_id FROM Candidates WHERE Candidate_id = ?))",
            (vote,vote,)
            ) 

            cursor.execute("""UPDATE Sessions SET has_voted = 1 WHERE session_token = ?;""", (token))

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
            conn.close()

        if vote is None:
            return{"status": "error"} # her ser vi lige om de har gemt
        
        else:
            return render_template(
            "confirmation.html",
                vote = vote
                )
        
@app.get("/reciept")
def confirmation():
    token = request.form["session_token"]

    if(chk_expiry(token) == True):
        return(make_response(redirect("/login")))

    if(not chk_perms(token,1)):
        return(make_response(redirect("/register")))

    return render_template(
        "confirmation.html"
    )

app.run(
    host="127.0.0.1",
    port=80,
    debug=True
)

with sqlite3.connect("voting.db") as conn:
    cursor = conn.cursor()
    conn.commit()
    conn.close()