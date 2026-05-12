import os
import subprocess
import time
import sys

def test_normal():
    # Ensure keys and file exist
    subprocess.run([sys.executable, "../generate_keys.py"], cwd="..")
    subprocess.run([sys.executable, "../generate_dummy_mp3.py"], cwd="..")
    
    print("\n--- Starting Normal Test ---")
    receiver = subprocess.Popen([sys.executable, "receiver.py"], cwd="..")
    time.sleep(1) # wait for receiver to start
    sender = subprocess.Popen([sys.executable, "sender.py"], cwd="..")
    
    sender.wait()
    receiver.wait()
    
    # Check if received file exists and size matches
    orig_path = "../recording.mp3"
    recv_path = "../received_recording.mp3"
    
    if os.path.exists(recv_path):
        orig_size = os.path.getsize(orig_path)
        recv_size = os.path.getsize(recv_path)
        if orig_size == recv_size:
            print("[+] test_normal: PASS")
        else:
            print("[-] test_normal: FAIL (Size mismatch)")
    else:
        print("[-] test_normal: FAIL (File not received)")

if __name__ == "__main__":
    test_normal()
