# src/ai_service/api_keys.py

import os
from pathlib import Path


def load_api_keys():
    """ API keysを読み込む """
    keys = {}

    secrets_path = Path("/app/secrets/.api_keys")

    if secrets_path.exists():
        with open(secrets_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    keys[key] = value
    else:
        if Path("/app/secrets").exists():
            print("Contents of /app/secrets:")
            print(os.listdir("/app/secrets"))

    return keys


API_KEYS = load_api_keys()
