"""
Vector Database Service Module (Qdrant)

이 모듈은 Qdrant Vector Database와의 통합을 제공합니다.
RAG 시스템을 위한 벡터 저장 및 검색 기능을 지원합니다.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams
)
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class VectorDBService:
    """Qdrant Vector Database 서비스"""

    def __init__(self):
        """Initialize Qdrant Vector DB Service"""
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.collection_prefix = os.getenv("QDRANT_COLLECTION_PREFIX", "agentic_ai")

        # Initialize client
        try:
            if self.api_key:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    api_key=self.api_key
                )
            else:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port
                )

            logger.info(f"VectorDBService initialized with Qdrant at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            raise

    def _get_collection_name(self, name: str) -> str:
        """
        컬렉션 이름에 prefix 추가

        Args:
            name: 기본 컬렉션 이름

        Returns:
            str: Prefix가 추가된 컬렉션 이름
        """
        return f"{self.collection_prefix}_{name}"

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,  # text-embedding-ada-002 dimension
        distance: Distance = Distance.COSINE
    ) -> bool:
        """
        컬렉션 생성

        Args:
            collection_name: 컬렉션 이름
            vector_size: 벡터 차원 (기본: 1536)
            distance: 거리 측정 방식 (COSINE, EUCLID, DOT)

        Returns:
            bool: 생성 성공 여부
        """
        full_name = self._get_collection_name(collection_name)

        try:
            # Check if collection already exists
            collections = self.client.get_collections().collections
            if any(c.name == full_name for c in collections):
                logger.info(f"Collection '{full_name}' already exists")
                return True

            # Create collection
            self.client.create_collection(
                collection_name=full_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )

            logger.info(f"Collection '{full_name}' created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection '{full_name}': {str(e)}")
            raise Exception(f"컬렉션 생성 실패: {str(e)}")

    def collection_exists(self, collection_name: str) -> bool:
        """
        컬렉션 존재 여부 확인

        Args:
            collection_name: 컬렉션 이름

        Returns:
            bool: 존재 여부
        """
        full_name = self._get_collection_name(collection_name)

        try:
            collections = self.client.get_collections().collections
            return any(c.name == full_name for c in collections)
        except Exception as e:
            logger.error(f"Failed to check collection existence: {str(e)}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """
        컬렉션 삭제

        Args:
            collection_name: 컬렉션 이름

        Returns:
            bool: 삭제 성공 여부
        """
        full_name = self._get_collection_name(collection_name)

        try:
            self.client.delete_collection(collection_name=full_name)
            logger.info(f"Collection '{full_name}' deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{full_name}': {str(e)}")
            return False

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        문서 삽입/업데이트

        Args:
            collection_name: 컬렉션 이름
            documents: 문서 메타데이터 리스트
            embeddings: 임베딩 벡터 리스트
            ids: 문서 ID 리스트 (선택적, 없으면 자동 생성)

        Returns:
            bool: 성공 여부
        """
        full_name = self._get_collection_name(collection_name)

        if len(documents) != len(embeddings):
            raise ValueError("Documents and embeddings must have the same length")

        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(documents))]

            # Create points
            points = [
                PointStruct(
                    id=ids[i],
                    vector=embeddings[i],
                    payload=documents[i]
                )
                for i in range(len(documents))
            ]

            # Upsert points
            self.client.upsert(
                collection_name=full_name,
                points=points
            )

            logger.info(f"Upserted {len(points)} documents to collection '{full_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert documents to '{full_name}': {str(e)}")
            raise Exception(f"문서 삽입 실패: {str(e)}")

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        유사도 검색

        Args:
            collection_name: 컬렉션 이름
            query_vector: 쿼리 벡터
            limit: 반환할 결과 수
            score_threshold: 최소 유사도 점수
            filter_conditions: 필터 조건 (선택적)

        Returns:
            List[Dict]: 검색 결과
                - id: 문서 ID
                - score: 유사도 점수
                - payload: 문서 메타데이터
        """
        full_name = self._get_collection_name(collection_name)

        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                        for key, value in filter_conditions.items()
                    ]
                )

            # Perform search
            results = self.client.search(
                collection_name=full_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            # Format results
            formatted_results = [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]

            logger.info(f"Search in '{full_name}' returned {len(formatted_results)} results")

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed in collection '{full_name}': {str(e)}")
            raise Exception(f"검색 실패: {str(e)}")

    def get_document_by_id(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        ID로 문서 조회

        Args:
            collection_name: 컬렉션 이름
            document_id: 문서 ID

        Returns:
            Optional[Dict]: 문서 정보 (없으면 None)
        """
        full_name = self._get_collection_name(collection_name)

        try:
            points = self.client.retrieve(
                collection_name=full_name,
                ids=[document_id]
            )

            if points:
                return {
                    "id": str(points[0].id),
                    "payload": points[0].payload,
                    "vector": points[0].vector
                }
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve document '{document_id}' from '{full_name}': {str(e)}")
            return None

    def delete_document(
        self,
        collection_name: str,
        document_id: str
    ) -> bool:
        """
        문서 삭제

        Args:
            collection_name: 컬렉션 이름
            document_id: 문서 ID

        Returns:
            bool: 삭제 성공 여부
        """
        full_name = self._get_collection_name(collection_name)

        try:
            self.client.delete(
                collection_name=full_name,
                points_selector=[document_id]
            )

            logger.info(f"Document '{document_id}' deleted from '{full_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document '{document_id}' from '{full_name}': {str(e)}")
            return False

    def count_documents(self, collection_name: str) -> int:
        """
        컬렉션의 문서 수 조회

        Args:
            collection_name: 컬렉션 이름

        Returns:
            int: 문서 수
        """
        full_name = self._get_collection_name(collection_name)

        try:
            collection_info = self.client.get_collection(collection_name=full_name)
            return collection_info.points_count
        except Exception as e:
            logger.error(f"Failed to count documents in '{full_name}': {str(e)}")
            return 0

    def list_collections(self) -> List[str]:
        """
        모든 컬렉션 목록 조회

        Returns:
            List[str]: 컬렉션 이름 리스트
        """
        try:
            collections = self.client.get_collections().collections
            # Remove prefix from collection names
            prefix_len = len(self.collection_prefix) + 1
            return [c.name[prefix_len:] for c in collections if c.name.startswith(self.collection_prefix)]
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            return []

    def health_check(self) -> bool:
        """
        Qdrant 연결 상태 확인

        Returns:
            bool: 연결 성공 여부
        """
        try:
            collections = self.client.get_collections()
            logger.info("Qdrant health check passed")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return False


