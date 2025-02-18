from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid

class ResponseModel(BaseModel):
    message: str
    data: Optional[Dict] = None
