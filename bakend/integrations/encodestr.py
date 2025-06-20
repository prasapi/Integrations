import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import hashlib

import requests
state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': 'krushna.021523@gmail.com',
        'org_id': 'TestOrg'
    }
encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')
code_verifier = secrets.token_urlsafe(32)
m = hashlib.sha256()
m.update(code_verifier.encode('utf-8'))
code_challenge = base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace('=', '')
print("state=",str(state_data['state']),code_challenge)
