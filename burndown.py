import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys


CSV_FILE = "issues.csv"
CREATED_COLUMN = "createdAt"
CLOSED_COLUMN = "closedAt"

PROJECT_START = pd.Timestamp("2026-02-11")
PROJECT_END = pd.Timestamp("2026-04-20")


# load CSV
file_path = Path(CSV_FILE)
if not file_path.is_file():
    print(f"Error: File '{CSV_FILE}' not found.")
    sys.exit(1)

df = pd.read_csv(CSV_FILE, encoding='utf-8-sig', quotechar='"')
df.columns = df.columns.str.strip()
print("Columns found:", df.columns.tolist())

# Convert dates
def parse_datetime(series):
    series = pd.to_datetime(series, errors='coerce', utc=True)
    return series.dt.tz_convert(None)

df[CREATED_COLUMN] = parse_datetime(df[CREATED_COLUMN])
df[CLOSED_COLUMN] = parse_datetime(df[CLOSED_COLUMN])

# Date ranges
today = pd.Timestamp.today().normalize()

all_dates = pd.date_range(PROJECT_START, PROJECT_END)   # for axis + ideal
actual_dates = pd.date_range(PROJECT_START, min(today, PROJECT_END))  # blue only

total_issues = df.shape[0]


# Actual burndown (blue)
remaining = []
for date in actual_dates:
    open_issues = df[
        df[CLOSED_COLUMN].isna() | (df[CLOSED_COLUMN] > date)
    ].shape[0]
    remaining.append(open_issues)


# Ideal burndown (red)
ideal_line = [
    total_issues - (total_issues * i / (len(all_dates) - 1))
    for i in range(len(all_dates))
]

# Plot
plt.figure(figsize=(12,6))

plt.plot(actual_dates, remaining, marker='o', label='Actual')  # stops at today
plt.plot(all_dates, ideal_line, linestyle='--', color='red', label='Ideal')  # full range

plt.title("Delta Burndown Chart")
plt.xlabel("Date")
plt.ylabel("Remaining Issues")
plt.grid(True)
plt.xticks(rotation=45)
plt.ylim(0, total_issues + 1)
plt.xlim(PROJECT_START, PROJECT_END)

plt.legend()
plt.tight_layout()
plt.show()
