from flask import Flask
from flask import request, jsonify
from mongita import MongitaClientDisk
from bson import ObjectId
from datetime import datetime, timezone

app = Flask(__name__)

client = MongitaClientDisk()
db = client["rocky_db"]
users = db["users"]
courses = db["courses"]
api_keys = db["api_keys"]


# ── Users ──────────────────────────────────────────────────────────────────────

@app.route("/users", methods=["POST"])
def create_user():
    # Expected: { name, email, flash_id, role: "student"|"instructor"|"admin" }
    data = request.json
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    users.insert_one(data)
    return jsonify({"message": "User created"})

@app.route("/users", methods=["GET"])
def get_users():
    result = list(users.find())
    for u in result:
        u["_id"] = str(u["_id"])
    return jsonify(result)

@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user["_id"] = str(user["_id"])
    return jsonify(user)

@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    users.update_one({"_id": ObjectId(user_id)}, {"$set": data})
    return jsonify({"message": "User updated"})

@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    users.delete_one({"_id": ObjectId(user_id)})
    return jsonify({"message": "User deleted"})


# ── Courses ────────────────────────────────────────────────────────────────────

@app.route("/courses", methods=["POST"])
def create_course():
    # Expected: { name, instructor_ids: [], student_ids: [], semester: { year, term } }
    data = request.json
    courses.insert_one(data)
    return jsonify({"message": "Course created"})

@app.route("/courses", methods=["GET"])
def get_courses():
    result = list(courses.find())
    for c in result:
        c["_id"] = str(c["_id"])
    return jsonify(result)

@app.route("/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    course = courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        return jsonify({"error": "Course not found"}), 404
    course["_id"] = str(course["_id"])
    return jsonify(course)

@app.route("/courses/<course_id>", methods=["PUT"])
def update_course(course_id):
    data = request.json
    courses.update_one({"_id": ObjectId(course_id)}, {"$set": data})
    return jsonify({"message": "Course updated"})

@app.route("/courses/<course_id>", methods=["DELETE"])
def delete_course(course_id):
    courses.delete_one({"_id": ObjectId(course_id)})
    return jsonify({"message": "Course deleted"})


# ── API Keys ───────────────────────────────────────────────────────────────────

@app.route("/api_keys", methods=["POST"])
def create_api_key():
    # Expected: { u_id, c_id, expire: ISO string | null }
    data = request.json
    data["created"] = datetime.now(timezone.utc).isoformat()
    api_keys.insert_one(data)
    return jsonify({"message": "API key created"})

@app.route("/api_keys", methods=["GET"])
def get_api_keys():
    result = list(api_keys.find())
    for k in result:
        k["_id"] = str(k["_id"])
    return jsonify(result)

@app.route("/api_keys/<key_id>", methods=["GET"])
def get_api_key(key_id):
    key = api_keys.find_one({"_id": ObjectId(key_id)})
    if not key:
        return jsonify({"error": "API key not found"}), 404
    key["_id"] = str(key["_id"])
    return jsonify(key)

@app.route("/api_keys/<key_id>", methods=["DELETE"])
def delete_api_key(key_id):
    api_keys.delete_one({"_id": ObjectId(key_id)})
    return jsonify({"message": "API key deleted"})

if __name__ == "__main__":
    app.run(debug=True, port = 5001)