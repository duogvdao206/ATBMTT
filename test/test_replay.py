import subprocess
import time
import sys

def test_replay():
    print("\n--- Starting Replay Test ---")
    receiver = subprocess.Popen([sys.executable, "receiver.py"], cwd="..")
    time.sleep(1)
    
    sender = subprocess.Popen([sys.executable, "sender.py", "--replay"], cwd="..")
    
    sender.wait()
    receiver.wait()
    
    print("[+] test_replay: FINISHED. Check logs to confirm NACK on Timestamp expired.")

if __name__ == "__main__":
    test_replay()
