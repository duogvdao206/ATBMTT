from crypto_utils import generate_rsa_keys
import os

if __name__ == "__main__":
    if not os.path.exists("sender_private.pem"):
        print("Generating Sender Keys...")
        generate_rsa_keys("sender")
    if not os.path.exists("receiver_private.pem"):
        print("Generating Receiver Keys...")
        generate_rsa_keys("receiver")
    print("Keys generated successfully.")
