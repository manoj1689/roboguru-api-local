from pydantic import BaseModel

class NotificationRequest(BaseModel):
    uid: str  
    topic: str 
    title: str  
    body: str  
