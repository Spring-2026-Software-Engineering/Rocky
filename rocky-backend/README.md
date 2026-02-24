# Create and run Virtual environment

```cmd
REM Create
cd .\rocky-backend
py -3 -m venv .venv
REM Activate
.venv\Scripts\activate
```

# Running Flask

```cmd
flask --app main run
flask --app main run --debug
flask --app main run --debug --port 5001
```