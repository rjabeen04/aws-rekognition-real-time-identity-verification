import time
import json
import os
import streamlit as st
from boto3.dynamodb.conditions import Key
from app.config import DATA_FILE


def poll_dynamodb(table, capture_key, retries=15, delay=1):
    for _ in range(retries):
        result = table.query(KeyConditionExpression=Key('ImageId').eq(capture_key))
        if result['Items']:
            return result['Items'][0]
        time.sleep(delay)
    return None


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"alerts": [], "logs": [], "settings": {}}


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "settings": {
                "similarity_threshold": st.session_state.get("similarity_threshold", 80),
                "max_labels": st.session_state.get("max_labels", 15),
                "custom_danger_labels": list(st.session_state.get("custom_danger_labels", []))
            }
        }, f)
