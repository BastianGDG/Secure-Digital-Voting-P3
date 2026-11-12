import pyotp
totp = pyotp.TOTP("7K6JTZ763GKK64PNQIMCMZSZ3SVUD2SS")
print(totp.now())
print("Current OTP:", totp.verify(233217))

otp = "123123"
print(pyotp.TOTP("7K6JTZ763GKK64PNQIMCMZSZ3SVUD2SS").verify(otp))