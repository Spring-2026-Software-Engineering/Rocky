import sys, json, os, hashlib

p = os.path.join(os.path.dirname(__file__), 'db.json')
args = sys.argv[1:]

if not args:
    sys.exit('Usage: python validate_key.py <key>')

def get_db():
    try:
        with open(p) as f: return json.load(f)
    except: return []

def h(v):
    return hashlib.sha256(v.encode()).hexdigest()

found = next((x for x in get_db() if x.get('hash') == h(args[0])), None)

if not found: 
    print('\naccess denied (invalid key)')
else: 
    print(f"\naccess granted\nid: {found['id']}\ncreated: {found['createdAt']}\n")