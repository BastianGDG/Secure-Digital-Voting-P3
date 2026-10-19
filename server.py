from flask import Flask, request, render_template

app = Flask(__name__)

@app.get("/candidates")
def candidates():
    return ["Candidate A", "Candidate B"]


@app.get("/")
def main():
    return render_template("index.html")
    

@app.post("/vote")
def vote():
    data = request.get_json()

    candidate = data["candidate"]

    print(f"Vote received for {candidate}")

    return {"status": "success"}

app.run(
    host="127.0.0.1",
    port=5000,
    debug=True
)