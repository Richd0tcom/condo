

from pydantic import EmailStr, Field


class CreateOrganization:
    org_name: str
    domain: str
    slug: str

    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)


class UpdateOrganizationSettings:
    pass

class EnableFeature:
    pass

