import os
import subprocess
import time
import sys

IMAGE_PATH = "image_dir/output.png"
IMAGE_DIR = "image_dir"
DISPLAY_CMD = ["python3", "src/display_picture.py", IMAGE_PATH]
GENERATE_CMD = ["python3", "src/generate_picture.py", IMAGE_DIR]
SLEEP_AFTER_DISPLAY = 300      # 5분
SLEEP_AFTER_GENERATE = 3600    # 1시간

def display_image():
    if not os.path.exists(IMAGE_PATH):
        print(f"[ERROR] Image file not found: {IMAGE_PATH}", file=sys.stderr)
        return False
    try:
        result = subprocess.run(DISPLAY_CMD, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error outputting image: {e}", file=sys.stderr)
        return False

def generate_image():
    try:
        result = subprocess.run(GENERATE_CMD, check=True)
        if not os.path.exists(IMAGE_PATH):
            print(f"[ERROR] File not found after image creation: {IMAGE_PATH}", file=sys.stderr)
            return False
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error creating image: {e}", file=sys.stderr)
        return False

def main():
    # 최초 display
    if not display_image():
        return
    time.sleep(SLEEP_AFTER_DISPLAY)

    # 최초 generate
    if not generate_image():
        return

    while True:
        time.sleep(SLEEP_AFTER_GENERATE)
        if not display_image():
            break
        time.sleep(SLEEP_AFTER_DISPLAY)
        if not generate_image():
            break

if __name__ == "__main__":
    main()
