import os
import subprocess
import time
import sys
import json

IMAGE_DIR = "image_dir"
COUNTER_FILE = os.path.join(IMAGE_DIR, "image_counter.json")
DISPLAY_CMD = ["python3", "src/display_picture.py"]
GENERATE_CMD = ["python3", "src/generate_picture_cycle.py", IMAGE_DIR]  # 파일명 변경
SLEEP_AFTER_DISPLAY = 300      # 5분
SLEEP_AFTER_GENERATE = 3600    # 1시간
MAX_IMAGES = 50

def load_counter():
    """이미지 카운터를 로드합니다."""
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f:
                data = json.load(f)
                return data.get('counter', 0)
        except:
            return 0
    return 0

def save_counter(counter):
    """이미지 카운터를 저장합니다."""
    try:
        os.makedirs(IMAGE_DIR, exist_ok=True)
        with open(COUNTER_FILE, 'w') as f:
            json.dump({'counter': counter}, f)
    except Exception as e:
        print(f"[ERROR] Failed to save counter: {e}", file=sys.stderr)

def get_next_counter():
    """다음 이미지 번호를 반환하고 카운터를 업데이트합니다."""
    counter = load_counter()
    next_counter = (counter % MAX_IMAGES) + 1
    save_counter(next_counter)
    return next_counter

def get_latest_image_path():
    """가장 최근에 생성된 이미지 경로를 반환합니다."""
    counter = load_counter()
    if counter == 0:
        # 아직 생성된 이미지가 없으면 기본 output.png 사용
        return os.path.join(IMAGE_DIR, "output.png")
    
    # 현재 카운터의 이미지 확인
    image_path = os.path.join(IMAGE_DIR, f"output{counter}.png")
    if os.path.exists(image_path):
        return image_path
    
    # 역순으로 기존 이미지 찾기
    for i in range(counter - 1, 0, -1):
        image_path = os.path.join(IMAGE_DIR, f"output{i}.png")
        if os.path.exists(image_path):
            return image_path
    
    # 50부터 역순으로 찾기 (순환 구조)
    for i in range(MAX_IMAGES, counter, -1):
        image_path = os.path.join(IMAGE_DIR, f"output{i}.png")
        if os.path.exists(image_path):
            return image_path
    
    # 기본값
    return os.path.join(IMAGE_DIR, "output.png")

def display_image():
    """이미지를 표시합니다."""
    image_path = get_latest_image_path()
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}", file=sys.stderr)
        return False
    
    print(f"[INFO] Displaying: {image_path}")
    try:
        cmd = DISPLAY_CMD + [image_path]
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error outputting image: {e}", file=sys.stderr)
        return False

def generate_image():
    """이미지를 생성합니다."""
    try:
        counter = get_next_counter()
        print(f"[INFO] Generating image {counter}")
        
        # 파일 경로를 명령줄 인수로 전달
        output_path = os.path.join(IMAGE_DIR, f"output{counter}.png")
        cmd = GENERATE_CMD + ["--output-number", str(counter)]
        
        result = subprocess.run(cmd, check=True)
        
        # 생성된 이미지 파일 확인
        if not os.path.exists(output_path):
            print(f"[ERROR] File not found after image creation: {output_path}", file=sys.stderr)
            return False
        
        print(f"[INFO] Generated: {output_path}")
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error creating image: {e}", file=sys.stderr)
        return False

def main():
    """메인 실행 함수"""
    # 디렉터리 생성
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    print("[INFO] Starting image cycle...")
    
    # 기존 이미지가 있으면 표시, 없으면 먼저 생성
    if load_counter() == 0:
        print("[INFO] No existing images found. Generating first image...")
        if not generate_image():
            print("[ERROR] Failed to generate initial image")
            return
    
    # 최초 display
    if not display_image():
        print("[ERROR] Failed to display image")
        return
    
    time.sleep(SLEEP_AFTER_DISPLAY)

    while True:
        # 이미지 생성
        if not generate_image():
            print("[ERROR] Failed to generate image, stopping cycle")
            break
        
        time.sleep(SLEEP_AFTER_GENERATE)
        
        # 이미지 표시
        if not display_image():
            print("[ERROR] Failed to display image, stopping cycle")
            break
        
        time.sleep(SLEEP_AFTER_DISPLAY)

if __name__ == "__main__":
    main()
