import json, os, hashlib, secrets
from datetime import datetime, timezone

p = os.path.join(os.path.dirname(__file__), 'db.json')

def get_db():
    try:
        with open(p) as f: return json.load(f)
    except: return []

def h(v):
    return hashlib.sha256(v.encode()).hexdigest()

k = f"sk_kent_{secrets.token_hex(32)}"
db = get_db()
n = datetime.now(timezone.utc)

db.append({
    'id': int(n.timestamp() * 1000), 
    'hash': h(k), 
    'createdAt': n.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
})

with open(p, 'w') as f: json.dump(db, f, indent=2)
print(f"\nGenerated Key:\n{k}\n")