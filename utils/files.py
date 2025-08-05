# utils/files.py

import csv

def export_users_to_csv(users: list[dict], path: str):
    with open(path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=users[0].keys())
        writer.writeheader()
        writer.writerows(users)

def import_users_from_csv(path: str) -> list[dict]:
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)