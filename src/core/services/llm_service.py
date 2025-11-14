"""
Azure OpenAI Service Module

이 모듈은 Azure OpenAI API와의 통합을 제공합니다.
LLM 호출, 임베딩 생성, Function Calling 등을 지원합니다.
"""

from openai import AzureOpenAI, AsyncAzureOpenAI
from typing import List, Dict, Any, Optional, AsyncIterator
import os
from dotenv import load_dotenv
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError, APITimeoutError

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Azure OpenAI 통합 서비스"""

    def __init__(self):
        """Initialize Azure OpenAI Service"""
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

        # Validate configuration
        if not all([self.api_key, self.azure_endpoint]):
            raise ValueError(
                "Azure OpenAI configuration is incomplete. "
                "Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables."
            )

        # Initialize clients
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )

        self.async_client = AsyncAzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )

        logger.info(f"AzureOpenAIService initialized with endpoint: {self.azure_endpoint}")

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        wait=wait_exponential(min=1, max=60),
        stop=stop_after_attempt(5)
    )
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        채팅 완성 API 호출

        Args:
            messages: 메시지 리스트 [{"role": "user", "content": "..."}]
            temperature: 온도 파라미터 (0.0-1.0)
            max_tokens: 최대 토큰 수
            functions: Function calling 정의 (선택적)
            function_call: Function call 모드 (선택적)

        Returns:
            Dict containing:
                - content: 생성된 텍스트
                - function_call: Function call 정보 (있는 경우)
                - usage: 토큰 사용량
                - model: 사용된 모델
                - finish_reason: 완료 이유

        Raises:
            Exception: API 호출 실패 시
        """
        try:
            kwargs = {
                "model": self.deployment_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            if functions:
                kwargs["functions"] = functions
                kwargs["function_call"] = function_call or "auto"

            logger.debug(f"Calling Azure OpenAI with {len(messages)} messages")

            response = self.client.chat.completions.create(**kwargs)

            result = {
                "content": response.choices[0].message.content,
                "function_call": None,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }

            # Check for function call
            if hasattr(response.choices[0].message, 'function_call') and response.choices[0].message.function_call:
                result["function_call"] = {
                    "name": response.choices[0].message.function_call.name,
                    "arguments": response.choices[0].message.function_call.arguments
                }

            logger.info(f"Chat completion successful. Tokens used: {result['usage']['total_tokens']}")

            return result

        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded. Retrying... Error: {str(e)}")
            raise  # Will be retried by tenacity
        except APITimeoutError as e:
            logger.warning(f"API timeout. Retrying... Error: {str(e)}")
            raise  # Will be retried by tenacity
        except Exception as e:
            logger.error(f"Azure OpenAI API call failed: {str(e)}")
            raise Exception(f"Azure OpenAI API 호출 실패: {str(e)}")

    async def async_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        비동기 채팅 완성 API 호출

        Args:
            messages: 메시지 리스트
            temperature: 온도 파라미터
            max_tokens: 최대 토큰 수
            functions: Function calling 정의
            function_call: Function call 모드

        Returns:
            Dict containing completion results
        """
        try:
            kwargs = {
                "model": self.deployment_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            if functions:
                kwargs["functions"] = functions
                kwargs["function_call"] = function_call or "auto"

            response = await self.async_client.chat.completions.create(**kwargs)

            result = {
                "content": response.choices[0].message.content,
                "function_call": None,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }

            if hasattr(response.choices[0].message, 'function_call') and response.choices[0].message.function_call:
                result["function_call"] = {
                    "name": response.choices[0].message.function_call.name,
                    "arguments": response.choices[0].message.function_call.arguments
                }

            return result

        except Exception as e:
            logger.error(f"Async Azure OpenAI API call failed: {str(e)}")
            raise Exception(f"Azure OpenAI API 호출 실패: {str(e)}")

    async def streaming_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """
        스트리밍 채팅 완성

        Args:
            messages: 메시지 리스트
            temperature: 온도 파라미터
            max_tokens: 최대 토큰 수

        Yields:
            생성된 텍스트 chunk
        """
        try:
            logger.debug("Starting streaming completion")

            response = await self.async_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            logger.info("Streaming completion finished")

        except Exception as e:
            logger.error(f"Streaming API call failed: {str(e)}")
            raise Exception(f"Streaming API 호출 실패: {str(e)}")

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        wait=wait_exponential(min=1, max=60),
        stop=stop_after_attempt(5)
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            List[float]: 임베딩 벡터 (1536 차원)

        Raises:
            Exception: API 호출 실패 시
        """
        try:
            # Clean text
            text = text.replace("\n", " ").strip()

            if not text:
                raise ValueError("Text for embedding cannot be empty")

            logger.debug(f"Generating embedding for text of length {len(text)}")

            response = self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text
            )

            embedding = response.data[0].embedding

            logger.info(f"Embedding generated successfully. Dimension: {len(embedding)}")

            return embedding

        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded for embedding. Retrying... Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise Exception(f"Embedding 생성 실패: {str(e)}")

    async def async_generate_embedding(self, text: str) -> List[float]:
        """
        비동기 텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            List[float]: 임베딩 벡터
        """
        try:
            text = text.replace("\n", " ").strip()

            if not text:
                raise ValueError("Text for embedding cannot be empty")

            response = await self.async_client.embeddings.create(
                model=self.embedding_deployment,
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Async embedding generation failed: {str(e)}")
            raise Exception(f"Embedding 생성 실패: {str(e)}")

    def function_calling(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        function_call: str = "auto"
    ) -> Dict[str, Any]:
        """
        Function Calling

        Args:
            messages: 메시지 리스트
            functions: Function 정의 리스트
            function_call: "auto", "none", 또는 {"name": "function_name"}

        Returns:
            Dict containing:
                - function_name: 호출할 함수 이름
                - arguments: 함수 인자 (JSON string)
                - content: LLM 응답 (function call이 없는 경우)

        Raises:
            Exception: API 호출 실패 시
        """
        response = self.chat_completion(
            messages=messages,
            functions=functions,
            function_call=function_call
        )

        if response["function_call"]:
            return {
                "function_name": response["function_call"]["name"],
                "arguments": response["function_call"]["arguments"],
                "content": None
            }
        else:
            return {
                "function_name": None,
                "arguments": None,
                "content": response["content"]
            }

    def count_tokens(self, text: str) -> int:
        """
        토큰 수 추정 (간단한 방법)

        Args:
            text: 텍스트

        Returns:
            int: 추정 토큰 수
        """
        # Simple estimation: ~4 characters per token for English
        # This is a rough estimate. For accurate counting, use tiktoken library
        return len(text) // 4

    def validate_connection(self) -> bool:
        """
        Azure OpenAI 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            self.chat_completion(test_messages, max_tokens=10)
            logger.info("Azure OpenAI connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI connection validation failed: {str(e)}")
            return False


# Singleton instance
_llm_service_instance = None


def get_llm_service() -> AzureOpenAIService:
    """
    LLMService 싱글톤 인스턴스 반환

    Returns:
        AzureOpenAIService: LLM 서비스 인스턴스
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = AzureOpenAIService()
    return _llm_service_instance


if __name__ == "__main__":
    # Test the service
    logging.basicConfig(level=logging.INFO)

    try:
        llm_service = AzureOpenAIService()

        # Test chat completion
        print("\n=== Testing Chat Completion ===")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Azure OpenAI에 대해 간단히 설명해줘"}
        ]
        result = llm_service.chat_completion(messages)
        print(f"Response: {result['content']}")
        print(f"Tokens used: {result['usage']['total_tokens']}")

        # Test embedding
        print("\n=== Testing Embedding ===")
        embedding = llm_service.generate_embedding("This is a test sentence for embedding.")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")

        # Test connection validation
        print("\n=== Testing Connection Validation ===")
        is_valid = llm_service.validate_connection()
        print(f"Connection valid: {is_valid}")

    except Exception as e:
        print(f"Error: {str(e)}")
