"""
DB Extract Agent Module

데이터베이스 조회 Agent
- 자연어 쿼리 생성
- 데이터 정합성 검증
- 복잡한 통계 쿼리
"""

from typing import List, Dict, Any, Optional
from src.core.base.base_agent import BaseAgent
from src.core.tools.db_tools import (
    get_sql_generator,
    get_data_validator,
    get_schema_analyzer
)
from src.core.tools.monitoring_tools import get_database_connection_tool
import logging
from datetime import datetime
import os

# Configure logging
logger = logging.getLogger(__name__)


class DBExtractAgent(BaseAgent):
    """데이터베이스 조회 Agent"""

    def __init__(self):
        """Initialize DB Extract Agent"""
        super().__init__(
            name="DBExtractAgent",
            role="데이터베이스 전문가",
            goal="자연어 요청을 SQL 쿼리로 변환하고 데이터를 추출합니다",
            backstory="""
            당신은 20년 경력의 데이터베이스 엔지니어입니다.
            SQL, PostgreSQL, MySQL, Oracle 등 다양한 데이터베이스에 정통하며,
            복잡한 쿼리 최적화와 데이터 무결성 검증에 탁월합니다.
            자연어 요청을 정확한 SQL 쿼리로 변환하는 능력이 뛰어납니다.
            """,
            verbose=True
        )

        # Tools
        self.sql_generator = get_sql_generator()
        self.data_validator = get_data_validator()
        self.schema_analyzer = get_schema_analyzer()
        self.db_connector = get_database_connection_tool()

    def get_tools(self) -> List:
        """
        DB Extract Agent의 도구 목록

        Returns:
            List: Tool 리스트
        """
        return []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Task 실행

        Args:
            task: Task 정보
                - task_type: "nl_query", "data_validation", "statistical_query"
                - task_data: 작업별 데이터

        Returns:
            Dict: 실행 결과
        """
        task_type = task.get("task_type")
        task_data = task.get("task_data", {})

        self._log_action(f"Executing task: {task_type}")

        try:
            if task_type == "nl_query":
                result = await self._generate_sql(task_data)
            elif task_type == "data_validation":
                result = await self._validate_data(task_data)
            elif task_type == "statistical_query":
                result = await self._execute_statistical_query(task_data)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            self._log_action(f"Task completed successfully: {task_type}")

            return {
                "success": True,
                "task_type": task_type,
                "result": result
            }

        except Exception as e:
            self._log_action(f"Task failed: {str(e)}", level="error")
            return {
                "success": False,
                "task_type": task_type,
                "error": str(e)
            }

    async def _generate_sql(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        자연어 쿼리를 SQL로 변환

        Args:
            data: 쿼리 데이터
                - nl_query: 자연어 쿼리
                - database: 데이터베이스 이름
                - execute: 쿼리 실행 여부

        Returns:
            Dict: SQL 생성 결과
        """
        self._log_action("Generating SQL from natural language query")

        nl_query = data.get("nl_query")
        database = data.get("database", os.getenv("POSTGRES_DB", "agentic_ai"))
        execute = data.get("execute", False)

        if not nl_query:
            raise ValueError("Natural language query is required")

        # RAG를 사용하여 스키마 정보 검색
        schema_context = await self._get_schema_context(nl_query)

        # LLM을 사용하여 SQL 생성
        sql_query = await self._convert_nl_to_sql(
            nl_query,
            schema_context
        )

        # SQL 검증
        validation = self.sql_generator.validate_sql_syntax(sql_query)

        if not validation["is_valid"]:
            raise ValueError(f"Invalid SQL generated: {validation['error']}")

        result = {
            "nl_query": nl_query,
            "generated_sql": sql_query,
            "validation": validation,
            "schema_used": schema_context.get("tables", [])
        }

        # 쿼리 실행 (요청된 경우)
        if execute:
            query_result = await self._execute_query(
                sql_query,
                database
            )
            result["execution"] = query_result

        self._log_action(f"SQL generated: {sql_query}")

        return result

    async def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 정합성 검증

        Args:
            data: 검증 데이터
                - table_name: 테이블 이름
                - validation_rules: 검증 규칙
                - database: 데이터베이스 이름

        Returns:
            Dict: 검증 결과
        """
        self._log_action("Validating data integrity")

        table_name = data.get("table_name")
        validation_rules = data.get("validation_rules", {})
        database = data.get("database", os.getenv("POSTGRES_DB", "agentic_ai"))

        if not table_name:
            raise ValueError("Table name is required")

        # 데이터 조회
        query = f"SELECT * FROM {table_name} LIMIT 1000;"
        query_result = await self._execute_query(query, database)

        if not query_result["success"]:
            raise Exception(f"Failed to query data: {query_result.get('error')}")

        # 데이터를 딕셔너리 리스트로 변환
        rows = query_result["rows"]
        columns = query_result["columns"]
        data_rows = [dict(zip(columns, row)) for row in rows]

        # 스키마 분석
        schema_analysis = self.schema_analyzer.analyze_table_structure(data_rows)

        # 무결성 검증
        integrity_result = self.data_validator.validate_data_integrity(
            data=data_rows,
            schema=validation_rules
        )

        # 중복 검증
        duplicate_result = {}
        if validation_rules.get("check_duplicates"):
            key_columns = validation_rules.get("key_columns", [])
            duplicate_result = self.data_validator.check_duplicates(
                data=data_rows,
                key_columns=key_columns
            )

        # 타입 검증
        type_result = {}
        if validation_rules.get("type_spec"):
            type_result = self.data_validator.validate_data_types(
                data=data_rows,
                type_spec=validation_rules["type_spec"]
            )

        # LLM을 사용하여 검증 결과 분석
        analysis = await self._analyze_validation_results(
            table_name,
            integrity_result,
            duplicate_result,
            type_result,
            schema_analysis
        )

        self._log_action(f"Data validation completed for table: {table_name}")

        return {
            "table_name": table_name,
            "row_count": len(data_rows),
            "schema_analysis": schema_analysis,
            "integrity_check": integrity_result,
            "duplicate_check": duplicate_result,
            "type_check": type_result,
            "analysis": analysis,
            "validated_at": datetime.now().isoformat()
        }

    async def _execute_statistical_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        통계 쿼리 실행

        Args:
            data: 통계 쿼리 데이터
                - question: 통계 질문
                - table_name: 테이블 이름
                - database: 데이터베이스 이름

        Returns:
            Dict: 통계 결과
        """
        self._log_action("Executing statistical query")

        question = data.get("question")
        table_name = data.get("table_name")
        database = data.get("database", os.getenv("POSTGRES_DB", "agentic_ai"))

        if not question or not table_name:
            raise ValueError("Question and table name are required")

        # 스키마 정보 조회
        schema_context = await self._get_schema_context(f"table {table_name}")

        # LLM을 사용하여 통계 쿼리 생성
        stat_query = await self._generate_statistical_query(
            question,
            table_name,
            schema_context
        )

        # 쿼리 실행
        query_result = await self._execute_query(stat_query, database)

        if not query_result["success"]:
            raise Exception(f"Failed to execute statistical query: {query_result.get('error')}")

        # 결과 분석 및 해석
        interpretation = await self._interpret_statistical_results(
            question,
            stat_query,
            query_result
        )

        self._log_action(f"Statistical query completed: {question}")

        return {
            "question": question,
            "table_name": table_name,
            "generated_query": stat_query,
            "result": query_result,
            "interpretation": interpretation,
            "executed_at": datetime.now().isoformat()
        }

    async def _get_schema_context(self, query: str) -> Dict[str, Any]:
        """
        RAG를 사용하여 스키마 컨텍스트 검색

        Args:
            query: 검색 쿼리

        Returns:
            Dict: 스키마 컨텍스트
        """
        try:
            results = self.rag_service.semantic_search(
                collection_type="schemas",
                query=query,
                limit=3,
                score_threshold=0.6
            )

            tables = []
            schema_info = []

            for result in results:
                payload = result["payload"]
                tables.append(payload.get("table_name", ""))
                schema_info.append(payload.get("content", ""))

            return {
                "tables": tables,
                "schema_info": "\n\n".join(schema_info)
            }

        except Exception as e:
            self._log_action(f"Failed to get schema context: {str(e)}", level="warning")
            return {
                "tables": [],
                "schema_info": ""
            }

    async def _convert_nl_to_sql(
        self,
        nl_query: str,
        schema_context: Dict[str, Any]
    ) -> str:
        """
        자연어를 SQL로 변환

        Args:
            nl_query: 자연어 쿼리
            schema_context: 스키마 컨텍스트

        Returns:
            str: 생성된 SQL 쿼리
        """
        messages = [
            {
                "role": "system",
                "content": """당신은 SQL 전문가입니다. 자연어 요청을 PostgreSQL 쿼리로 변환하세요.

규칙:
1. SELECT 문만 생성하세요 (INSERT, UPDATE, DELETE 금지)
2. 안전한 쿼리만 생성하세요
3. 적절한 LIMIT을 사용하세요
4. 주석은 포함하지 마세요
5. 쿼리만 반환하세요 (설명 없이)"""
            },
            {
                "role": "user",
                "content": f"""
다음 자연어 요청을 SQL 쿼리로 변환해주세요:

요청: {nl_query}

스키마 정보:
{schema_context.get('schema_info', '스키마 정보 없음')}

SQL 쿼리를 생성하세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.1)

        # Extract SQL from response
        sql = response["content"].strip()

        # Remove markdown code blocks if present
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
            sql = sql.replace("```sql", "").replace("```", "").strip()

        return sql

    async def _execute_query(
        self,
        sql: str,
        database: str
    ) -> Dict[str, Any]:
        """
        SQL 쿼리 실행

        Args:
            sql: SQL 쿼리
            database: 데이터베이스 이름

        Returns:
            Dict: 쿼리 결과
        """
        try:
            result = self.db_connector.execute_query(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                database=database,
                user=os.getenv("POSTGRES_USER", "admin"),
                password=os.getenv("POSTGRES_PASSWORD", ""),
                query=sql
            )

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _generate_statistical_query(
        self,
        question: str,
        table_name: str,
        schema_context: Dict[str, Any]
    ) -> str:
        """
        통계 쿼리 생성

        Args:
            question: 통계 질문
            table_name: 테이블 이름
            schema_context: 스키마 컨텍스트

        Returns:
            str: 생성된 SQL 쿼리
        """
        messages = [
            {
                "role": "system",
                "content": "당신은 SQL 통계 분석 전문가입니다. 통계 질문을 SQL 쿼리로 변환하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 통계 질문에 답하는 SQL 쿼리를 생성해주세요:

질문: {question}
테이블: {table_name}

스키마 정보:
{schema_context.get('schema_info', '')}

COUNT, AVG, SUM, MIN, MAX, GROUP BY 등의 집계 함수를 활용하세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.1)

        sql = response["content"].strip()

        # Remove markdown code blocks
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
            sql = sql.replace("```sql", "").replace("```", "").strip()

        return sql

    async def _analyze_validation_results(
        self,
        table_name: str,
        integrity_result: Dict,
        duplicate_result: Dict,
        type_result: Dict,
        schema_analysis: Dict
    ) -> Dict[str, str]:
        """
        검증 결과 분석

        Args:
            table_name: 테이블 이름
            integrity_result: 무결성 검증 결과
            duplicate_result: 중복 검증 결과
            type_result: 타입 검증 결과
            schema_analysis: 스키마 분석 결과

        Returns:
            Dict: 분석 결과
        """
        summary = []

        if integrity_result.get("is_valid"):
            summary.append("✓ 데이터 무결성: 정상")
        else:
            error_count = len(integrity_result.get("errors", []))
            summary.append(f"✗ 데이터 무결성: {error_count}개 오류 발견")

        if duplicate_result.get("has_duplicates"):
            dup_count = duplicate_result.get("duplicate_count", 0)
            summary.append(f"✗ 중복 데이터: {dup_count}개 발견")
        else:
            summary.append("✓ 중복 데이터: 없음")

        if type_result.get("is_valid"):
            summary.append("✓ 데이터 타입: 정상")
        else:
            type_errors = len(type_result.get("errors", []))
            summary.append(f"✗ 데이터 타입: {type_errors}개 오류")

        messages = [
            {
                "role": "system",
                "content": "당신은 데이터 품질 분석 전문가입니다. 검증 결과를 분석하고 권장사항을 제시하세요."
            },
            {
                "role": "user",
                "content": f"""
테이블 '{table_name}'의 데이터 검증 결과를 분석해주세요:

{chr(10).join(summary)}

Row count: {schema_analysis.get('row_count', 0)}
Columns: {', '.join(schema_analysis.get('columns', []))}

데이터 품질 평가 및 개선 권장사항을 제시해주세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "summary": "\n".join(summary),
            "analysis": response["content"],
            "recommendations": []
        }

    async def _interpret_statistical_results(
        self,
        question: str,
        query: str,
        query_result: Dict
    ) -> Dict[str, str]:
        """
        통계 결과 해석

        Args:
            question: 통계 질문
            query: 실행된 쿼리
            query_result: 쿼리 결과

        Returns:
            Dict: 해석 결과
        """
        rows = query_result.get("rows", [])
        columns = query_result.get("columns", [])

        # Format results
        result_text = f"Columns: {', '.join(columns)}\n"
        result_text += f"Rows: {len(rows)}\n\n"

        for row in rows[:10]:  # Limit to 10 rows
            result_text += f"{row}\n"

        messages = [
            {
                "role": "system",
                "content": "당신은 데이터 분석 전문가입니다. 통계 결과를 해석하고 인사이트를 제공하세요."
            },
            {
                "role": "user",
                "content": f"""
질문: {question}

실행된 쿼리:
{query}

결과:
{result_text}

이 결과를 분석하고 질문에 대한 답변과 인사이트를 제공해주세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "interpretation": response["content"]
        }


# Factory function
def create_db_extract_agent() -> DBExtractAgent:
    """
    DBExtractAgent 인스턴스 생성

    Returns:
        DBExtractAgent: DB Extract Agent 인스턴스
    """
    return DBExtractAgent()


if __name__ == "__main__":
    # Test the agent
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_db_extract_agent():
        agent = create_db_extract_agent()

        # Test natural language query
        print("\n=== Testing Natural Language Query ===")
        task = {
            "task_type": "nl_query",
            "task_data": {
                "nl_query": "Show me the top 10 users by created date",
                "database": "agentic_ai",
                "execute": False
            }
        }

        result = await agent.execute_with_tracking(task)
        print(f"Result: {result}")

    asyncio.run(test_db_extract_agent())
