from flask import Flask
from flask import request, redirect, url_for

app = Flask(__name__)

def build_doubled_value(value):
    return f"{value}{value}"

@app.route("/double")
def double_value():
    value = request.args.get("value", "Hello")
    return f"<p>{build_doubled_value(value)}</p>"