from flask import Flask
from flask import request, redirect, url_for, jsonify
from mongita import MongitaClientDisk

app = Flask(__name__)

client = MongitaClientDisk()
db = client["rocky_db"]
collection = db["items"]

#Create
@app.route("/items", methods=["POST"])
def add_item():
    data = request.json
    collection.insert_one(data)
    return jsonify({"message": "Item added"})
    
#read
@app.route("/items", methods=["GET"])
def get_items():
    items = list(collection.find())
    for item in items:
        item["_id"] = str(item["_id"])
    return jsonify(items)

#update
@app.route("/items/<item_id>", methods=["PUT"])
def update_item(item_id):
    data = request.json
    collection.update_one({"_id": item_id}, {"$set": data})
    return jsonify({"message": "Updated"})

#delete
@app.route("/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    collection.delete_one({"_id": item_id})
    return jsonify({"message": "Deleted"})
