"""
JPype 초기화 설정
- JVM 설정 및 초기화
- HWP 파일 처리를 위한 Java 환경 구성
"""

import jpype
import jpype.imports
from jpype.types import *
import os
from pathlib import Path


def init_jpype():
    """
    JPype 초기화
    - JVM이 실행 중이면 스킵
    - 필요한 JAR 파일 로드
    """
    # JVM이 이미 시작됨
    if jpype.isJVMStarted():
        return
    
    try:
        # 현재 파일 디렉토리 기준으로 JAR 파일 경로 설정
        current_dir = Path(__file__).parent
        jar_paths = [
            current_dir / "python-hwpxlib" / "hwpxlib-1.0.5.jar",
            current_dir / "python-hwplib" / "hwplib-1.1.8.jar",
        ]
        
        # 존재하는 JAR 파일만 필터링
        existing_jars = [str(jar) for jar in jar_paths if jar.exists()]
        
        if not existing_jars:
            print("[경고] JAR 파일을 찾을 수 없습니다. HWP 파일 처리 기능이 제한될 수 있습니다.")
            # JVM 시작 (JAR 없이)
            jpype.startJVM(classpath=[])
            return
        
        # JVM 시작 (클래스패스에 JAR 추가)
        jpype.startJVM(classpath=existing_jars)
        print(f"[JPype] JVM 초기화 완료 (JAR: {len(existing_jars)}개)")
        
    except Exception as e:
        print(f"[경고] JPype 초기화 실패: {e}")
        print("[정보] HWP 파일 처리 기능이 제한될 수 있습니다.")


def shutdown_jpype():
    """JPype 종료"""
    if jpype.isJVMStarted():
        try:
            jpype.shutdownJVM()
            print("[JPype] JVM 종료 완료")
        except Exception as e:
            print(f"[경고] JPype 종료 중 오류: {e}")


if __name__ == "__main__":
    init_jpype()
    print("JPype 초기화 테스트 완료")
    shutdown_jpype()

