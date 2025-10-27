"""
JPype 환경 설정 유틸리티
extract.py 모듈화를 위한 공통 설정 함수
"""

import os
import sys
import subprocess


def setup_java_home():
    """
    JAVA_HOME 환경변수를 자동으로 설정
    이미 설정되어 있으면 그대로 사용
    """
    if 'JAVA_HOME' in os.environ:
        java_home = os.environ['JAVA_HOME']
        # jvm.dll이 실제로 존재하는지 확인
        jvm_dll = os.path.join(java_home, 'bin', 'server', 'jvm.dll')
        if os.path.exists(jvm_dll):
            return java_home
    
    # Windows에서 자동으로 Java 찾기
    # 방법 1: java -XshowSettings:properties로 실제 Java 경로 찾기
    try:
        result = subprocess.run(
            'java -XshowSettings:properties',
            shell=True,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr
        
        for line in output.split('\n'):
            if 'java.home' in line and '=' in line:
                # "    java.home = C:\Program Files\Java\jdk-21"
                java_home = line.split('=', 1)[1].strip()
                
                # jvm.dll 존재 확인
                jvm_dll = os.path.join(java_home, 'bin', 'server', 'jvm.dll')
                if os.path.exists(jvm_dll):
                    os.environ['JAVA_HOME'] = java_home
                    return java_home
    except Exception as e:
        pass
    
    # 방법 2: where java로 찾기 (fallback)
    try:
        java_path = subprocess.check_output('where java', shell=True).decode().strip().split('\n')[0]
        # C:\Program Files\Java\jdk-21\bin\java.exe -> C:\Program Files\Java\jdk-21
        java_home = os.path.dirname(os.path.dirname(java_path))
        
        # jvm.dll 존재 확인
        jvm_dll = os.path.join(java_home, 'bin', 'server', 'jvm.dll')
        if os.path.exists(jvm_dll):
            os.environ['JAVA_HOME'] = java_home
            return java_home
    except:
        pass
    
    raise EnvironmentError(
        "JAVA_HOME 환경변수를 찾을 수 없습니다.\n"
        "Java JDK가 제대로 설치되어 있는지 확인하세요.\n"
        "JRE가 아닌 JDK를 설치해야 합니다: https://adoptium.net/"
    )


def init_jpype(jar_path=None):
    """
    JPype 초기화 (JAVA_HOME 설정 + JVM 시작)
    
    Args:
        jar_path: JAR 파일 경로 (옵션)
    
    Returns:
        jpype 모듈
    """
    # 1. JAVA_HOME 설정
    java_home = setup_java_home()
    
    # 2. jpype import
    try:
        import jpype
    except ImportError:
        raise ImportError(
            "JPype1이 설치되어 있지 않습니다.\n"
            "다음 명령으로 설치하세요: pip install JPype1"
        )
    
    # 3. JVM이 이미 실행 중이면 그대로 반환
    if jpype.isJVMStarted():
        return jpype
    
    # 4. JVM 시작
    try:
        if jar_path:
            jpype.startJVM(
                jpype.getDefaultJVMPath(),
                f"-Djava.class.path={jar_path}",
                convertStrings=True,
            )
        else:
            jpype.startJVM(jpype.getDefaultJVMPath())
        
        return jpype
    
    except Exception as e:
        raise RuntimeError(
            f"JVM 시작 실패: {e}\n"
            f"JAVA_HOME: {java_home}\n"
            "Python과 Java의 비트 버전(32/64bit)이 일치하는지 확인하세요."
        )


def get_java_info():
    """
    현재 Java 환경 정보 반환
    
    Returns:
        dict: Java 버전, 경로 등
    """
    info = {
        'java_home': os.environ.get('JAVA_HOME', 'Not set'),
        'java_version': None,
        'java_path': None
    }
    
    try:
        java_version = subprocess.check_output(
            'java -version', 
            stderr=subprocess.STDOUT, 
            shell=True
        ).decode()
        info['java_version'] = java_version.split('\n')[0]
    except:
        info['java_version'] = 'Not found'
    
    try:
        java_path = subprocess.check_output('where java', shell=True).decode().strip().split('\n')[0]
        info['java_path'] = java_path
    except:
        info['java_path'] = 'Not found'
    
    return info


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("JPype 환경 설정 테스트")
    print("=" * 60)
    
    # Java 정보 확인
    info = get_java_info()
    print(f"\nJava 정보:")
    print(f"  JAVA_HOME: {info['java_home']}")
    print(f"  Java 버전: {info['java_version']}")
    print(f"  Java 경로: {info['java_path']}")
    
    # JAVA_HOME 설정 테스트
    try:
        java_home = setup_java_home()
        print(f"\n[성공] JAVA_HOME 설정: {java_home}")
    except Exception as e:
        print(f"\n[오류] JAVA_HOME 설정 실패: {e}")
        sys.exit(1)
    
    # JPype 초기화 테스트
    try:
        jpype = init_jpype()
        print(f"[성공] JPype 초기화 완료")
        print(f"       JPype 버전: {jpype.__version__}")
        print(f"       JVM 실행 중: {jpype.isJVMStarted()}")
    except Exception as e:
        print(f"[오류] JPype 초기화 실패: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("모든 테스트 통과!")
    print("=" * 60)

