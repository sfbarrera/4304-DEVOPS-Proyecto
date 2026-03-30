"""
Run this script once to generate a static Bearer token for testing/Postman.

    python generate_token.py

Copy the printed token and use it as:
    Authorization: Bearer <token>
"""
from app import app
from flask_jwt_extended import create_access_token
from datetime import timedelta

with app.app_context():
    token = create_access_token(
        identity="static-api-client",
        expires_delta=timedelta(days=365)   # 1 year — good enough for testing
    )
    print("\n── Static Bearer Token ──────────────────────────────────────────")
    print(token)
    print("────────────────────────────────────────────────────────────────\n")
    print("Use in Postman:")
    print("  Header: Authorization")
    print("  Value:  Bearer " + token)
