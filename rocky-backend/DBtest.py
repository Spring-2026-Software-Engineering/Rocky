import requests

BASE = "http://127.0.0.1:5001"

def test(name, condition):
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")

print("\nDatabase Tests\n")

# create valid user
res = requests.post(f"{BASE}/users", json={
    "name": "Jane",
    "email": "jane@test.com",
    "flash_id": "321",
    "role": "student"
})
test("Create valid user", res.status_code == 200)


#create user with missing fields
res = requests.post(f"{BASE}/users", json={"name": "Bad"})
test("Reject invalid user", res.status_code == 400)


# get user
res = requests.get(f"{BASE}/users")
users = res.json()
test("Get users list", isinstance(users, list))


# for getting ID
user_id = users[0]["_id"] if users else None


# get user
if user_id:
    res = requests.get(f"{BASE}/users/{user_id}")
    test("Get valid user", res.status_code == 200)


# get invalid id user
res = requests.get(f"{BASE}/users/abc")
test("Reject invalid ID format", res.status_code == 400)


# update user
if user_id:
    res = requests.put(f"{BASE}/users/{user_id}", json={"role": "admin"})
    test("Update user", res.status_code == 200)


# update user bad data
if user_id:
    res = requests.put(f"{BASE}/users/{user_id}", json={"role": 123})
    test("Reject bad update", res.status_code == 400)


# delete user
if user_id:
    res = requests.delete(f"{BASE}/users/{user_id}")
    test("Delete user", res.status_code == 200)


# delete
if user_id:
    res = requests.delete(f"{BASE}/users/{user_id}")
    test("Delete non-existent user handled", res.status_code in [200, 404])


# crete course
res = requests.post(f"{BASE}/courses", json={
    "name": "CS101",
    "semester": {"year": 2026, "term": "Spring"}
})
test("Create valid course", res.status_code == 200)


# create invalid course
res = requests.post(f"{BASE}/courses", json={
    "name": "BadCourse",
    "semester": "wrong"
})
test("Reject invalid course", res.status_code == 400)


# create API key
res = requests.post(f"{BASE}/api_keys", json={
    "u_id": user_id,
    "c_id": "fake_course",
    "expire": None
})
test("Create API key", res.status_code == 200)


print("\nDONE")