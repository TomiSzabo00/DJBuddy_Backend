from pydantic import BaseModel

class SocialUser(BaseModel):
    name: str = ""
    email: str = ""
    picture_url: str = ""
    