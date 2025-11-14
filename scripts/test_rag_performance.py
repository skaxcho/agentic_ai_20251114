#!/usr/bin/env python3
"""
RAG Performance Test Script

RAG 시스템의 검색 정확도 및 응답 시간을 테스트합니다.

실행 방법:
    python scripts/test_rag_performance.py
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.services.rag_service import get_rag_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGPerformanceTester:
    """RAG 성능 테스트 클래스"""

    def __init__(self):
        """Initialize RAG Performance Tester"""
        self.rag_service = get_rag_service()

        # Test queries
        self.test_queries = [
            {
                "query": "Azure OpenAI API Rate Limit 오류가 발생했을 때 어떻게 해결하나요?",
                "expected_collection": "incidents",
                "expected_keywords": ["rate limit", "429", "azure openai"]
            },
            {
                "query": "PostgreSQL 데이터베이스에 연결할 수 없을 때 확인해야 할 사항은?",
                "expected_collection": "manuals",
                "expected_keywords": ["postgresql", "connection", "pg_hba.conf"]
            },
            {
                "query": "tasks 테이블의 구조와 주요 컬럼에 대해 설명해주세요.",
                "expected_collection": "schemas",
                "expected_keywords": ["tasks", "agent_name", "status"]
            },
            {
                "query": "AI/ML 관련 문제가 생겼을 때 누구에게 연락해야 하나요?",
                "expected_collection": "contacts",
                "expected_keywords": ["김철수", "AI/ML", "chulsoo.kim"]
            },
            {
                "query": "Qdrant Vector Database의 메모리 사용량을 줄이는 방법은?",
                "expected_collection": "incidents",
                "expected_keywords": ["qdrant", "memory", "quantization"]
            },
            {
                "query": "데이터베이스 백업을 어떻게 수행하나요?",
                "expected_collection": "manuals",
                "expected_keywords": ["backup", "pg_dump", "postgresql"]
            },
            {
                "query": "agent_executions 테이블에서 Agent별 성능 통계를 조회하려면?",
                "expected_collection": "schemas",
                "expected_keywords": ["agent_executions", "performance", "avg"]
            },
            {
                "query": "DevOps 담당자의 연락처를 알려주세요.",
                "expected_collection": "contacts",
                "expected_keywords": ["박지훈", "DevOps", "infrastructure"]
            },
            {
                "query": "RAG 검색 정확도가 낮을 때의 해결 방법은?",
                "expected_collection": "incidents",
                "expected_keywords": ["rag", "search", "accuracy", "threshold"]
            },
            {
                "query": "Qdrant에서 컬렉션을 생성하는 방법을 알려주세요.",
                "expected_collection": "manuals",
                "expected_keywords": ["qdrant", "collection", "create"]
            }
        ]

        # Results
        self.results = []

    def test_semantic_search(
        self,
        query: str,
        collection_type: str,
        score_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        의미 검색 테스트

        Args:
            query: 검색 쿼리
            collection_type: 컬렉션 타입
            score_threshold: 최소 유사도 점수

        Returns:
            Dict: 테스트 결과
        """
        start_time = time.time()

        try:
            results = self.rag_service.semantic_search(
                collection_type=collection_type,
                query=query,
                limit=5,
                score_threshold=score_threshold
            )

            response_time = time.time() - start_time

            return {
                "success": True,
                "response_time": response_time,
                "num_results": len(results),
                "top_score": results[0]["score"] if results else 0,
                "results": results
            }

        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "response_time": response_time,
                "error": str(e)
            }

    def test_rag_query(
        self,
        query: str,
        collection_types: List[str]
    ) -> Dict[str, Any]:
        """
        RAG 쿼리 테스트

        Args:
            query: 사용자 질문
            collection_types: 검색할 컬렉션 타입

        Returns:
            Dict: 테스트 결과
        """
        start_time = time.time()

        try:
            result = self.rag_service.rag_query(
                query=query,
                collection_types=collection_types,
                max_context_results=3
            )

            response_time = time.time() - start_time

            return {
                "success": True,
                "response_time": response_time,
                "answer_length": len(result["answer"]),
                "tokens_used": result["usage"]["total_tokens"],
                "answer": result["answer"][:200] + "..." if len(result["answer"]) > 200 else result["answer"]
            }

        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "response_time": response_time,
                "error": str(e)
            }

    def evaluate_relevance(
        self,
        query_data: Dict[str, Any],
        search_results: List[Dict]
    ) -> float:
        """
        검색 결과의 관련성 평가

        Args:
            query_data: 쿼리 데이터 (expected_keywords 포함)
            search_results: 검색 결과

        Returns:
            float: 관련성 점수 (0-1)
        """
        if not search_results:
            return 0.0

        expected_keywords = query_data["expected_keywords"]
        top_result = search_results[0]
        content = top_result["payload"].get("content", "").lower()

        # Check how many expected keywords are found
        found_keywords = sum(
            1 for keyword in expected_keywords
            if keyword.lower() in content
        )

        relevance_score = found_keywords / len(expected_keywords)

        return relevance_score

    def run_tests(self):
        """모든 테스트 실행"""
        logger.info("="*60)
        logger.info("RAG Performance Test")
        logger.info("="*60)

        for i, test_case in enumerate(self.test_queries, 1):
            logger.info(f"\n--- Test {i}/{len(self.test_queries)} ---")
            logger.info(f"Query: {test_case['query']}")
            logger.info(f"Expected Collection: {test_case['expected_collection']}")

            # Test semantic search
            search_result = self.test_semantic_search(
                query=test_case["query"],
                collection_type=test_case["expected_collection"],
                score_threshold=0.7
            )

            if search_result["success"]:
                logger.info(f"✓ Search Response Time: {search_result['response_time']:.3f}s")
                logger.info(f"✓ Results Found: {search_result['num_results']}")
                logger.info(f"✓ Top Score: {search_result['top_score']:.3f}")

                # Evaluate relevance
                relevance = self.evaluate_relevance(test_case, search_result["results"])
                logger.info(f"✓ Relevance Score: {relevance:.3f}")

                result = {
                    "test_id": i,
                    "query": test_case["query"],
                    "collection": test_case["expected_collection"],
                    "search_success": True,
                    "search_response_time": search_result["response_time"],
                    "num_results": search_result["num_results"],
                    "top_score": search_result["top_score"],
                    "relevance_score": relevance
                }
            else:
                logger.error(f"✗ Search Failed: {search_result.get('error')}")
                result = {
                    "test_id": i,
                    "query": test_case["query"],
                    "collection": test_case["expected_collection"],
                    "search_success": False,
                    "error": search_result.get("error")
                }

            self.results.append(result)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """테스트 결과 요약 출력"""
        logger.info("\n" + "="*60)
        logger.info("Test Summary")
        logger.info("="*60)

        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.get("search_success"))

        # Calculate averages
        avg_response_time = sum(
            r.get("search_response_time", 0)
            for r in self.results if r.get("search_success")
        ) / successful_tests if successful_tests > 0 else 0

        avg_top_score = sum(
            r.get("top_score", 0)
            for r in self.results if r.get("search_success")
        ) / successful_tests if successful_tests > 0 else 0

        avg_relevance = sum(
            r.get("relevance_score", 0)
            for r in self.results if r.get("search_success")
        ) / successful_tests if successful_tests > 0 else 0

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful Tests: {successful_tests}")
        logger.info(f"Failed Tests: {total_tests - successful_tests}")
        logger.info(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        logger.info(f"\nAverage Response Time: {avg_response_time:.3f}s")
        logger.info(f"Average Top Score: {avg_top_score:.3f}")
        logger.info(f"Average Relevance Score: {avg_relevance:.3f}")

        # Evaluation criteria
        logger.info("\n" + "="*60)
        logger.info("Evaluation Criteria")
        logger.info("="*60)

        criteria = {
            "Response Time < 3s": avg_response_time < 3.0,
            "Top Score > 0.8": avg_top_score > 0.8,
            "Relevance Score > 0.7": avg_relevance > 0.7,
            "Success Rate > 90%": (successful_tests/total_tests) > 0.9
        }

        for criterion, passed in criteria.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{status}: {criterion}")

        # Overall result
        all_passed = all(criteria.values())
        logger.info("\n" + "="*60)
        if all_passed:
            logger.info("🎉 Overall Result: PASS")
        else:
            logger.info("⚠️  Overall Result: FAIL")
        logger.info("="*60)

        return all_passed


def main():
    """Main function"""
    tester = RAGPerformanceTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
