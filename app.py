from pathlib import Path
import json
import os

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from pymongo import MongoClient
from pymongo.errors import PyMongoError


load_dotenv()

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

mongo_uri = os.getenv("MONGO_URI")

client = None
employee_collection = None
todo_collection = None


if mongo_uri:
    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
        )

        client.admin.command("ping")

        print("MongoDB Atlas Connected")

        db = client["company"]

        employee_collection = db["employees"]
        todo_collection = db["todo_items"]

    except PyMongoError as error:
        print(f"MongoDB Connection Error: {error}")

else:
    print(
        "MongoDB Connection Error: "
        "MONGO_URI is not configured"
    )


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/todo")
def todo():
    return render_template("todo.html")


@app.route("/submit", methods=["POST"])
def submit():
    try:
        if employee_collection is None:
            raise RuntimeError(
                "Database not connected. "
                "Check MONGO_URI in the .env file."
            )

        employee = {
            "name": request.form.get(
                "name",
                "",
            ).strip(),
            "email": request.form.get(
                "email",
                "",
            ).strip(),
            "department": request.form.get(
                "department",
                "",
            ).strip(),
        }

        if not all(employee.values()):
            raise ValueError(
                "Name, email, and department are required."
            )

        employee_collection.insert_one(employee)

        return redirect(url_for("success"))

    except Exception as error:
        return render_template(
            "index.html",
            error=str(error),
        )


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/api", methods=["GET"])
def api():
    try:
        with DATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
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


@app.route("/submittodoitem", methods=["POST"])
def submit_todo_item():
    try:
        if todo_collection is None:
            raise RuntimeError(
                "Database not connected. "
                "Check MONGO_URI in the .env file."
            )

        item_name = request.form.get(
            "itemName",
            "",
        ).strip()

        item_description = request.form.get(
            "itemDescription",
            "",
        ).strip()

        if not item_name or not item_description:
            error_message = (
                "Item Name and Item Description are required."
            )

            if request.is_json:
                return jsonify(
                    {
                        "status": "error",
                        "message": error_message,
                    }
                ), 400

            return render_template(
                "todo.html",
                error=error_message,
            ), 400

        todo_item = {
            "itemName": item_name,
            "itemDescription": item_description,
        }

        result = todo_collection.insert_one(todo_item)

        if request.is_json:
            return jsonify(
                {
                    "status": "success",
                    "message": "To-Do item saved successfully.",
                    "id": str(result.inserted_id),
                }
            ), 201

        return render_template(
            "todo.html",
            success="To-Do item saved successfully.",
        ), 201

    except Exception as error:
        if request.is_json:
            return jsonify(
                {
                    "status": "error",
                    "message": str(error),
                }
            ), 500

        return render_template(
            "todo.html",
            error=str(error),
        ), 500


if __name__ == "__main__":
    app.run(
        debug=True,
        port=50001,
    )