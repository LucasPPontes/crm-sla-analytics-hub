import json
import os
from typing import Dict, Any

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "mockCrmData.json")

def load_crm_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_PATH):
        return {"customers": [], "deals": [], "interactions": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
