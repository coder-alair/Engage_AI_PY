import hashlib
import jwt
import time
from engage_api.settings import config
from typing import Dict

JWT_SECRET = config("JWT_SECRET")
JWT_ALGORITHM = config("JWT_ALGORITHM")


def decode_jwt(token: str) -> dict:
    try:
      decoded_token = jwt.decode(token,
                                 JWT_SECRET,
                                 algorithms=[JWT_ALGORITHM])
      
      return decoded_token if time.time() <= decoded_token["exp"] else None
    except Exception:
        return {}