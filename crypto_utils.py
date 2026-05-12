import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import DES3, PKCS1_OAEP
from Crypto.Hash import SHA512
from Crypto.Signature import pss
from Crypto.Util.Padding import pad, unpad

def generate_rsa_keys(filename_prefix):
    key = RSA.generate(2048)
    private_key = key.export_key()
    with open(f"{filename_prefix}_private.pem", "wb") as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open(f"{filename_prefix}_public.pem", "wb") as f:
        f.write(public_key)

def load_rsa_key(filename):
    with open(filename, "rb") as f:
        return RSA.import_key(f.read())

def rsa_encrypt(public_key, data):
    cipher_rsa = PKCS1_OAEP.new(public_key, hashAlgo=SHA512.new())
    return cipher_rsa.encrypt(data)

def rsa_decrypt(private_key, enc_data):
    cipher_rsa = PKCS1_OAEP.new(private_key, hashAlgo=SHA512.new())
    return cipher_rsa.decrypt(enc_data)

def rsa_sign(private_key, data):
    h = SHA512.new(data)
    signature = pss.new(private_key).sign(h)
    return signature

def rsa_verify(public_key, data, signature):
    h = SHA512.new(data)
    verifier = pss.new(public_key)
    try:
        verifier.verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False

def generate_session_key():
    return DES3.adjust_key_parity(os.urandom(24))

def des3_encrypt(key, data):
    iv = os.urandom(8)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(data, DES3.block_size))
    return iv, ct_bytes

def des3_decrypt(key, iv, ct_bytes):
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct_bytes), DES3.block_size)
    return pt

def calculate_hash(iv, ciphertext):
    h = SHA512.new()
    h.update(iv + ciphertext)
    return h.digest()
