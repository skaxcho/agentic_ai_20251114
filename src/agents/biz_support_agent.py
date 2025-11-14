"""
Business Support Agent

비즈니스 사용자 지원 및 문의 응대
- 사용법 문의 응대
- 담당자 정보 조회
- 계정 발급 요청
- RAG 기반 지식 검색
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

from src.core.base.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class BizSupportAgent(BaseAgent):
    """Business Support Agent - 비즈니스 사용자 지원"""

    def __init__(self):
        """Initialize Business Support Agent"""
        super().__init__(
            name="Business Support Agent",
            role="Business Support Specialist",
            goal="사용자 문의 응대 및 기본 지원. 사용법 안내, 담당자 정보 제공, 계정 발급 요청 처리",
            backstory="""
            나는 비즈니스 사용자를 지원하는 전문가입니다.
            시스템 사용법, 담당자 정보, 계정 발급 등 다양한 문의에 친절하고 정확하게 응대합니다.
            RAG 기반 지식 검색을 활용하여 최신 정보를 제공하며,
            필요 시 ITS 티켓을 생성하여 요청 사항을 처리합니다.
            """
        )

        logger.info("BizSupportAgent initialized")

    def get_tools(self) -> List:
        """Get tools for this agent"""
        return [
            # RAG is available through self.rag_service
            # ITS is available through self.mcp_hub
        ]

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute business support task

        Args:
            task: Task definition with type and data

        Returns:
            Dict: Task execution result
        """
        task_type = task.get("type")
        data = task.get("data", {})

        logger.info(f"Executing business support task: {task_type}")

        try:
            if task_type == "answer_usage_question":
                # UC-B-01: 사용법 문의 응대
                return await self._answer_usage_question(data)
            elif task_type == "find_contact":
                # UC-B-02: 담당자 정보 조회
                return await self._find_contact(data)
            elif task_type == "request_account":
                # UC-B-03: 계정 발급 요청
                return await self._request_account(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown task type: {task_type}"
                }

        except Exception as e:
            logger.error(f"Failed to execute task: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _answer_usage_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-B-01: 사용법 문의 응대

        사용자의 사용법 관련 질문에 RAG를 활용하여 답변

        Args:
            data: {
                "question": str,
                "system_name": str (optional),
                "context": str (optional)
            }

        Returns:
            Dict: 답변 및 관련 문서
        """
        try:
            question = data.get("question", "")
            system_name = data.get("system_name")
            context = data.get("context", "")

            if not question:
                return {
                    "success": False,
                    "error": "Question is required"
                }

            logger.info(f"Answering usage question: {question}")

            # Step 1: Understand question intent
            intent_prompt = f"""
            사용자 질문을 분석해주세요:
            질문: {question}
            시스템: {system_name or '지정되지 않음'}
            컨텍스트: {context or '없음'}

            다음을 파악해주세요:
            1. 질문의 주요 의도
            2. 필요한 정보 유형 (사용법, 설정, 트러블슈팅 등)
            3. 검색에 사용할 핵심 키워드
            """

            intent_analysis = await self._llm_call(intent_prompt, temperature=0.3)

            # Step 2: Search knowledge base using RAG
            logger.info("Searching knowledge base...")

            # Search in manuals collection
            rag_result = await self._rag_query(
                query=question,
                collection_types=["manuals"],
                top_k=5
            )

            if not rag_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to search knowledge base",
                    "details": rag_result
                }

            # Step 3: Generate detailed answer
            answer_prompt = f"""
            사용자 질문에 친절하고 상세하게 답변해주세요:

            질문: {question}
            시스템: {system_name or '일반'}

            검색된 관련 문서:
            {rag_result.get('answer', '')}

            답변 형식:
            1. 간단한 요약 (1-2문장)
            2. 상세한 설명 (단계별 가이드)
            3. 주의사항 (있다면)
            4. 추가 참고사항

            답변은 비기술 사용자도 이해하기 쉽게 작성해주세요.
            """

            detailed_answer = await self._llm_call(answer_prompt, temperature=0.5)

            # Step 4: Extract related documents
            sources = rag_result.get("sources", [])
            related_docs = []

            for source in sources[:3]:  # Top 3 sources
                related_docs.append({
                    "title": source.get("metadata", {}).get("title", "Unknown"),
                    "type": source.get("metadata", {}).get("type", "manual"),
                    "relevance_score": source.get("score", 0.0)
                })

            # Step 5: Prepare follow-up suggestions
            followup_prompt = f"""
            사용자가 "{question}"에 대해 질문했습니다.
            이 질문과 관련하여 사용자가 추가로 궁금해할 수 있는 3가지 질문을 제안해주세요.
            """

            followup_suggestions = await self._llm_call(followup_prompt, temperature=0.6)

            logger.info(f"Usage question answered successfully")

            return {
                "success": True,
                "question": question,
                "answer": detailed_answer.get("content", ""),
                "related_documents": related_docs,
                "followup_suggestions": followup_suggestions.get("content", ""),
                "intent_analysis": intent_analysis.get("content", ""),
                "confidence": rag_result.get("confidence", 0.0),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to answer usage question: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _find_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-B-02: 담당자 정보 조회

        시스템 담당자 정보를 검색하여 제공

        Args:
            data: {
                "query": str (e.g., "A system 담당자는?"),
                "system_name": str (optional),
                "role": str (optional, e.g., "개발", "운영")
            }

        Returns:
            Dict: 담당자 정보
        """
        try:
            query = data.get("query", "")
            system_name = data.get("system_name")
            role = data.get("role")

            if not query and not system_name:
                return {
                    "success": False,
                    "error": "Query or system_name is required"
                }

            logger.info(f"Finding contact: {query or system_name}")

            # Step 1: Parse query to extract system name and role
            parse_prompt = f"""
            다음 질문에서 시스템 이름과 역할을 추출해주세요:
            질문: {query}

            추출 형식:
            - 시스템 이름: [시스템명]
            - 역할: [역할]

            명시되지 않은 항목은 "없음"으로 표시해주세요.
            """

            parsed = await self._llm_call(parse_prompt, temperature=0.2)

            # Step 2: Search contact information using RAG
            logger.info("Searching contact information...")

            search_query = query
            if system_name:
                search_query = f"{system_name} 담당자"
            if role:
                search_query += f" {role}"

            rag_result = await self._rag_query(
                query=search_query,
                collection_types=["contacts"],
                top_k=5
            )

            if not rag_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to search contact information",
                    "details": rag_result
                }

            # Step 3: Format contact information
            contacts = []
            sources = rag_result.get("sources", [])

            for source in sources:
                metadata = source.get("metadata", {})
                contacts.append({
                    "name": metadata.get("name", "Unknown"),
                    "role": metadata.get("role", "Unknown"),
                    "system": metadata.get("system", "Unknown"),
                    "email": metadata.get("email", ""),
                    "phone": metadata.get("phone", ""),
                    "team": metadata.get("team", ""),
                    "relevance_score": source.get("score", 0.0)
                })

            # Step 4: Generate summary
            summary_prompt = f"""
            담당자 정보를 요약해주세요:
            질문: {query}
            찾은 담당자 수: {len(contacts)}

            담당자 정보:
            {contacts[:3]}  # Top 3

            다음 형식으로 요약해주세요:
            - 주 담당자: [이름] ([역할])
            - 연락처: [이메일/전화]
            - 기타 관련 담당자: [목록]
            """

            summary = await self._llm_call(summary_prompt, temperature=0.4)

            logger.info(f"Found {len(contacts)} contacts")

            return {
                "success": True,
                "query": query,
                "system_name": system_name,
                "role": role,
                "contacts": contacts,
                "summary": summary.get("content", ""),
                "contact_count": len(contacts),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to find contact: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _request_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-B-03: 계정 발급 요청

        사용자 정보를 받아 ITS 티켓 생성

        Args:
            data: {
                "user_info": {
                    "name": str,
                    "email": str,
                    "department": str,
                    "manager": str
                },
                "system_name": str,
                "access_level": str (optional),
                "reason": str
            }

        Returns:
            Dict: 티켓 생성 결과
        """
        try:
            user_info = data.get("user_info", {})
            system_name = data.get("system_name", "")
            access_level = data.get("access_level", "standard")
            reason = data.get("reason", "")

            # Validate required fields
            if not user_info.get("name") or not user_info.get("email"):
                return {
                    "success": False,
                    "error": "User name and email are required"
                }

            if not system_name:
                return {
                    "success": False,
                    "error": "System name is required"
                }

            logger.info(f"Processing account request for {user_info.get('name')} - {system_name}")

            # Step 1: Validate request using LLM
            validation_prompt = f"""
            계정 발급 요청을 검증해주세요:

            사용자 정보:
            - 이름: {user_info.get('name')}
            - 이메일: {user_info.get('email')}
            - 부서: {user_info.get('department', '없음')}
            - 승인자: {user_info.get('manager', '없음')}

            시스템: {system_name}
            접근 권한: {access_level}
            요청 사유: {reason}

            다음을 확인해주세요:
            1. 필수 정보 누락 여부
            2. 요청의 타당성
            3. 보안 고려사항
            4. 승인이 필요한지 여부
            """

            validation = await self._llm_call(validation_prompt, temperature=0.3)

            # Step 2: Check if similar system exists
            system_info = await self._rag_query(
                query=f"{system_name} 시스템 정보",
                collection_types=["manuals", "contacts"],
                top_k=1
            )

            # Step 3: Generate ticket description
            ticket_description = f"""
계정 발급 요청

【신청자 정보】
- 이름: {user_info.get('name')}
- 이메일: {user_info.get('email')}
- 부서: {user_info.get('department', '미기재')}
- 승인자: {user_info.get('manager', '미기재')}

【시스템 정보】
- 시스템명: {system_name}
- 접근 권한: {access_level}

【요청 사유】
{reason}

【검증 결과】
{validation.get('content', '')}
"""

            # Step 4: Create ITS ticket (simulate)
            logger.info("Creating ITS ticket...")

            # In real implementation, this would call ITS Agent or ServiceNow MCP
            ticket = {
                "ticket_number": f"REQ{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": "Account Request",
                "title": f"계정 발급 요청 - {system_name} - {user_info.get('name')}",
                "description": ticket_description,
                "requester": user_info.get("name"),
                "requester_email": user_info.get("email"),
                "system": system_name,
                "access_level": access_level,
                "status": "Submitted",
                "priority": "Medium",
                "created_at": datetime.now().isoformat()
            }

            # Step 5: Generate confirmation message
            confirmation_prompt = f"""
            계정 발급 요청이 접수되었습니다.

            티켓 번호: {ticket['ticket_number']}
            시스템: {system_name}
            신청자: {user_info.get('name')}

            다음 단계와 예상 처리 시간을 안내하는 메시지를 작성해주세요.
            친절하고 명확하게 작성해주세요.
            """

            confirmation = await self._llm_call(confirmation_prompt, temperature=0.5)

            # Send notification
            await self._send_notification(
                subject=f"계정 발급 요청 접수: {ticket['ticket_number']}",
                message=confirmation.get("content", ""),
                recipients=[user_info.get("email")]
            )

            logger.info(f"Account request processed: {ticket['ticket_number']}")

            return {
                "success": True,
                "ticket": ticket,
                "validation": validation.get("content", ""),
                "confirmation_message": confirmation.get("content", ""),
                "system_info": system_info.get("answer", ""),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to process account request: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_biz_support_agent_instance = None


def get_biz_support_agent() -> BizSupportAgent:
    """BizSupportAgent 싱글톤 인스턴스 반환"""
    global _biz_support_agent_instance
    if _biz_support_agent_instance is None:
        _biz_support_agent_instance = BizSupportAgent()
    return _biz_support_agent_instance


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_agent():
        print("\n=== Testing Business Support Agent ===")
        agent = BizSupportAgent()

        # Test UC-B-01: Answer usage question
        print("\n--- Test UC-B-01: Usage Question ---")
        result = await agent.execute_task({
            "type": "answer_usage_question",
            "data": {
                "question": "Azure OpenAI API를 사용하는 방법을 알려주세요",
                "system_name": "AI Platform"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Answer preview: {result.get('answer', '')[:200]}...")
        print(f"Related docs: {len(result.get('related_documents', []))}")

        # Test UC-B-02: Find contact
        print("\n--- Test UC-B-02: Find Contact ---")
        result = await agent.execute_task({
            "type": "find_contact",
            "data": {
                "query": "API 플랫폼 개발팀 담당자는?",
                "system_name": "API Platform"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Contacts found: {result.get('contact_count', 0)}")

        # Test UC-B-03: Request account
        print("\n--- Test UC-B-03: Account Request ---")
        result = await agent.execute_task({
            "type": "request_account",
            "data": {
                "user_info": {
                    "name": "홍길동",
                    "email": "hong@company.com",
                    "department": "마케팅팀",
                    "manager": "김팀장"
                },
                "system_name": "CRM System",
                "access_level": "read-only",
                "reason": "고객 데이터 조회 및 분석 업무 수행"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Ticket number: {result.get('ticket', {}).get('ticket_number')}")

    asyncio.run(test_agent())
