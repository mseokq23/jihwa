#!/usr/bin/env python3
"""
Stable Diffusion 이미지 생성기 (사이클용)

프롬프트 기반으로 Stable Diffusion 모델을 사용하여 이미지를 생성합니다.
OnnxStream을 통해 실행됩니다.
순번이 매겨진 파일명으로 저장하고 50개 초과 시 순환 덮어쓰기를 지원합니다.
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import logging
from typing import List, Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_prompts(prompt_file: str) -> List[List[str]]:
    """
    프롬프트 파일에서 프롬프트 집합을 로드합니다.
    
    Args:
        prompt_file: 프롬프트가 저장된 JSON 파일 경로
        
    Returns:
        프롬프트 조각의 중첩 리스트
    """
    with open(prompt_file, 'r', encoding='utf-8') as file:
        return json.load(file)


def generate_prompt(prompts: List[List[str]], custom_prompt: str = "") -> str:
    """
    프롬프트 조각을 결합하여 최종 프롬프트를 생성합니다.
    
    Args:
        prompts: 프롬프트 조각의 중첩 리스트
        custom_prompt: 사용자 정의 프롬프트 (있을 경우 prompts를 대체)
        
    Returns:
        생성된 최종 프롬프트 문자열
    """
    if custom_prompt:
        return custom_prompt
    
    # 각 프롬프트 집합에서 무작위로 하나의 항목 선택
    return ' '.join(random.choice(fragments) for fragments in prompts)


def generate_image(
    sd_path: str,
    model_path: str,
    prompt: str,
    output_path: str,
    width: int,
    height: int,
    steps: int,
    seed: int
) -> None:
    """
    Stable Diffusion 명령을 구성하고 실행하여 이미지를 생성합니다.
    
    Args:
        sd_path: Stable Diffusion 실행 파일 경로
        model_path: 모델 파일 경로
        prompt: 이미지 생성에 사용할 프롬프트
        output_path: 출력 이미지 경로
        width: 이미지 너비
        height: 이미지 높이
        steps: 추론 스텝 수
        seed: 랜덤 시드
    """
    # 명령어 구성
    cmd = [
        sd_path,
        "--xl", "--turbo",
        "--models-path", model_path,
        "--rpi-lowmem",
        "--prompt", prompt,
        "--seed", str(seed),
        "--output", output_path,
        "--steps", str(steps),
        "--res", f"{width}x{height}"
    ]
    
    # Print command execution info
    logger.info(f"Prompt: '{prompt}'")
    logger.info(f"Seed: {seed}")
    logger.info(f"Save path: {output_path}")
    
    # 명령어 실행
    subprocess.run(cmd)
    logger.info("Image generation complete")


def parse_arguments() -> Dict[str, Any]:
    """
    명령줄 인수를 파싱합니다.
    
    Returns:
        파싱된 명령줄 인수 딕셔너리
    """
    parser = argparse.ArgumentParser(description="Generate images using Stable Diffusion with cycle numbering.")
    
    parser.add_argument(
        "output_dir", 
        help="Directory to save generated images"
    )
    parser.add_argument(
        "--output-number",
        type=int,
        help="Specific output number for the image (1-50)"
    )
    parser.add_argument(
        "--prompts", 
        default="prompts/flowers.json", 
        help="Prompt file to use"
    )
    parser.add_argument(
        "--prompt", 
        default="", 
        help="Prompt to use (overrides prompt file if specified)"
    )
    parser.add_argument(
        "--seed", 
        type=int,
        default=random.randint(1, 10000), 
        help="Seed to use for image generation"
    )
    parser.add_argument(
        "--steps", 
        type=int,
        default=3, 
        help="Number of steps to perform"
    )
    parser.add_argument(
        "--width", 
        type=int,
        default=480, 
        help="Width of the generated image"
    )
    parser.add_argument(
        "--height", 
        type=int,
        default=800, 
        help="Height of the generated image"
    )
    parser.add_argument(
        "--sd", 
        default="OnnxStream/src/build/sd", 
        help="Path to Stable Diffusion executable"
    )
    parser.add_argument(
        "--model", 
        default="models/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream", 
        help="Path to Stable Diffusion model to use"
    )
    
    return vars(parser.parse_args())


def main() -> int:
    """
    메인 실행 함수
    
    Returns:
        종료 코드 (0: 성공, 1: 오류)
    """
    try:
        # 명령줄 인수 파싱
        args = parse_arguments()
        
        # 출력 디렉터리 확인
        output_dir = args["output_dir"]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        # 프롬프트 생성
        try:
            prompts = load_prompts(args["prompts"])
            prompt = generate_prompt(prompts, args["prompt"])
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            return 1
        
        # 출력 파일명 결정
        if args["output_number"]:
            # 특정 번호로 저장 (사이클용)
            output_filename = f"output{args['output_number']}.png"
            logger.info(f"Cycle mode: saving as {output_filename}")
        else:
            # 기존 방식 (일반 사용 시)
            unique_arg = f"{prompt.replace(' ', '_')}_seed_{args['seed']}_steps_{args['steps']}"
            output_filename = f"{unique_arg}.png"
            logger.info(f"Manual mode: saving as {output_filename}")
        
        output_path = os.path.join(output_dir, output_filename)
        logger.info(f"Output file: {output_path}")
        
        # 이미지 생성
        try:
            generate_image(
                sd_path=args["sd"],
                model_path=args["model"],
                prompt=prompt,
                output_path=output_path,
                width=args["width"],
                height=args["height"],
                steps=args["steps"],
                seed=args["seed"]
            )
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return 1
        
        # 생성 확인
        if not os.path.exists(output_path):
            logger.error(f"Generated image not found: {output_path}")
            return 1
        
        # output.png로도 복사 (호환성 유지)
        shared_file = 'output.png'
        shared_fullpath = os.path.join(output_dir, shared_file)
        try:
            shutil.copyfile(output_path, shared_fullpath)
            logger.info(f"Image also copied to: {shared_fullpath}")
        except Exception as e:
            logger.warning(f"Failed to copy to output.png: {e}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
