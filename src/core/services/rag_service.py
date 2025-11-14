"""
RAG (Retrieval-Augmented Generation) Service Module

이 모듈은 RAG 시스템을 제공합니다.
Vector DB에서 관련 문서를 검색하고, LLM과 결합하여 답변을 생성합니다.
"""

from src.core.services.vector_db_service import VectorDBService, get_vector_db_service
from src.core.services.llm_service import AzureOpenAIService, get_llm_service
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)


class RAGService:
    """RAG (Retrieval-Augmented Generation) 서비스"""

    def __init__(
        self,
        vector_db: Optional[VectorDBService] = None,
        llm_service: Optional[AzureOpenAIService] = None
    ):
        """
        Initialize RAG Service

        Args:
            vector_db: VectorDBService 인스턴스 (선택적)
            llm_service: AzureOpenAIService 인스턴스 (선택적)
        """
        self.vector_db = vector_db or get_vector_db_service()
        self.llm_service = llm_service or get_llm_service()

        # Collection names mapping
        self.collection_names = {
            "manuals": "system_manuals",
            "incidents": "incident_history",
            "schemas": "database_schemas",
            "contacts": "contact_information",
            "sop": "sop_procedures"
        }

        logger.info("RAGService initialized")

    def initialize_collections(self, vector_size: int = 1536):
        """
        모든 RAG 컬렉션 초기화

        Args:
            vector_size: 벡터 차원 (기본: 1536)
        """
        logger.info("Initializing RAG collections...")

        for collection_type, collection_name in self.collection_names.items():
            try:
                self.vector_db.create_collection(
                    collection_name=collection_name,
                    vector_size=vector_size
                )
                logger.info(f"Collection '{collection_name}' initialized")
            except Exception as e:
                logger.error(f"Failed to initialize collection '{collection_name}': {str(e)}")

        logger.info("All RAG collections initialized successfully")

    def index_documents(
        self,
        collection_type: str,
        documents: List[Dict[str, Any]],
        content_field: str = "content"
    ) -> bool:
        """
        문서 인덱싱

        Args:
            collection_type: 컬렉션 타입 ("manuals", "incidents", "schemas", "contacts")
            documents: 문서 리스트 [{"content": "...", "metadata": {...}}]
            content_field: 임베딩할 필드 이름 (기본: "content")

        Returns:
            bool: 인덱싱 성공 여부
        """
        collection_name = self.collection_names.get(collection_type)
        if not collection_name:
            raise ValueError(f"Unknown collection type: {collection_type}")

        try:
            logger.info(f"Indexing {len(documents)} documents to collection '{collection_name}'")

            # Generate embeddings
            embeddings = []
            valid_documents = []

            for doc in documents:
                content = doc.get(content_field, "")
                if not content:
                    logger.warning(f"Skipping document with empty content: {doc}")
                    continue

                try:
                    embedding = self.llm_service.generate_embedding(content)
                    embeddings.append(embedding)
                    valid_documents.append(doc)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for document: {str(e)}")
                    continue

            if not valid_documents:
                logger.warning("No valid documents to index")
                return False

            # Upsert to vector DB
            self.vector_db.upsert_documents(
                collection_name=collection_name,
                documents=valid_documents,
                embeddings=embeddings
            )

            logger.info(f"Successfully indexed {len(valid_documents)} documents")
            return True

        except Exception as e:
            logger.error(f"Failed to index documents: {str(e)}")
            raise Exception(f"문서 인덱싱 실패: {str(e)}")

    def semantic_search(
        self,
        collection_type: str,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        의미 기반 검색

        Args:
            collection_type: 컬렉션 타입
            query: 검색 쿼리
            limit: 반환할 결과 수
            score_threshold: 최소 유사도 점수
            filter_conditions: 필터 조건 (선택적)

        Returns:
            List[Dict]: 검색 결과
                - id: 문서 ID
                - score: 유사도 점수
                - payload: 문서 메타데이터
        """
        collection_name = self.collection_names.get(collection_type)
        if not collection_name:
            raise ValueError(f"Unknown collection type: {collection_type}")

        try:
            logger.debug(f"Performing semantic search in '{collection_name}' with query: '{query[:50]}...'")

            # Generate query embedding
            query_embedding = self.llm_service.generate_embedding(query)

            # Search in vector DB
            results = self.vector_db.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions
            )

            logger.info(f"Semantic search returned {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise Exception(f"의미 검색 실패: {str(e)}")

    def retrieve_context(
        self,
        query: str,
        collection_types: List[str] = ["manuals", "incidents"],
        max_results_per_collection: int = 3,
        score_threshold: float = 0.7
    ) -> str:
        """
        RAG 컨텍스트 생성

        여러 컬렉션에서 관련 문서를 검색하여 컨텍스트 생성

        Args:
            query: 검색 쿼리
            collection_types: 검색할 컬렉션 타입 리스트
            max_results_per_collection: 컬렉션당 최대 결과 수
            score_threshold: 최소 유사도 점수

        Returns:
            str: 생성된 컨텍스트
        """
        all_contexts = []

        try:
            for collection_type in collection_types:
                try:
                    results = self.semantic_search(
                        collection_type=collection_type,
                        query=query,
                        limit=max_results_per_collection,
                        score_threshold=score_threshold
                    )

                    for result in results:
                        context = f"[{collection_type.upper()}] (Relevance: {result['score']:.2f})\n"
                        context += result['payload'].get('content', '')
                        all_contexts.append(context)

                except Exception as e:
                    logger.warning(f"Failed to search in collection '{collection_type}': {str(e)}")
                    continue

            if not all_contexts:
                logger.warning("No context found for query")
                return "관련 정보를 찾을 수 없습니다."

            context_str = "\n\n" + "="*50 + "\n\n".join(all_contexts)

            logger.info(f"Retrieved {len(all_contexts)} context chunks")

            return context_str

        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return f"컨텍스트 생성 중 오류 발생: {str(e)}"

    def rag_query(
        self,
        query: str,
        collection_types: List[str] = ["manuals"],
        system_prompt: str = "You are a helpful assistant.",
        max_context_results: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        RAG 기반 질의응답

        Args:
            query: 사용자 질문
            collection_types: 검색할 컬렉션 타입 리스트
            system_prompt: 시스템 프롬프트
            max_context_results: 컬렉션당 최대 컨텍스트 수
            temperature: LLM temperature
            max_tokens: 최대 토큰 수

        Returns:
            Dict containing:
                - answer: 생성된 답변
                - sources: 사용된 소스 정보
                - usage: 토큰 사용량
        """
        try:
            logger.info(f"Processing RAG query: '{query[:50]}...'")

            # 1. Retrieve context
            context = self.retrieve_context(
                query=query,
                collection_types=collection_types,
                max_results_per_collection=max_context_results
            )

            # 2. Construct messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
다음 정보를 참고하여 질문에 답변하세요:

<컨텍스트>
{context}
</컨텍스트>

<질문>
{query}
</질문>

답변:
                """}
            ]

            # 3. Generate answer using LLM
            response = self.llm_service.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            result = {
                "answer": response["content"],
                "sources": context,
                "usage": response["usage"],
                "model": response["model"]
            }

            logger.info("RAG query completed successfully")

            return result

        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise Exception(f"RAG 쿼리 실패: {str(e)}")

    async def async_rag_query(
        self,
        query: str,
        collection_types: List[str] = ["manuals"],
        system_prompt: str = "You are a helpful assistant.",
        max_context_results: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        비동기 RAG 기반 질의응답

        Args:
            query: 사용자 질문
            collection_types: 검색할 컬렉션 타입 리스트
            system_prompt: 시스템 프롬프트
            max_context_results: 컬렉션당 최대 컨텍스트 수
            temperature: LLM temperature
            max_tokens: 최대 토큰 수

        Returns:
            Dict containing answer and metadata
        """
        try:
            # Retrieve context (synchronous for now)
            context = self.retrieve_context(
                query=query,
                collection_types=collection_types,
                max_results_per_collection=max_context_results
            )

            # Construct messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
다음 정보를 참고하여 질문에 답변하세요:

<컨텍스트>
{context}
</컨텍스트>

<질문>
{query}
</질문>

답변:
                """}
            ]

            # Generate answer asynchronously
            response = await self.llm_service.async_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                "answer": response["content"],
                "sources": context,
                "usage": response["usage"],
                "model": response["model"]
            }

        except Exception as e:
            logger.error(f"Async RAG query failed: {str(e)}")
            raise Exception(f"비동기 RAG 쿼리 실패: {str(e)}")

    def update_document(
        self,
        collection_type: str,
        document_id: str,
        updated_document: Dict[str, Any],
        content_field: str = "content"
    ) -> bool:
        """
        문서 업데이트

        Args:
            collection_type: 컬렉션 타입
            document_id: 문서 ID
            updated_document: 업데이트할 문서
            content_field: 임베딩할 필드 이름

        Returns:
            bool: 업데이트 성공 여부
        """
        collection_name = self.collection_names.get(collection_type)
        if not collection_name:
            raise ValueError(f"Unknown collection type: {collection_type}")

        try:
            content = updated_document.get(content_field, "")
            if not content:
                raise ValueError("Document content cannot be empty")

            # Generate new embedding
            embedding = self.llm_service.generate_embedding(content)

            # Upsert (update or insert)
            self.vector_db.upsert_documents(
                collection_name=collection_name,
                documents=[updated_document],
                embeddings=[embedding],
                ids=[document_id]
            )

            logger.info(f"Document '{document_id}' updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}")
            return False

    def delete_document(
        self,
        collection_type: str,
        document_id: str
    ) -> bool:
        """
        문서 삭제

        Args:
            collection_type: 컬렉션 타입
            document_id: 문서 ID

        Returns:
            bool: 삭제 성공 여부
        """
        collection_name = self.collection_names.get(collection_type)
        if not collection_name:
            raise ValueError(f"Unknown collection type: {collection_type}")

        return self.vector_db.delete_document(collection_name, document_id)

    def get_collection_stats(self, collection_type: str) -> Dict[str, Any]:
        """
        컬렉션 통계 조회

        Args:
            collection_type: 컬렉션 타입

        Returns:
            Dict: 컬렉션 통계
        """
        collection_name = self.collection_names.get(collection_type)
        if not collection_name:
            raise ValueError(f"Unknown collection type: {collection_type}")

        document_count = self.vector_db.count_documents(collection_name)

        return {
            "collection_type": collection_type,
            "collection_name": collection_name,
            "document_count": document_count
        }


# Singleton instance
_rag_service_instance = None


def get_rag_service() -> RAGService:
    """
    RAGService 싱글톤 인스턴스 반환

    Returns:
        RAGService: RAG 서비스 인스턴스
    """
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance


if __name__ == "__main__":
    # Test the service
    import logging
    logging.basicConfig(level=logging.INFO)

    try:
        rag_service = RAGService()

        # Test collection initialization
        print("\n=== Testing Collection Initialization ===")
        rag_service.initialize_collections()

        # Test document indexing
        print("\n=== Testing Document Indexing ===")
        test_documents = [
            {
                "content": "Azure OpenAI is a cloud-based AI service that provides access to OpenAI's GPT models.",
                "title": "Azure OpenAI Overview",
                "type": "manual"
            },
            {
                "content": "To use Azure OpenAI, you need an API key and endpoint URL from Azure portal.",
                "title": "Getting Started",
                "type": "manual"
            }
        ]
        rag_service.index_documents("manuals", test_documents)

        # Test semantic search
        print("\n=== Testing Semantic Search ===")
        query = "How to use Azure OpenAI?"
        results = rag_service.semantic_search("manuals", query, limit=2)
        print(f"Found {len(results)} results")
        for result in results:
            print(f"  Score: {result['score']:.2f}")
            print(f"  Content: {result['payload'].get('content', '')[:100]}...")

        # Test RAG query
        print("\n=== Testing RAG Query ===")
        rag_result = rag_service.rag_query(
            query="What is Azure OpenAI?",
            collection_types=["manuals"]
        )
        print(f"Answer: {rag_result['answer']}")
        print(f"Tokens used: {rag_result['usage']['total_tokens']}")

        # Test collection stats
        print("\n=== Testing Collection Stats ===")
        stats = rag_service.get_collection_stats("manuals")
        print(f"Stats: {stats}")

    except Exception as e:
        print(f"Error: {str(e)}")
