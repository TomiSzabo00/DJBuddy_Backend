from enum import Enum

class ErrorCode(Enum):
    UNDEFINED = 0
    SESSION_EXPIRED = 1
    INCORRECT_EMAIL_PASSWORD = 2
    EMAIL_ALREADY_IN_USE = 3
    NOT_VERIFIED = 4
    WRONG_VERIFICATION_CODE = 5
    NOT_FOUND = 6
    NOT_ENOUGH_MONEY = 7
    DUPLICATE_ENTRY = 8

class CustomError(Exception):
    def __init__(self, message: str, error_code: ErrorCode):
        self.message = message
        self.status_code = error_code

    def to_dict(self):
        return {
            'message': self.message,
            'error_code': self.status_code.value
        }

class APIError(Enum):
    incorrectEmailOrPassword = CustomError(
        message="Incorrect email or password",
        error_code=ErrorCode.INCORRECT_EMAIL_PASSWORD,
    ).to_dict()
    
    sessionExpired = CustomError(
        message="Session expired",
        error_code=ErrorCode.SESSION_EXPIRED,
    ).to_dict()
    
    emailAlreadyInUse = CustomError(
        message="Email already in use",
        error_code=ErrorCode.EMAIL_ALREADY_IN_USE,
    ).to_dict()

    notVerified = CustomError(
        message="Account not verified",
        error_code=ErrorCode.NOT_VERIFIED,
    ).to_dict()

    verificationFailed = CustomError(
        message="Verification code is incorrect",
        error_code=ErrorCode.WRONG_VERIFICATION_CODE,
    ).to_dict()

    userNotFound = CustomError(
        message="User not found",
        error_code=ErrorCode.NOT_FOUND,
    ).to_dict()

    notEnoughMoney = CustomError(
        message="Your balance is not enough to make this transaction",
        error_code=ErrorCode.NOT_ENOUGH_MONEY,
    ).to_dict()

    songNotFound = CustomError(
        message="Song not found",
        error_code=ErrorCode.NOT_FOUND,
    ).to_dict()

    eventNotFound = CustomError(
        message="Event not found",
        error_code=ErrorCode.NOT_FOUND,
    ).to_dict()

    playlistNotFound = CustomError(
        message="Playlist not found",
        error_code=ErrorCode.NOT_FOUND,
    ).to_dict()

    songAlreadyExists = CustomError(
        message="This song was added already",
        error_code=ErrorCode.DUPLICATE_ENTRY,
    ).to_dict()

    def general(self, message: str):
        return CustomError(
            message=message,
            error_code=ErrorCode.UNDEFINED,
        ).to_dict()
