from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, oauth2
import requests
from jose import JWTError, jwt


# Your Auth0 domain
AUTH0_DOMAIN = "dev-l2onngs40ome5udh.us.auth0.com"
API_IDENTIFIER = "https://freeonlinelibrary.local"

# Get Auth0 public key for decoding JWT
def get_jwk():
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    return requests.get(url).json()

# Decode JWT using Auth0 public key
def decode_jwt(token: str):
    try:
        headers = jwt.get_unverified_header(token)
        if headers is None:
            raise JWTError("Unable to decode header")

        # Get the key id from header
        key_id = headers["kid"]
        jwks = get_jwk()
        public_key = None

        for key in jwks["keys"]:
            if key["kid"] == key_id:
                public_key = key
                break

        if public_key is None:
            raise JWTError("Unable to find appropriate key")

        # Now we decode the JWT
        rsa_key = {
            "kty": public_key["kty"],
            "kid": public_key["kid"],
            "use": public_key["use"],
            "n": public_key["n"],
            "e": public_key["e"]
        }

        payload = jwt.decode(token, rsa_key, algorithms=["RS256"])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Dependency to get current user from the access token
def get_current_user(request: Request):
    templist = []
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        templist = auth_header.split()
        return decode_jwt(templist[-1])
    raise HTTPException(status_code=401)

''''R
'@app.get("/books")
async def get_books(current_user: dict = Depends(get_current_user)):
    # This is where you would implement logic to return books
    return {"message": "Welcome to the online library!", "user": current_user}'
'''


'''
this is my comment
'''