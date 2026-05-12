import os

if __name__ == "__main__":
    if not os.path.exists("recording.mp3"):
        with open("recording.mp3", "wb") as f:
            f.write(os.urandom(1024 * 1024)) # 1MB dummy file
        print("Dummy recording.mp3 created.")
    else:
        print("recording.mp3 already exists.")
