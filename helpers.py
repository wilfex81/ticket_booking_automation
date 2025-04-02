import json
import os

# Function to load sites from a JSON file
def load_sites(file_path="sites.json"):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sites = json.load(f)
        except json.JSONDecodeError:
            sites = {}  # If JSON is corrupted, start fresh
    else:
        sites = {}  # Return an empty dict if file doesn't exist
    return sites

# Function to save sites to a JSON file
def save_sites(sites, file_path="sites.json"):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sites, f, ensure_ascii=False, indent=4)
