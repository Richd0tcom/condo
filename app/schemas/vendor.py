from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Dict


# Generic Error Response
class VendorErrorResponse(BaseModel):
    status: str
    error_code: str
    message: str



class SlackInviteUserResponses(BaseModel):
    success_response: SlackInviteUserSuccessResponse
    error_response: Optional[VendorErrorResponse] = None

class VendorIntegrationResponses(BaseModel):
    pass
