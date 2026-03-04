# Create and run Virtual environment

```cmd
REM Create
cd .\rocky-backend
py -3 -m venv .venv
REM Activate
.venv\Scripts\activate
```

> If activation is blocked, run this first in PowerShell:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

# Install Dependencies

```cmd
pip install -r requirements.txt
```

# Running Flask

```cmd
python main.py  flask --app main run --debug
```

# Adding a New Collection

To add a new collection (e.g. `assignments`), open `main.py` and follow these steps:

### 1. Register the collection (after the existing ones)
```python
assignments = db["assignments"]
```

### 2. Add routes

```python
@app.route("/assignments", methods=["POST"])
def create_assignment():
    data = request.json
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    assignments.insert_one(data)
    return jsonify({"message": "Assignment created"})

@app.route("/assignments", methods=["GET"])
def get_assignments():
    result = list(assignments.find())
    for a in result:
        a["_id"] = str(a["_id"])
    return jsonify(result)

@app.route("/assignments/<assignment_id>", methods=["GET"])
def get_assignment(assignment_id):
    assignment = assignments.find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    assignment["_id"] = str(assignment["_id"])
    return jsonify(assignment)

@app.route("/assignments/<assignment_id>", methods=["PUT"])
def update_assignment(assignment_id):
    data = request.json
    assignments.update_one({"_id": ObjectId(assignment_id)}, {"$set": data})
    return jsonify({"message": "Assignment updated"})

@app.route("/assignments/<assignment_id>", methods=["DELETE"])
def delete_assignment(assignment_id):
    assignments.delete_one({"_id": ObjectId(assignment_id)})
    return jsonify({"message": "Assignment deleted"})
```

### 3. Test with Postman / Thunder Client
- **POST** `http://127.0.0.1:5000/assignments` with `Content-Type: application/json` and a JSON body
- **GET** `http://127.0.0.1:5000/assignments` to retrieve all
- **DELETE** `http://127.0.0.1:5000/assignments/<id>` to remove one

> Data is stored on disk in `mongita/rocky_db/<collection_name>/` — stopping Flask does not erase data.

