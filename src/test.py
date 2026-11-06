import pyotp
totp = pyotp.TOTP("E3GKK6POTZFIZVO5UPEUJKQO7CIB36UL")
print(totp.now())
print("Current OTP:", totp.verify(233217))

otp = totp.now()
print(pyotp.TOTP("E3GKK6POTZFIZVO5UPEUJKQO7CIB36UL").verify(otp))