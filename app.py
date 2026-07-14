from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import json
import os

load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

mongo_uri = os.getenv("MONGO_URI")
collection = None

if mongo_uri:
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("MongoDB Atlas Connected")

        db = client["company"]
        collection = db["employees"]

    except Exception as error:
        print(f"MongoDB Connection Error: {error}")
else:
    print("MongoDB Connection Error: MONGO_URI is not configured")


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/todo")
def todo():
    return render_template("todo.html")


@app.route("/submit", methods=["POST"])
def submit():
    try:
        if collection is None:
            raise RuntimeError(
                "Database not connected. Check MONGO_URI in the .env file."
            )

        employee = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "department": request.form.get("department", "").strip(),
        }

        if not all(employee.values()):
            raise ValueError("Name, email, and department are required.")

        collection.insert_one(employee)

        return redirect(url_for("success"))

    except Exception as error:
        return render_template("index.html", error=str(error))


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/api", methods=["GET"])
def api():
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return jsonify(data), 200

    except FileNotFoundError:
        return jsonify(
            {
                "status": "error",
                "message": "data.json file was not found.",
            }
        ), 404

    except json.JSONDecodeError:
        return jsonify(
            {
                "status": "error",
                "message": "data.json contains invalid JSON.",
            }
        ), 500

    except Exception as error:
        return jsonify(
            {
                "status": "error",
                "message": str(error),
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True, port=50001)