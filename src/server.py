from flask import Flask, request, render_template, redirect, url_for, make_response
import sqlite3
import pyotp
from crypto import hashBcr, hashSha
import secrets
from datetime import datetime, timezone
import logging

# ---- Setup ------

app = Flask(__name__)

logging.basicConfig(filename="voting.log",
                    format='%(asctime)s %(levelname)s: %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# ----- Setup ------

def getCandidates():
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    cursor.execute("""SELECT * FROM PARTIES_VIEW;""")

    temp = []

    for i in cursor:
        party = i[0]
        temp.append(party)

    parties={}

    cursor.execute("""SELECT * FROM CANDIDATES_VIEW;""")

    for n in range(len(temp)):
        cand = []
        cursor.execute(f"""SELECT CANDIDATE_NAME FROM CANDIDATES_VIEW WHERE PARTY_ID = {n+1};""")
        for i in cursor:
            cand.append(i[0])
        parties[temp[n]] = cand

    cursor.execute("""SELECT ABBREVIATION FROM PARTIES_VIEW;""")
    abbreviations = []
    result = cursor.fetchone()

    for i in range(len(temp)):
        abbreviations.append(result[i])
        
    return parties, abbreviations

def updateToken(result,response):

    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    token = secrets.token_urlsafe(32)

    cursor.execute("""SELECT * FROM session_view WHERE ((voter_id = ?) AND ((Select has_voted FROM Voters WHERE Voter_id = ?) = 0))""",(result,result,))

    if(cursor.fetchone()):
        cursor.execute("""UPDATE Sessions SET session_token = ?, created_at = datetime('now', '+1 hour'), expires_at = datetime('now', '+1 hour', '+5 minute') WHERE voter_id = ?;""", (token,result,))
    else:
        cursor.execute("""INSERT INTO Sessions (voter_id,session_token,mfa_verified) VALUES (?,?,0)""",(result,token))

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
        cursor.execute("""SELECT Voter_ID FROM Session_view WHERE session_token = ? AND MFA_VERIFIED = ? AND (
                    SELECT has_voted FROM Voters WHERE Voters.voter_id = Session_view.Voter_ID) = 0;""",(token,level))
    else:
        cursor.execute("""SELECT Voter_ID FROM Session_view WHERE session_token = ? AND (
                    SELECT has_voted FROM Voters WHERE Voters.voter_id = Session_view.Voter_ID) = 0;""",(token,))
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
                
                cursor.execute("""SELECT Has_registered,Has_voted FROM VOTERS_VIEW WHERE Voter_id = ? LIMIT 1;""",(result,))
                
                row = cursor.fetchone()
                registered = row[0]
                voted = row[1]

                if(registered == True):
                    response = make_response(redirect("/two_fac"))
                elif(voted == True):
                    return make_response(redirect("/confirmation"))
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
        return(make_response(redirect("/login")))

    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor()

    cursor.execute("""SELECT has_registered FROM voters_view WHERE Voter_ID = ((SELECT Voter_ID FROM Session_VIEW WHERE session_token = ?));""",(token,))
    if(cursor.fetchone()[0] == 1):
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

        if(pyotp.TOTP(totp).verify(otp)):
            cursor.execute("""UPDATE Voters SET has_registered = 1 WHERE voter_id = ?""", (VoterId,))
            cursor.execute("""UPDATE Sessions SET mfa_verified = 1 WHERE voter_id = ?""", (VoterId,))
            conn.commit()

            return(updateToken(VoterId,make_response(redirect("/voting"))))
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

    if(not chk_perms(token,0)):
        return(make_response(redirect("/register")))

    with sqlite3.connect("voting.db") as conn:
            cursor = conn.cursor()

    cursor.execute("SELECT Voter_ID FROM Session_view WHERE (session_token = ?)",(token,))

    voterID = cursor.fetchone()

    if(not voterID):
        return(make_response(redirect("/login")))

    voterID = voterID[0]
    
    if request.method == 'GET':
        conn.close()
        return render_template(
            "twofac.html"
        )
    
    elif request.method == 'POST':
        otp = request.form["OTP"]
        otp = int(otp)

        cursor.execute("""SELECT OTP From Voters_view WHERE((Voter_id = ?) AND (Has_voted = 0))""",(voterID,))
        totp = cursor.fetchone()
        totp = totp[0]

        if(pyotp.TOTP(totp).verify(otp)):
            cursor.execute("""UPDATE Sessions SET mfa_verified = 1 WHERE voter_id = ?""", (voterID,))
            conn.commit()
            conn.close()

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

    parties,abbreviations = getCandidates()

    print(abbreviations)

    return render_template(
        "voting.html",
        parties = parties,
        abbreviations = abbreviations
        )

@app.post("/submit_vote")
def submit_vote():
    with sqlite3.connect("voting.db") as conn:
        cursor = conn.cursor() 

    token = request.cookies.get("session_token")

    if(chk_expiry(token) == True):
        return(make_response(redirect("/login")))

    if(not chk_perms(token,1)):
        return(make_response(redirect("/login")))   

    vote = request.form.get("vote")

    vote_type, vote_value = vote.split(":", 1)

    if vote_type == "candidate":
        cursor.execute("""SELECT Candidate_id FROM Candidates WHERE Candidate_name = ?""", (vote_value,))
        candidate = cursor.fetchone()
        vote = candidate[0] # for at sikre os det er en kandidat
        
        cursor.execute(
        "INSERT INTO votes (candidate_id,party_id,timestamp) VALUES (?,(SELECT party_id FROM Candidates WHERE Candidate_id = ?),(strftime('%Y-%m-%d %H:%M:%f', 'now')))",
        (vote,vote,)
        ) 

    elif vote_type == "party":
        print(vote_value)
        cursor.execute("""SELECT party_id FROM Parties WHERE Party_name = ?""", (vote_value,))
        party = cursor.fetchone()
        vote = party[0] # for at sikre os det er en kandidat
        
        cursor.execute(
        "INSERT INTO votes (candidate_id,party_id,timestamp) VALUES (?,(SELECT party_id FROM Candidates WHERE Candidate_id = ?),(strftime('%Y-%m-%d %H:%M:%f', 'now')))",
        (None,vote,)
        ) 
    
    else:
        return{"status": "error"}    

    try:
        cursor.execute("""UPDATE Voters SET has_voted = 1 WHERE Voter_Id = (SELECT Voter_id from Sessions WHERE session_token = ?);""", (token,))
        cursor.execute("""SELECT Voter_ID From Session_view WHERE session_token = ?""",(token,))
        ID = cursor.fetchone()

        cursor.execute("""DELETE FROM Sessions WHERE session_token = ?""",(token,))
        
        
        logging.info("VOTE_ACCEPTED voter_id=%s", ID)

        conn.commit()
        conn.close()

        return render_template(
        "confirmation.html",
            vote = vote
            )
    except:
        return{"status": "error"}


        
@app.get("/reciept")
def confirmation():
    return render_template(
        "confirmation.html"
    )

app.run(
    host="127.0.0.1",
    port=80,
    debug=True
)

with sqlite3.connect("voting.db") as conn:
    conn.commit()
    conn.close()