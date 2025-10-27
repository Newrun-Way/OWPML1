"""
JPype 환경 테스트 스크립트
팀원들이 extract.py를 실행하기 전에 환경을 확인하는 용도
"""

import sys
import struct
import os

print("=" * 60)
print("JPype 환경 테스트")
print("=" * 60)

# 1. Python 비트 확인
python_bits = struct.calcsize('P') * 8
print(f"Python 버전: {sys.version}")
print(f"Python 비트: {python_bits} bit")

if python_bits != 64:
    print("\n[경고] 64bit Python 사용을 권장합니다.")

# 2. Java 확인
import subprocess
try:
    java_version = subprocess.check_output('java -version', stderr=subprocess.STDOUT, shell=True).decode()
    print(f"\nJava 설치됨:")
    for line in java_version.split('\n')[:2]:
        if line.strip():
            print(f"  {line.strip()}")
    
    # Java 비트 확인
    if '64-Bit' in java_version:
        java_bits = 64
    elif '32-Bit' in java_version:
        java_bits = 32
    else:
        java_bits = "알 수 없음"
    
    print(f"  Java 비트: {java_bits} bit")
    
    if java_bits != python_bits and java_bits != "알 수 없음":
        print(f"\n[오류] Python({python_bits}bit)과 Java({java_bits}bit)의 비트가 다릅니다!")
        print("       둘 다 64bit로 설치해야 합니다.")
        sys.exit(1)
    
except Exception as e:
    print(f"\n[오류] Java가 설치되어 있지 않거나 PATH에 없습니다.")
    print(f"       {e}")
    print("\n해결방법:")
    print("  1. Java JDK 64bit 설치: https://adoptium.net/")
    print("  2. 설치 후 터미널 재시작")
    sys.exit(1)

# 3. JAVA_HOME 확인
java_home = os.environ.get('JAVA_HOME')
if java_home:
    print(f"\nJAVA_HOME: {java_home}")
    if not os.path.exists(java_home):
        print(f"[경고] JAVA_HOME 경로가 존재하지 않습니다: {java_home}")
else:
    print("\n[경고] JAVA_HOME 환경변수가 설정되지 않았습니다.")
    print("       extract.py는 자동으로 Java를 찾지만, JAVA_HOME 설정을 권장합니다.")
    
    # 자동으로 Java 경로 찾기
    try:
        java_path = subprocess.check_output('where java', shell=True).decode().strip().split('\n')[0]
        auto_java_home = os.path.dirname(os.path.dirname(java_path))
        print(f"       자동 감지된 경로: {auto_java_home}")
    except:
        pass

# 4. JPype import 테스트
print("\n" + "-" * 60)
print("JPype 테스트 시작...")
print("-" * 60)

try:
    import jpype
    print(f"\n[성공] JPype import 성공!")
    print(f"       JPype 버전: {jpype.__version__}")
    
    # 최소 버전 확인
    version_parts = jpype.__version__.split('.')
    major_version = int(version_parts[0])
    minor_version = int(version_parts[1]) if len(version_parts) > 1 else 0
    
    if major_version < 1 or (major_version == 1 and minor_version < 4):
        print(f"[경고] JPype 버전이 낮습니다. 최소 1.4.0 이상 권장합니다.")
        print(f"       현재 버전: {jpype.__version__}")
        print(f"       업그레이드: pip install --upgrade JPype1")
    
    # 5. JVM 시작 테스트
    print("\nJVM 시작 테스트 중...")
    if not jpype.isJVMStarted():
        try:
            jpype.startJVM(jpype.getDefaultJVMPath())
            print("[성공] JVM 시작 성공!")
            
            # 간단한 Java 코드 테스트
            JString = jpype.JClass("java.lang.String")
            test_string = JString("Hello from Java!")
            print(f"[성공] Java 객체 생성 성공: {test_string}")
            
            jpype.shutdownJVM()
            print("[성공] JVM 종료 성공!")
        except Exception as e:
            print(f"[오류] JVM 시작 실패:")
            print(f"       {type(e).__name__}: {e}")
            raise
    
except ImportError as e:
    print(f"\n[오류] JPype가 설치되어 있지 않습니다.")
    print(f"       {e}")
    print("\n해결방법:")
    print("  pip install JPype1")
    sys.exit(1)

except Exception as e:
    print(f"\n[오류] JPype 문제 발생:")
    print(f"  오류 유형: {type(e).__name__}")
    print(f"  오류 메시지: {e}")
    print("\n해결방법:")
    print("  1. docs/JPype_에러_해결가이드.md 참고")
    print("  2. Python과 Java가 모두 64bit인지 확인")
    print("  3. JAVA_HOME 환경변수 설정")
    print("  4. JPype 재설치: pip uninstall JPype1 -y && pip install JPype1")
    sys.exit(1)

print("\n" + "=" * 60)
print("모든 테스트 통과!")
print("extract.py를 실행할 수 있습니다.")
print("=" * 60)
print("\n사용법:")
print("  python extract.py \"hwp data/파일명.hwpx\"")
print("=" * 60)

