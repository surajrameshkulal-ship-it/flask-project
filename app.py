from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")

try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("MongoDB Atlas Connected")

    db = client["company"]
    collection = db["employees"]

except Exception as e:
    print("MongoDB Connection Error:", e)
    collection = None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    try:
        if collection is None:
            raise Exception("Database not connected. Check MONGO_URI in .env")

        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "department": request.form["department"]
        }

        collection.insert_one(data)

        return redirect(url_for("success"))

    except Exception as e:
        return render_template("index.html", error=str(e))


@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(debug=True, port=50001)
