import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_utils import generate_session_key, des3_encrypt, des3_decrypt

def benchmark():
    print("--- Benchmark Triple DES ---")
    sizes = [
        (10 * 1024, "10 KB"),
        (1 * 1024 * 1024, "1 MB"),
        (10 * 1024 * 1024, "10 MB")
    ]
    
    key = generate_session_key()
    
    for size, name in sizes:
        data = os.urandom(size)
        
        start_enc = time.time()
        iv, cipher = des3_encrypt(key, data)
        end_enc = time.time()
        
        start_dec = time.time()
        pt = des3_decrypt(key, iv, cipher)
        end_dec = time.time()
        
        assert data == pt
        
        print(f"File size: {name}")
        print(f"  Encrypt time: {end_enc - start_enc:.4f} s")
        print(f"  Decrypt time: {end_dec - start_dec:.4f} s")
        print(f"  Total time:   {(end_enc - start_enc) + (end_dec - start_dec):.4f} s")
        print("-" * 30)

if __name__ == "__main__":
    benchmark()
