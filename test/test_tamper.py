import subprocess
import time
import sys

def test_tamper():
    print("\n--- Starting Tamper Test ---")
    receiver = subprocess.Popen([sys.executable, "receiver.py"], cwd="..")
    time.sleep(1)
    
    sender = subprocess.Popen([sys.executable, "sender.py", "--tamper"], cwd="..")
    
    sender.wait()
    receiver.wait()
    
    print("[+] test_tamper: FINISHED. Check logs and output to confirm NACK on Hash mismatch.")

if __name__ == "__main__":
    test_tamper()
