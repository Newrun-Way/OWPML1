"""
LLM 모듈
GPT-4o mini를 사용한 답변 생성
"""

from typing import List, Dict
from openai import OpenAI
import config
from loguru import logger


class LLMGenerator:
    """LLM 답변 생성 클래스"""
    
    def __init__(
        self,
        api_key: str = None,
        model: str = config.LLM_MODEL,
        temperature: float = config.LLM_TEMPERATURE,
        max_tokens: int = config.LLM_MAX_TOKENS
    ):
        """
        Args:
            api_key: OpenAI API 키
            model: 모델 이름
            temperature: 온도 (0~2, 낮을수록 일관성)
            max_tokens: 최대 토큰 수
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"LLM 초기화: model={model}, temp={temperature}")
    
    def generate(
        self,
        context: str,
        question: str,
        system_prompt: str = config.SYSTEM_PROMPT
    ) -> str:
        """
        질문에 대한 답변 생성
        
        Args:
            context: 검색된 문서 컨텍스트
            question: 사용자 질문
            system_prompt: 시스템 프롬프트
        
        Returns:
            생성된 답변
        """
        # 사용자 프롬프트 구성
        user_prompt = config.USER_PROMPT_TEMPLATE.format(
            context=context,
            question=question
        )
        
        logger.info(f"답변 생성 중: {question[:50]}...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content
            
            # 사용량 로깅
            usage = response.usage
            logger.info(
                f"답변 생성 완료: "
                f"input={usage.prompt_tokens} tokens, "
                f"output={usage.completion_tokens} tokens"
            )
            
            return answer
        
        except Exception as e:
            logger.error(f"답변 생성 실패: {e}")
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    def summarize_document(
        self,
        document_text: str,
        max_tokens: int = None
    ) -> str:
        if max_tokens is None:
            max_tokens = config.SUMMARY_MAX_TOKENS
        
        # 문서 길이 제한 (토큰 절약)
        truncated_text = document_text[:2000] if len(document_text) > 2000 else document_text
        
        # 요약 프롬프트 구성
        summary_prompt = config.SUMMARY_PROMPT_TEMPLATE.format(
            document_text=truncated_text
        )
        
        logger.info(f"문서 요약 생성 중...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=config.SUMMARY_TEMPERATURE,
                max_tokens=max_tokens
            )
            
            summary = response.choices[0].message.content.strip()
            
            # 사용량 로깅
            usage = response.usage
            logger.info(
                f"요약 생성 완료: "
                f"input={usage.prompt_tokens} tokens, "
                f"output={usage.completion_tokens} tokens"
            )
            
            return summary
        
        except Exception as e:
            logger.error(f"요약 생성 실패: {e}")
            return ""
    
    def summarize_from_parsed_json(
        self,
        parsed_data: Dict,
        max_tokens: int = None
    ) -> Dict:
        """
        파싱된 JSON 데이터에서 텍스트를 추출해 요약 생성 후 JSON에 추가
    
          parsed_data: 파싱된 문서 JSON
                {
                    "doc_id": "doc_XXX",
                    "doc_name": "문서명",
                    "text_content": "전체 텍스트 내용",
                    "metadata": {...}
                }
            max_tokens: 최대 토큰 수 (기본값: config.SUMMARY_MAX_TOKENS)
        
        Returns:
            요약이 추가된 JSON
                {
                    "doc_id": "doc_XXX",
                    "doc_name": "문서명",
                    "text_content": "전체 텍스트 내용",
                    "metadata": {...},
                    "summary": "LLM이 생성한 3-4줄 요약"  ← 추가됨
                }
        """
        if max_tokens is None:
            max_tokens = config.SUMMARY_MAX_TOKENS
        
        # JSON에서 텍스트 추출
        text_content = parsed_data.get("text_content", "")
        
        if not text_content:
            logger.warning("parsed_data에 text_content가 없습니다")
            parsed_data["summary"] = ""
            return parsed_data
        
        logger.info(f"파싱된 JSON에서 요약 생성 중: {parsed_data.get('doc_name', 'Unknown')}")
        
        # 요약 생성
        summary = self.summarize_document(text_content, max_tokens)
        
        # 응답 JSON에 summary 필드 추가
        response = parsed_data.copy()
        response["summary"] = summary
        
        logger.info(f"요약이 JSON에 추가됨: {len(summary)} 글자")
        
        return response
    
    def generate_with_sources(
        self,
        contexts: List[Dict],
        question: str
    ) -> Dict[str, any]:
        """
        출처 정보를 포함한 답변 생성
        
        Args:
            contexts: 검색된 문서 리스트 [{"content": str, "metadata": dict, "score": float}, ...]
            question: 사용자 질문
        
        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "context_used": str
            }
        """
        # 컨텍스트 포맷팅
        context_parts = []
        for i, ctx in enumerate(contexts):
            content = ctx['content']
            metadata = ctx.get('metadata', {})
            doc_name = metadata.get('doc_name', '알 수 없음')
            hierarchy_path = metadata.get('hierarchy_path', '')
            
            # 구조 정보가 있으면 포함
            doc_header = f"[문서 {i+1}: {doc_name}]"
            if hierarchy_path:
                doc_header += f"\n[위치: {hierarchy_path}]"
            
            context_parts.append(f"{doc_header}\n{content}")
        
        context_str = "\n\n".join(context_parts)
        
        # 답변 생성
        answer = self.generate(context_str, question)
        
        # 출처 정보 구성 (구조 메타데이터 포함)
        sources = []
        for i, ctx in enumerate(contexts):
            metadata = ctx.get('metadata', {})
            source_info = {
                'index': i + 1,
                'doc_name': metadata.get('doc_name', '알 수 없음'),
                'doc_id': metadata.get('doc_id', ''),
                'chunk_id': metadata.get('chunk_id', -1),
                'chunk_index': metadata.get('chunk_index', -1),
                'score': ctx.get('score', 0.0),
                'content_preview': ctx['content'][:200] + "...",  # 일부만 포함
                # 문서 구조 정보
                'chapter_number': metadata.get('chapter_number', ''),
                'chapter_title': metadata.get('chapter_title', ''),
                'article_number': metadata.get('article_number', ''),
                'article_title': metadata.get('article_title', ''),
                'hierarchy_path': metadata.get('hierarchy_path', ''),
                # 사용자/프로젝트 정보 (향후 프론트엔드에서 입력)
                'user_id': metadata.get('user_id', ''),
                'dept_id': metadata.get('dept_id', ''),
                'project_id': metadata.get('project_id', '')
            }
            sources.append(source_info)
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': context_str
        }


def test_llm():
    """LLM 테스트"""
    import os
    
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY 환경변수를 설정해주세요")
        print("예: export OPENAI_API_KEY='your-api-key'")
        return
    
    llm = LLMGenerator()
    
    # 테스트 컨텍스트
    context = """
    [문서: 2024년 디지털정부 발전유공 포상 추진계획]
    
    1. 포상 대상
    - 공무원: 디지털정부 구축 및 운영에 기여한 중앙부처 및 지방자치단체 공무원
    - 민간인: 디지털정부 발전에 기여한 민간 전문가 및 기업 관계자
    
    2. 포상 규모
    - 총 50명 내외
    - 정부포상(대통령, 국무총리, 장관 표창) 30명
    - 기관장 표창 20명
    
    3. 선발 기준
    - 디지털정부 서비스 개선 우수 사례
    - 행정 효율성 향상 기여도
    - 국민 만족도 제고 실적
    """
    
    question = "포상 대상자는 누구인가요?"
    
    print(f"\n=== LLM 테스트 ===")
    print(f"질문: {question}\n")
    
    answer = llm.generate(context, question)
    print(f"답변:\n{answer}")
    
    # 출처 포함 테스트
    contexts = [
        {
            'content': context,
            'metadata': {'doc_name': '포상_추진계획.hwpx', 'chunk_id': 0},
            'score': 0.15
        }
    ]
    
    print(f"\n\n=== 출처 포함 테스트 ===")
    result = llm.generate_with_sources(contexts, question)
    print(f"답변:\n{result['answer']}")
    print(f"\n출처:")
    for source in result['sources']:
        print(f"  - {source['doc_name']} (score: {source['score']:.4f})")


if __name__ == "__main__":
    test_llm()

