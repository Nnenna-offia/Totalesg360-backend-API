"""JWT token creation and validation service."""
import uuid
import jwt
from datetime import datetime
from django.conf import settings

JWT_ALGORITHM = getattr(settings, "JWT_ALGORITHM", "HS256")
JWT_SECRET = getattr(settings, "JWT_SECRET", settings.SECRET_KEY)
ACCESS_EXP = getattr(settings, "JWT_ACCESS_LIFETIME_SECONDS", 300)  # 5 minutes
REFRESH_EXP = getattr(settings, "JWT_REFRESH_LIFETIME_SECONDS", 7 * 24 * 3600)  # 7 days
ISSUER = getattr(settings, "JWT_ISS", "totalesg360")


def _now_ts():
    """Return current UTC timestamp as integer."""
    return int(datetime.utcnow().timestamp())


def make_token(payload: dict, lifetime: int, jti: str = None) -> str:
    """Create a signed JWT with the given payload and lifetime.
    
    Args:
        payload: Dictionary of claims to include
        lifetime: Token lifetime in seconds
        jti: Optional JWT ID (generated if not provided)
    
    Returns:
        Encoded JWT string
    """
    jti = jti or str(uuid.uuid4())
    now = _now_ts()
    data = dict(payload)
    data.update({"jti": jti, "iat": now, "exp": now + lifetime, "iss": ISSUER})
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token.
    
    Args:
        token: Encoded JWT string
    
    Returns:
        Decoded payload dictionary
    
    Raises:
        jwt.exceptions.*: Various JWT validation errors
    """
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"verify_aud": False}
    )