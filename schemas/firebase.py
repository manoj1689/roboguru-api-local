from pydantic import BaseModel

class FirebaseLoginInput(BaseModel):
    id_token: str