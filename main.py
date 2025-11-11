"""
RAG 시스템 메인 실행 파일
CLI 인터페이스
"""

# ⚠️ 환경변수는 모든 import 이전에 설정해야 함
import os
os.environ["ORT_LOGGING_LEVEL"] = "3"  # ONNX Runtime GPU 경고 비활성화
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # TensorFlow 경고 비활성화

import argparse
from pathlib import Path
from loguru import logger
import config
from rag.pipeline import RAGPipeline


def setup_logging():
    """로깅 설정"""
    logger.add(
        config.LOG_FILE,
        rotation="10 MB",
        level=config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        encoding='utf-8'
    )


def add_documents(pipeline: RAGPipeline, extracted_dir: Path = None):
    """문서 추가"""
    if extracted_dir:
        # 특정 문서 추가
        pipeline.add_document_from_extract(extracted_dir)
        print(f"✓ 문서 추가 완료: {extracted_dir.name}")
    else:
        # 전체 일괄 추가
        pipeline.add_documents_batch()
        print(f"✓ 전체 문서 일괄 추가 완료")
    
    # 통계 출력
    stats = pipeline.get_stats()
    print(f"\n현재 시스템 상태:")
    print(f"  - 총 문서 수: {stats['vector_store']['total_documents']}")
    print(f"  - 임베딩 모델: {stats['embedding_model']}")
    print(f"  - LLM 모델: {stats['llm_model']}")


def query(pipeline: RAGPipeline, question: str):
    """질의응답"""
    print(f"\n질문: {question}")
    print("=" * 60)
    
    result = pipeline.query(question)
    
    print(f"\n답변:")
    print(result['answer'])
    
    if result.get('sources'):
        print(f"\n출처:")
        for source in result['sources']:
            print(f"  - {source['doc_name']} (청크 {source['chunk_id']})")
    
    print(f"\n처리 시간: {result['processing_time']:.2f}초")


def interactive(pipeline: RAGPipeline):
    """대화형 모드"""
    print("\n" + "=" * 60)
    print("RAG 시스템 대화형 모드")
    print("=" * 60)
    print("명령어:")
    print("  - 질문 입력: 답변 생성")
    print("  - 'stats': 시스템 통계")
    print("  - 'quit' 또는 'exit': 종료")
    print("=" * 60 + "\n")
    
    stats = pipeline.get_stats()
    print(f"시스템 준비 완료 (문서 {stats['vector_store']['total_documents']}개)\n")
    
    while True:
        try:
            question = input("\n질문> ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', '종료']:
                print("종료합니다.")
                break
            
            if question.lower() == 'stats':
                stats = pipeline.get_stats()
                print(f"\n시스템 통계:")
                print(f"  - 총 문서 수: {stats['vector_store']['total_documents']}")
                print(f"  - 임베딩 차원: {stats['vector_store']['embedding_dim']}")
                print(f"  - 임베딩 모델: {stats['embedding_model']}")
                print(f"  - LLM 모델: {stats['llm_model']}")
                continue
            
            # 답변 생성
            result = pipeline.query(question, return_sources=True)
            
            print(f"\n답변:")
            print(result['answer'])
            
            if result.get('sources'):
                print(f"\n출처:")
                for source in result['sources'][:3]:  # 상위 3개만
                    print(f"  - {source['doc_name']} (score: {source['score']:.4f})")
        
        except KeyboardInterrupt:
            print("\n\n종료합니다.")
            break
        except Exception as e:
            print(f"\n오류: {e}")
            logger.error(f"Interactive mode error: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="RAG 시스템 CLI")
    
    subparsers = parser.add_subparsers(dest='command', help='명령어')
    
    # add 명령어
    add_parser = subparsers.add_parser('add', help='문서 추가')
    add_parser.add_argument(
        '--dir',
        type=str,
        help='추출된 문서 디렉토리 (없으면 전체 일괄 추가)'
    )
    
    # query 명령어
    query_parser = subparsers.add_parser('query', help='질의응답')
    query_parser.add_argument('question', type=str, help='질문')
    
    # interactive 명령어
    subparsers.add_parser('interactive', help='대화형 모드')
    
    # stats 명령어
    subparsers.add_parser('stats', help='시스템 통계')
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging()
    
    # 파이프라인 초기화
    try:
        pipeline = RAGPipeline(load_existing=True)
    except Exception as e:
        logger.error(f"파이프라인 초기화 실패: {e}")
        print(f"오류: {e}")
        print("\nOpenAI API 키를 확인하세요:")
        print("  1. .env 파일에 OPENAI_API_KEY 추가")
        print("  2. 또는 환경변수로 설정: export OPENAI_API_KEY='your-key'")
        return
    
    # 명령어 실행
    if args.command == 'add':
        extracted_dir = Path(args.dir) if args.dir else None
        add_documents(pipeline, extracted_dir)
    
    elif args.command == 'query':
        query(pipeline, args.question)
    
    elif args.command == 'interactive':
        interactive(pipeline)
    
    elif args.command == 'stats':
        stats = pipeline.get_stats()
        print(f"\n시스템 통계:")
        print(f"  - 총 문서 수: {stats['vector_store']['total_documents']}")
        print(f"  - 임베딩 차원: {stats['vector_store']['embedding_dim']}")
        print(f"  - 인덱스 타입: {stats['vector_store']['index_type']}")
        print(f"  - 임베딩 모델: {stats['embedding_model']}")
        print(f"  - LLM 모델: {stats['llm_model']}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

