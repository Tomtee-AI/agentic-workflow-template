"""
AuthN/AuthZ at the edge. Raw credentials never propagate past this module.
Implement OAuth/OIDC/mTLS verification here.
"""


def authenticate(raw_request: dict) -> str:
    """Validate credentials and return the principal identity string."""
    # TODO: implement OAuth/OIDC/mTLS verification
    token = raw_request.get("authorization", "")
    if not token:
        raise PermissionError("Missing authorization token")
    return "user:anonymous"  # replace with decoded identity
