

from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import config
from loguru import logger
import re


class DocumentChunker:
    """문서 청킹 클래스"""
    
    def __init__(
        self,
        chunk_size: int = config.CHUNK_SIZE,
        chunk_overlap: int = config.CHUNK_OVERLAP,
        separators: List[str] = None
    ):
        """
        Args:
            chunk_size: 청크 크기 (토큰)
            chunk_overlap: 청크 간 겹침 (토큰)
            separators: 구분자 리스트
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or config.SEPARATORS
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
        )
        
        logger.info(f"DocumentChunker 초기화: chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def _find_structure_context(self, text: str, chunk_start: int, chunk_end: int) -> Dict:
        """
        청크의 위치를 기반으로 해당 청크가 속한 문서 구조 찾기
        
        Args:
            text: 전체 문서 텍스트
            chunk_start: 청크 시작 위치
            chunk_end: 청크 끝 위치
        
        Returns:
            구조 메타데이터 dict
        """
        # 청크 앞부분의 텍스트에서 가장 가까운 장/조 찾기
        text_before = text[:chunk_start]
        
        # 패턴 정의
        chapter_pattern = re.compile(r'제\s*(\d+)\s*장\s+(.+)')
        article_pattern = re.compile(r'제\s*(\d+)\s*조\s*(?:\((.+?)\))?')
        
        # 역순으로 검색 (가장 가까운 것 찾기)
        lines_before = text_before.split('\n')
        
        current_chapter = None
        current_chapter_title = ""
        current_article = None
        current_article_title = ""
        
        # 뒤에서부터 검색
        for line in reversed(lines_before):
            line = line.strip()
            
            # 조 찾기
            if current_article is None:
                article_match = article_pattern.search(line)
                if article_match:
                    current_article = article_match.group(1)
                    current_article_title = article_match.group(2) if article_match.group(2) else ""
            
            # 장 찾기
            if current_chapter is None:
                chapter_match = chapter_pattern.search(line)
                if chapter_match:
                    current_chapter = chapter_match.group(1)
                    current_chapter_title = chapter_match.group(2).strip()
            
            # 둘 다 찾으면 중단
            if current_chapter and current_article:
                break
        
        # 계층 경로 생성
        hierarchy_parts = []
        if current_chapter:
            if current_chapter_title:
                hierarchy_parts.append(f"제{current_chapter}장 {current_chapter_title}")
            else:
                hierarchy_parts.append(f"제{current_chapter}장")
        
        if current_article:
            if current_article_title:
                hierarchy_parts.append(f"제{current_article}조 ({current_article_title})")
            else:
                hierarchy_parts.append(f"제{current_article}조")
        
        return {
            'chapter_number': current_chapter or "",
            'chapter_title': current_chapter_title,
            'article_number': current_article or "",
            'article_title': current_article_title,
            'hierarchy_path': " > ".join(hierarchy_parts) if hierarchy_parts else ""
        }
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict = None
    ) -> List[Document]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 입력 텍스트
            metadata: 메타데이터 (문서명, 섹션 등)
        
        Returns:
            Document 리스트
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트 입력")
            return []
        
        # 메타데이터 기본값
        if metadata is None:
            metadata = {}
        
        # 청크 생성
        chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[metadata]
        )
        
        # 각 청크에 구조 메타데이터 추가
        current_pos = 0
        for i, chunk in enumerate(chunks):
            # 청크의 텍스트 위치 찾기
            chunk_text = chunk.page_content
            chunk_start = text.find(chunk_text, current_pos)
            chunk_end = chunk_start + len(chunk_text) if chunk_start != -1 else current_pos
            
            # 기본 청크 메타데이터
            chunk.metadata['chunk_id'] = i
            chunk.metadata['chunk_index'] = i
            chunk.metadata['chunk_size'] = len(chunk_text)
            
            # 문서 구조 메타데이터 추가
            if chunk_start != -1:
                structure_context = self._find_structure_context(text, chunk_start, chunk_end)
                chunk.metadata.update(structure_context)
                current_pos = chunk_end
            else:
                # 위치를 찾지 못한 경우 빈 구조 정보
                chunk.metadata.update({
                    'chapter_number': "",
                    'chapter_title': "",
                    'article_number': "",
                    'article_title': "",
                    'hierarchy_path': ""
                })
        
        logger.info(f"텍스트 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks
    
    def chunk_documents(
        self,
        documents: List[Dict]
    ) -> List[Document]:
        """
        여러 문서를 청크로 분할
        
        Args:
            documents: 문서 리스트 [{"text": str, "metadata": dict}, ...]
        
        Returns:
            Document 리스트
        """
        all_chunks = []
        
        for doc_idx, doc in enumerate(documents):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            metadata['doc_idx'] = doc_idx
            
            chunks = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        
        logger.info(f"전체 문서 청킹 완료: {len(documents)}개 문서 → {len(all_chunks)}개 청크")
        return all_chunks
    
    def chunk_with_tables(
        self,
        text: str,
        tables: List[Dict],
        metadata: Dict = None
    ) -> List[Document]:
        """
        텍스트와 표를 함께 청크로 분할
        표는 별도 청크로 생성
        
        Args:
            text: 입력 텍스트
            tables: 표 리스트 [{"summary": str, "rows": [[str]], ...}, ...]
            metadata: 메타데이터
        
        Returns:
            Document 리스트
        """
        if metadata is None:
            metadata = {}
        
        chunks = []
        
        # 1. 일반 텍스트 청킹
        text_chunks = self.chunk_text(text, metadata)
        chunks.extend(text_chunks)
        
        # 2. 표 청킹 (각 표는 별도 청크)
        for table_idx, table in enumerate(tables):
            table_content = self._format_table(table)
            table_metadata = metadata.copy()
            table_metadata['type'] = 'table'
            table_metadata['table_idx'] = table_idx
            table_metadata['table_summary'] = table.get('summary', '')
            
            table_doc = Document(
                page_content=table_content,
                metadata=table_metadata
            )
            chunks.append(table_doc)
        
        logger.info(f"텍스트+표 청킹 완료: 텍스트 {len(text_chunks)}개 + 표 {len(tables)}개")
        return chunks
    
    def _format_table(self, table: Dict) -> str:
        """
        표를 텍스트 형식으로 변환
        
        Args:
            table: 표 데이터
        
        Returns:
            포맷된 텍스트
        """
        lines = []
        
        # 표 요약
        if 'summary' in table:
            lines.append(f"[{table['summary']}]")
            lines.append("")
        
        # 표 내용
        rows = table.get('rows', [])
        if rows:
            # 헤더 (첫 행)
            if len(rows) > 0:
                lines.append(" | ".join(rows[0]))
                lines.append("-" * (len(" | ".join(rows[0]))))
            
            # 데이터 행
            for row in rows[1:]:
                lines.append(" | ".join(row))
        
        return "\n".join(lines)


def test_chunker():
    """청킹 테스트"""
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    # 테스트 텍스트
    text = """
    2024년 디지털정부 발전유공 포상 추진계획
    
    1. 목적
    디지털정부 발전에 기여한 공무원 및 민간인의 노력을 격려하고,
    우수 사례를 발굴하여 확산하기 위함
    
    2. 포상 개요
    - 대상: 공무원, 민간인
    - 규모: 총 50명 내외
    - 시기: 2024년 12월
    """
    
    metadata = {
        "doc_name": "포상_추진계획.hwpx",
        "section": "전체"
    }
    
    chunks = chunker.chunk_text(text, metadata)
    
    print(f"\n=== 청킹 테스트 결과 ===")
    print(f"생성된 청크 수: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n[청크 {i+1}]")
        print(f"내용: {chunk.page_content[:100]}...")
        print(f"메타데이터: {chunk.metadata}")


if __name__ == "__main__":
    test_chunker()

