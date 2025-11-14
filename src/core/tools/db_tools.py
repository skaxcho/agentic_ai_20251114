"""
Database Tools Module

데이터베이스 작업 관련 도구
- SQL 생성
- 데이터 검증
- 스키마 분석
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import re

# Configure logging
logger = logging.getLogger(__name__)


class SQLGeneratorTool:
    """SQL 쿼리 생성 도구"""

    def __init__(self):
        """Initialize SQL Generator Tool"""
        logger.info("SQLGeneratorTool initialized")

    def generate_select_query(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        SELECT 쿼리 생성

        Args:
            table_name: 테이블 이름
            columns: 컬럼 리스트 (None이면 *)
            where_clause: WHERE 조건
            order_by: ORDER BY 절
            limit: LIMIT 값

        Returns:
            str: 생성된 SQL 쿼리
        """
        cols = ", ".join(columns) if columns else "*"
        query = f"SELECT {cols} FROM {table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        query += ";"

        logger.debug(f"Generated SELECT query: {query}")
        return query

    def generate_insert_query(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> str:
        """
        INSERT 쿼리 생성

        Args:
            table_name: 테이블 이름
            data: 삽입할 데이터

        Returns:
            str: 생성된 SQL 쿼리
        """
        columns = ", ".join(data.keys())
        values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in data.values()])

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"

        logger.debug(f"Generated INSERT query: {query}")
        return query

    def generate_update_query(
        self,
        table_name: str,
        data: Dict[str, Any],
        where_clause: str
    ) -> str:
        """
        UPDATE 쿼리 생성

        Args:
            table_name: 테이블 이름
            data: 업데이트할 데이터
            where_clause: WHERE 조건

        Returns:
            str: 생성된 SQL 쿼리
        """
        set_clause = ", ".join([
            f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}"
            for k, v in data.items()
        ])

        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};"

        logger.debug(f"Generated UPDATE query: {query}")
        return query

    def validate_sql_syntax(self, sql: str) -> Dict[str, Any]:
        """
        SQL 문법 검증 (간단한 검증)

        Args:
            sql: SQL 쿼리

        Returns:
            Dict: 검증 결과
        """
        sql = sql.strip()

        # Basic validation
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
        has_dangerous = any(keyword in sql.upper() for keyword in dangerous_keywords)

        if has_dangerous:
            return {
                "is_valid": False,
                "error": "Dangerous keywords detected",
                "warnings": dangerous_keywords
            }

        # Check basic syntax
        if not sql.upper().startswith(("SELECT", "INSERT", "UPDATE")):
            return {
                "is_valid": False,
                "error": "Query must start with SELECT, INSERT, or UPDATE",
                "warnings": []
            }

        return {
            "is_valid": True,
            "error": None,
            "warnings": []
        }


