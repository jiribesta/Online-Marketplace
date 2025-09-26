import json
import os
import sys

CONFIG_FILE_DIR = "../"
CONFIG_FILE_NAME = "config.json"

def load_config():
    try:
        with open(os.path.join(CONFIG_FILE_DIR, CONFIG_FILE_NAME), "r") as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Unexpected error when obtaining config data: {e}")
        sys.exit(1)

def get_abs_or_rel_file_path(file_path):
    if os.path.isabs(file_path):
        return file_path
    else:
        return os.path.join(CONFIG_FILE_DIR, file_path)

config = load_config()

DB_USERNAME = config.get("database", {}).get("db_username", "postgres")
DB_PASSWORD = config.get("database", {}).get("db_password", "password123")
DB_HOST = config.get("database", {}).get("db_host", "localhost")
DB_PORT = config.get("database", {}).get("db_port", 5432)
DB_NAME = config.get("database", {}).get("db_name", "marketplace")

LOG_FILE_PATH = get_abs_or_rel_file_path(config.get("log_file_path", "./log.txt"))