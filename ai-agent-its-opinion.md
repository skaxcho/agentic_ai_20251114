# AI Agent 구축방안

## 1. 이미지 내 텍스트

```
AI Agent 구축방안

ITS         |   요청/인시던트 처리 자동화
-------------------------------------------
ITS 구성정보 현행화, 변경사항 수정
SSL인증서 요청(발급요금청, 설치요청, 설치, 인증서 파일 설정, 결과 점검), 도메인 연장 발급 요청, 연장 결과 점검 신청 등
ITS/Serviceflow 요청접수, 배정, 진행확인(모니터링), 통보, 종료 처리 등 ITS를 이용한 처리업무

* “구성정보 현행화해줘”
* “인증서 발급요청 해결”
* “요청서 접수해줘”

ITS Agent
  1) ITS 기능 호출
  2) 관련 정보 사용자 입력

제조 AI Platform
  LLM1   LLM2   RAG/Vector DB   MCP

TOOL
  ITS MCP Client

ITS 관리 시스템
  SERVICE NOW MCP
  크롤링(X?)

# 오른쪽 질문박스
✓ ITS 에서 MCP 제공하나?
✓ 없다면?
```

***

## 2. Mermaid 아키텍처 다이어그램

아래는 위 내용을 바탕으로 작성한 mermaid architecture diagram 예시입니다.

```mermaid
flowchart TD
    subgraph 제조_AI_Platform
        LLM1
        LLM2
        RAG_Vector_DB[RAG/Vector DB]
        MCP
    end

    subgraph ITS_Agent["ITS Agent"]
        ITS_Function["ITS 기능 호출"]
        User_Input["관련 정보 사용자 입력"]
    end

    subgraph TOOL
        MCP_Client["ITS MCP Client"]
    end

    subgraph ITS_관리_시스템
        ServiceNowMCP["SERVICE NOW MCP"]
        CRAWLING["크롤링 (X?)"]
    end

    LLM1-->|정보/지식 전달|ITS_Agent
    LLM2-->|정보/지식 전달|ITS_Agent
    RAG_Vector_DB-->|문서검색|ITS_Agent
    MCP-->|명령/상태 연계|ITS_Agent

    ITS_Agent-->|기능 호출 및 정보 입력|MCP_Client
    MCP_Client-->|연동|ServiceNowMCP
    MCP_Client-->|연동(예정)|CRAWLING
```

***

## 3. Markdown 파일 예시

```markdown
# AI Agent 구축방안

## 이미지 내 텍스트
- ITS 구성정보 현행화, 변경사항 수정
- SSL인증서 요청(발급요금청, 설치요청, 설치, 인증서 파일 설정, 결과 점검), 도메인 연장 발급 요청, 연장 결과 점검 신청 등
- ITS/Serviceflow 요청접수, 배정, 진행확인(모니터링), 통보, 종료 처리 등 ITS를 이용한 처리업무
- 예시 요청
    - “구성정보 현행화해줘”
    - “인증서 발급요청 해결”
    - “요청서 접수해줘”

## 블록 구성
- 제조 AI Platform: LLM1, LLM2, RAG/Vector DB, MCP
- ITS Agent: ITS 기능 호출, 관련 정보 사용자 입력
- TOOL: ITS MCP Client
- ITS 관리 시스템: SERVICE NOW MCP, 크롤링(X?)

## 시스템 아키텍처 다이어그램

```
flowchart TD
    subgraph 제조_AI_Platform
        LLM1
        LLM2
        RAG_Vector_DB[RAG/Vector DB]
        MCP
    end

    subgraph ITS_Agent["ITS Agent"]
        ITS_Function["ITS 기능 호출"]
        User_Input["관련 정보 사용자 입력"]
    end

    subgraph TOOL
        MCP_Client["ITS MCP Client"]
    end

    subgraph ITS_관리_시스템
        ServiceNowMCP["SERVICE NOW MCP"]
        CRAWLING["크롤링 (X?)"]
    end

    LLM1-->|정보/지식 전달|ITS_Agent
    LLM2-->|정보/지식 전달|ITS_Agent
    RAG_Vector_DB-->|문서검색|ITS_Agent
    MCP-->|명령/상태 연계|ITS_Agent

    ITS_Agent-->|기능 호출 및 정보 입력|MCP_Client
    MCP_Client-->|연동|ServiceNowMCP
    MCP_Client-->|연동(예정)|CRAWLING
```
```