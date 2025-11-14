#!/usr/bin/env python3
"""
Knowledge Base Builder

이 스크립트는 knowledge-base 디렉토리의 데이터를 읽어서
Qdrant Vector Database에 인덱싱합니다.

실행 방법:
    python scripts/build_knowledge_base.py

옵션:
    --reset: 기존 컬렉션을 삭제하고 새로 생성
    --dry-run: 실제 인덱싱 없이 데이터만 확인
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.services.rag_service import RAGService, get_rag_service
from src.core.services.vector_db_service import VectorDBService, get_vector_db_service
from src.core.services.llm_service import AzureOpenAIService, get_llm_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeBaseBuilder:
    """Knowledge Base 구축 클래스"""

    def __init__(self, reset: bool = False, dry_run: bool = False):
        """
        Initialize Knowledge Base Builder

        Args:
            reset: 기존 컬렉션 재생성 여부
            dry_run: Dry run 모드
        """
        self.reset = reset
        self.dry_run = dry_run
        self.kb_base_dir = Path(__file__).parent.parent / "knowledge-base"

        # Services
        self.rag_service = get_rag_service()
        self.vector_db = get_vector_db_service()
        self.llm_service = get_llm_service()

        # Statistics
        self.stats = {
            "manuals": {"total": 0, "success": 0, "failed": 0},
            "incidents": {"total": 0, "success": 0, "failed": 0},
            "schemas": {"total": 0, "success": 0, "failed": 0},
            "contacts": {"total": 0, "success": 0, "failed": 0}
        }

    def load_manual_files(self) -> List[Dict[str, Any]]:
        """
        매뉴얼 파일 로드

        Returns:
            List[Dict]: 매뉴얼 문서 리스트
        """
        manuals_dir = self.kb_base_dir / "manuals"
        documents = []

        if not manuals_dir.exists():
            logger.warning(f"Manuals directory not found: {manuals_dir}")
            return documents

        for file_path in manuals_dir.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract title from first line (assuming it's a markdown header)
                lines = content.split('\n')
                title = lines[0].strip('# ') if lines else file_path.stem

                doc = {
                    "content": content,
                    "title": title,
                    "filename": file_path.name,
                    "type": "manual",
                    "file_type": "markdown"
                }

                documents.append(doc)
                self.stats["manuals"]["total"] += 1

                logger.info(f"Loaded manual: {file_path.name}")

            except Exception as e:
                logger.error(f"Failed to load manual {file_path.name}: {str(e)}")
                self.stats["manuals"]["failed"] += 1

        logger.info(f"Loaded {len(documents)} manual documents")
        return documents

    def load_incidents(self) -> List[Dict[str, Any]]:
        """
        장애 사례 로드

        Returns:
            List[Dict]: 장애 사례 문서 리스트
        """
        incidents_file = self.kb_base_dir / "incidents" / "incidents.json"
        documents = []

        if not incidents_file.exists():
            logger.warning(f"Incidents file not found: {incidents_file}")
            return documents

        try:
            with open(incidents_file, 'r', encoding='utf-8') as f:
                incidents = json.load(f)

            for incident in incidents:
                # Create content from incident data
                content = f"""
                장애 ID: {incident['incident_id']}
                제목: {incident['title']}
                심각도: {incident['severity']}
                카테고리: {incident['category']}
                발생 시간: {incident['occurred_at']}

                설명:
                {incident['description']}

                근본 원인:
                {incident['root_cause']}

                해결 방법:
                {incident['solution']}

                예방 대책:
                {incident['prevention']}

                태그: {', '.join(incident['tags'])}
                """

                doc = {
                    "content": content.strip(),
                    "incident_id": incident['incident_id'],
                    "title": incident['title'],
                    "severity": incident['severity'],
                    "category": incident['category'],
                    "type": "incident"
                }

                documents.append(doc)
                self.stats["incidents"]["total"] += 1

            logger.info(f"Loaded {len(documents)} incident documents")

        except Exception as e:
            logger.error(f"Failed to load incidents: {str(e)}")
            self.stats["incidents"]["failed"] += 1

        return documents

    def load_schemas(self) -> List[Dict[str, Any]]:
        """
        데이터베이스 스키마 로드

        Returns:
            List[Dict]: 스키마 문서 리스트
        """
        schema_file = self.kb_base_dir / "schemas" / "database_schema.json"
        documents = []

        if not schema_file.exists():
            logger.warning(f"Schema file not found: {schema_file}")
            return documents

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schemas = json.load(f)

            for schema in schemas:
                # Create content from schema data
                columns_desc = "\n".join([
                    f"  - {col['name']} ({col['type']}): {col.get('description', '')}"
                    for col in schema['columns']
                ])

                content = f"""
                스키마: {schema['schema_name']}
                테이블: {schema['table_name']}

                설명:
                {schema['description']}

                컬럼:
                {columns_desc}

                샘플 쿼리:
                {schema.get('sample_query', '')}
                """

                doc = {
                    "content": content.strip(),
                    "schema_name": schema['schema_name'],
                    "table_name": schema['table_name'],
                    "description": schema['description'],
                    "type": "schema"
                }

                documents.append(doc)
                self.stats["schemas"]["total"] += 1

            logger.info(f"Loaded {len(documents)} schema documents")

        except Exception as e:
            logger.error(f"Failed to load schemas: {str(e)}")
            self.stats["schemas"]["failed"] += 1

        return documents

    def load_contacts(self) -> List[Dict[str, Any]]:
        """
        담당자 정보 로드

        Returns:
            List[Dict]: 담당자 문서 리스트
        """
        contacts_file = self.kb_base_dir / "contacts" / "team_contacts.json"
        documents = []

        if not contacts_file.exists():
            logger.warning(f"Contacts file not found: {contacts_file}")
            return documents

        try:
            with open(contacts_file, 'r', encoding='utf-8') as f:
                contacts = json.load(f)

            for contact in contacts:
                # Create content from contact data
                content = f"""
                이름: {contact['name']}
                역할: {contact['role']}
                부서: {contact['department']}
                이메일: {contact['email']}
                전화: {contact['phone']}
                Slack: {contact['slack']}

                담당 업무:
                {chr(10).join(['  - ' + resp for resp in contact['responsibilities']])}

                전문 분야:
                {', '.join(contact['expertise'])}

                근무 시간: {contact['availability']}
                긴급 연락처: {'예' if contact['emergency_contact'] else '아니오'}
                """

                doc = {
                    "content": content.strip(),
                    "name": contact['name'],
                    "role": contact['role'],
                    "department": contact['department'],
                    "email": contact['email'],
                    "type": "contact"
                }

                documents.append(doc)
                self.stats["contacts"]["total"] += 1

            logger.info(f"Loaded {len(documents)} contact documents")

        except Exception as e:
            logger.error(f"Failed to load contacts: {str(e)}")
            self.stats["contacts"]["failed"] += 1

        return documents

    def initialize_collections(self):
        """컬렉션 초기화"""
        logger.info("Initializing collections...")

        if self.reset:
            logger.warning("RESET mode: Deleting existing collections...")
            for collection_type in ["manuals", "incidents", "schemas", "contacts"]:
                collection_name = self.rag_service.collection_names[collection_type]
                try:
                    self.vector_db.delete_collection(collection_name)
                    logger.info(f"Deleted collection: {collection_name}")
                except Exception as e:
                    logger.warning(f"Could not delete collection {collection_name}: {str(e)}")

        if not self.dry_run:
            self.rag_service.initialize_collections()
            logger.info("Collections initialized successfully")
        else:
            logger.info("DRY RUN: Skipping collection initialization")

    def index_documents(
        self,
        collection_type: str,
        documents: List[Dict[str, Any]]
    ):
        """
        문서 인덱싱

        Args:
            collection_type: 컬렉션 타입
            documents: 문서 리스트
        """
        if not documents:
            logger.warning(f"No documents to index for {collection_type}")
            return

        if self.dry_run:
            logger.info(f"DRY RUN: Would index {len(documents)} documents to {collection_type}")
            self.stats[collection_type]["success"] = len(documents)
            return

        try:
            logger.info(f"Indexing {len(documents)} documents to {collection_type}...")

            self.rag_service.index_documents(
                collection_type=collection_type,
                documents=documents,
                content_field="content"
            )

            self.stats[collection_type]["success"] = len(documents)
            logger.info(f"Successfully indexed {len(documents)} documents to {collection_type}")

        except Exception as e:
            logger.error(f"Failed to index documents to {collection_type}: {str(e)}")
            self.stats[collection_type]["failed"] = len(documents)
            raise

    def verify_indexing(self):
        """인덱싱 검증"""
        logger.info("\n" + "="*50)
        logger.info("Verifying indexing...")
        logger.info("="*50)

        for collection_type in ["manuals", "incidents", "schemas", "contacts"]:
            try:
                stats = self.rag_service.get_collection_stats(collection_type)
                logger.info(f"{collection_type}: {stats['document_count']} documents")
            except Exception as e:
                logger.error(f"Failed to get stats for {collection_type}: {str(e)}")

    def print_summary(self):
        """결과 요약 출력"""
        logger.info("\n" + "="*50)
        logger.info("Knowledge Base Building Summary")
        logger.info("="*50)

        total_docs = 0
        total_success = 0
        total_failed = 0

        for collection_type, stats in self.stats.items():
            total_docs += stats["total"]
            total_success += stats["success"]
            total_failed += stats["failed"]

            logger.info(f"\n{collection_type.upper()}:")
            logger.info(f"  Total: {stats['total']}")
            logger.info(f"  Success: {stats['success']}")
            logger.info(f"  Failed: {stats['failed']}")

        logger.info(f"\nOVERALL:")
        logger.info(f"  Total Documents: {total_docs}")
        logger.info(f"  Successfully Indexed: {total_success}")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Success Rate: {(total_success/total_docs*100) if total_docs > 0 else 0:.1f}%")

        if self.dry_run:
            logger.info("\n(DRY RUN mode - no actual indexing performed)")

    def build(self):
        """Knowledge Base 구축 실행"""
        logger.info("Starting Knowledge Base building...")

        try:
            # 1. Initialize collections
            self.initialize_collections()

            # 2. Load and index manuals
            logger.info("\n--- Processing Manuals ---")
            manuals = self.load_manual_files()
            if manuals:
                self.index_documents("manuals", manuals)

            # 3. Load and index incidents
            logger.info("\n--- Processing Incidents ---")
            incidents = self.load_incidents()
            if incidents:
                self.index_documents("incidents", incidents)

            # 4. Load and index schemas
            logger.info("\n--- Processing Schemas ---")
            schemas = self.load_schemas()
            if schemas:
                self.index_documents("schemas", schemas)

            # 5. Load and index contacts
            logger.info("\n--- Processing Contacts ---")
            contacts = self.load_contacts()
            if contacts:
                self.index_documents("contacts", contacts)

            # 6. Verify indexing
            if not self.dry_run:
                self.verify_indexing()

            # 7. Print summary
            self.print_summary()

            logger.info("\nKnowledge Base building completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Knowledge Base building failed: {str(e)}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build Knowledge Base")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collections and recreate"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no actual indexing)"
    )

    args = parser.parse_args()

    builder = KnowledgeBaseBuilder(reset=args.reset, dry_run=args.dry_run)
    success = builder.build()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
