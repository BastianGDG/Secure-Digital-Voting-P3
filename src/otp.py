import pyotp

OTP = pyotp.random_base32()

print(pyotp.totp.TOTP(OTP).provisioning_uri(name='alice@google.com', issuer_name='MitID'))