class DataValidatorTool:
    """데이터 검증 도구"""

    def __init__(self):
        """Initialize Data Validator Tool"""
        logger.info("DataValidatorTool initialized")

    def validate_data_integrity(
        self,
        data: List[Dict[str, Any]],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        데이터 무결성 검증

        Args:
            data: 검증할 데이터
            schema: 스키마 정의

        Returns:
            Dict: 검증 결과
        """
        if not data:
            return {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "row_count": 0
            }

        errors = []
        warnings = []

        required_columns = schema.get("required_columns", [])

        # Check each row
        for i, row in enumerate(data):
            # Check required columns
            for col in required_columns:
                if col not in row or row[col] is None:
                    errors.append({
                        "row": i,
                        "column": col,
                        "error": "Required column is missing or null"
                    })

        logger.info(f"Data validation: {len(data)} rows, {len(errors)} errors")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "row_count": len(data)
        }

    def check_duplicates(
        self,
        data: List[Dict[str, Any]],
        key_columns: List[str]
    ) -> Dict[str, Any]:
        """
        중복 데이터 확인

        Args:
            data: 확인할 데이터
            key_columns: 중복 확인할 키 컬럼

        Returns:
            Dict: 중복 확인 결과
        """
        seen = set()
        duplicates = []

        for i, row in enumerate(data):
            key = tuple(row.get(col) for col in key_columns)

            if key in seen:
                duplicates.append({
                    "row": i,
                    "key": dict(zip(key_columns, key))
                })
            else:
                seen.add(key)

        logger.info(f"Duplicate check: {len(duplicates)} duplicates found")

        return {
            "has_duplicates": len(duplicates) > 0,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates[:10]  # Limit to 10
        }

    def validate_data_types(
        self,
        data: List[Dict[str, Any]],
        type_spec: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        데이터 타입 검증

        Args:
            data: 검증할 데이터
            type_spec: 타입 명세 {"column": "type"}

        Returns:
            Dict: 검증 결과
        """
        errors = []

        for i, row in enumerate(data):
            for col, expected_type in type_spec.items():
                if col not in row:
                    continue

                value = row[col]

                if value is None:
                    continue

                # Check type
                is_valid = self._check_type(value, expected_type)

                if not is_valid:
                    errors.append({
                        "row": i,
                        "column": col,
                        "expected_type": expected_type,
                        "actual_value": str(value)[:50]
                    })

        logger.info(f"Type validation: {len(errors)} type errors")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors[:20]  # Limit to 20
        }

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        타입 확인

        Args:
            value: 값
            expected_type: 기대하는 타입

        Returns:
            bool: 타입 일치 여부
        """
        type_map = {
            "int": int,
            "integer": int,
            "float": (int, float),
            "str": str,
            "string": str,
            "bool": bool,
            "boolean": bool
        }

        expected = type_map.get(expected_type.lower())

        if expected is None:
            return True  # Unknown type, pass

        return isinstance(value, expected)


class SchemaAnalyzerTool:
    """스키마 분석 도구"""

    def __init__(self):
        """Initialize Schema Analyzer Tool"""
        logger.info("SchemaAnalyzerTool initialized")

    def analyze_table_structure(
        self,
        table_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        테이블 구조 분석

        Args:
            table_data: 테이블 데이터

        Returns:
            Dict: 분석 결과
        """
        if not table_data:
            return {
                "columns": [],
                "row_count": 0,
                "inferred_types": {}
            }

        # Get columns
        columns = list(table_data[0].keys())

        # Infer types
        inferred_types = {}
        for col in columns:
            values = [row.get(col) for row in table_data if row.get(col) is not None]

            if not values:
                inferred_types[col] = "unknown"
                continue

            # Check first non-null value
            sample = values[0]

            if isinstance(sample, bool):
                inferred_types[col] = "boolean"
            elif isinstance(sample, int):
                inferred_types[col] = "integer"
            elif isinstance(sample, float):
                inferred_types[col] = "float"
            elif isinstance(sample, str):
                # Check if it's a date
                if self._is_date_string(sample):
                    inferred_types[col] = "date"
                else:
                    inferred_types[col] = "string"
            else:
                inferred_types[col] = "unknown"

        logger.info(f"Schema analysis: {len(columns)} columns, {len(table_data)} rows")

        return {
            "columns": columns,
            "row_count": len(table_data),
            "inferred_types": inferred_types
        }

    def _is_date_string(self, value: str) -> bool:
        """
        날짜 문자열 여부 확인

        Args:
            value: 문자열

        Returns:
            bool: 날짜 문자열 여부
        """
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"  # ISO 8601
        ]

        return any(re.match(pattern, value) for pattern in date_patterns)


# Singleton instances
_sql_generator_instance = None
_data_validator_instance = None
_schema_analyzer_instance = None


def get_sql_generator() -> SQLGeneratorTool:
    """SQLGeneratorTool 싱글톤 인스턴스 반환"""
    global _sql_generator_instance
    if _sql_generator_instance is None:
        _sql_generator_instance = SQLGeneratorTool()
    return _sql_generator_instance


def get_data_validator() -> DataValidatorTool:
    """DataValidatorTool 싱글톤 인스턴스 반환"""
    global _data_validator_instance
    if _data_validator_instance is None:
        _data_validator_instance = DataValidatorTool()
    return _data_validator_instance


def get_schema_analyzer() -> SchemaAnalyzerTool:
    """SchemaAnalyzerTool 싱글톤 인스턴스 반환"""
    global _schema_analyzer_instance
    if _schema_analyzer_instance is None:
        _schema_analyzer_instance = SchemaAnalyzerTool()
    return _schema_analyzer_instance


if __name__ == "__main__":
    # Test the tools
    logging.basicConfig(level=logging.INFO)

    print("\n=== Testing SQL Generator ===")
    sql_gen = SQLGeneratorTool()

    query = sql_gen.generate_select_query(
        table_name="users",
        columns=["id", "username", "email"],
        where_clause="is_active = true",
        order_by="created_at DESC",
        limit=10
    )
    print(f"Generated query: {query}")

    validation = sql_gen.validate_sql_syntax(query)
    print(f"Validation: {validation}")

    print("\n=== Testing Data Validator ===")
    validator = DataValidatorTool()

    test_data = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 3, "name": "Charlie"}  # Missing age
    ]

    result = validator.validate_data_integrity(
        data=test_data,
        schema={"required_columns": ["id", "name", "age"]}
    )
    print(f"Integrity check: {result}")

    print("\n=== Testing Schema Analyzer ===")
    analyzer = SchemaAnalyzerTool()

    analysis = analyzer.analyze_table_structure(test_data)
    print(f"Schema analysis: {analysis}")
