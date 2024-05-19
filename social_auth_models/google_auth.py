# {"sub":"101173408588151503540","name":"TamÃ¡s SzabÃ³","given_name":"TamÃ¡s","family_name":"SzabÃ³","picture":"https://lh3.googleusercontent.com/a/ACg8ocLMsXbXpWE5wq6veir5xtAUpiyyR3tcIhx84nT3bjYl8ub7EA=s96-c","email":"tamas.szabo0102@gmail.com","email_verified":true,"locale":"hu"}
from social_auth_models.social_auth import SocialUser

class GoogleUser(SocialUser):
    sub: str
    given_name: str = ""
    family_name: str = ""
    email_verified: bool = False
    locale: str = ""