# Singleton instance
_vector_db_service_instance = None


def get_vector_db_service() -> VectorDBService:
    """
    VectorDBService 싱글톤 인스턴스 반환

    Returns:
        VectorDBService: Vector DB 서비스 인스턴스
    """
    global _vector_db_service_instance
    if _vector_db_service_instance is None:
        _vector_db_service_instance = VectorDBService()
    return _vector_db_service_instance


if __name__ == "__main__":
    # Test the service
    logging.basicConfig(level=logging.INFO)

    try:
        vector_db = VectorDBService()

        # Test health check
        print("\n=== Testing Health Check ===")
        is_healthy = vector_db.health_check()
        print(f"Qdrant is healthy: {is_healthy}")

        # Test collection creation
        print("\n=== Testing Collection Creation ===")
        collection_name = "test_collection"
        vector_db.create_collection(collection_name)

        # Test document insertion
        print("\n=== Testing Document Insertion ===")
        documents = [
            {"content": "This is document 1", "type": "test"},
            {"content": "This is document 2", "type": "test"}
        ]
        embeddings = [
            [0.1] * 1536,  # Dummy embedding
            [0.2] * 1536   # Dummy embedding
        ]
        vector_db.upsert_documents(collection_name, documents, embeddings)

        # Test document count
        print("\n=== Testing Document Count ===")
        count = vector_db.count_documents(collection_name)
        print(f"Document count: {count}")

        # Test search
        print("\n=== Testing Search ===")
        query_vector = [0.15] * 1536
        results = vector_db.search(collection_name, query_vector, limit=2)
        print(f"Search results: {len(results)} found")

        # Test collection list
        print("\n=== Testing Collection List ===")
        collections = vector_db.list_collections()
        print(f"Collections: {collections}")

        # Clean up
        print("\n=== Cleaning Up ===")
        vector_db.delete_collection(collection_name)

    except Exception as e:
        print(f"Error: {str(e)}")
