# otp_chrono_fluide.py
import time
import hashlib
import sys

# 🔑 Ton secret CGAWEB
import pyotp
import time
import sys

SECRET = "23YTSR5S3ZJO5SJB" 
INTERVAL = 30  # Changement du code toutes les 30 secondes

def generate_otp(secret, interval=30):
    """
    Génère un OTP TOTP valide basé sur le secret fourni.
    Compatible Google Authenticator / CGAWEB.
    """
    totp = pyotp.TOTP(secret, interval=interval)
    return totp.now()

def main():
    previous_code = None
    while True:
        otp = generate_otp(SECRET, INTERVAL)
        remaining = INTERVAL - (int(time.time()) % INTERVAL)

        if otp != previous_code:  # Nouveau code
            previous_code = otp

        # Affichage dynamique sur une seule ligne
        sys.stdout.write(f"\r💡 Code OTP : {otp} | ⏱ Temps restant : {remaining:2d}s ")
        sys.stdout.flush()
        time.sleep(1)

if __name__ == "__main__":
    main()
