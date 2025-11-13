# AI Agent 구축방안

## 주요 텍스트(내용 정리)

**Report**  
회의록/보고서 자동화  
- Weekly/Monthly 등 정기업무 회의 사안 준비, 회의 참여, 보고서/회의록 작성 등  
- 비정기 업무 회의 시안 준비, 회의참여, 데이터 취합, 회의록 작성 등  
- 현황조사/취합

**작업일지 파일/Text로  
원드라이브 경로에 주간보고 작성해줘**  
- "원드라이브 링크에 시스템 정보 취합 파일 확인하고, 필요한 정보는 ITS/우리 시스템 정보 파일/RAG 참고해서 작성해줘"  
- "모르는 정보는 물어보고, 파일에 쓰기전에 작성내용 알려줘"

### Report Agent 동작 단계
1) 작성할 양식 필요 Data 확인  
2) Data 소스 읽기  
  - 파일/voice  
  - RAG/DB/ITS?  
3) 보고서 작성하기  
  - 로컬/원격

**Tool (도구)**  
- File 접근/One Drive MCP  
- Voice

**시스템 연동**
- 공용 Repo(각종 양식/OneDrive)
- 운영자 PC/VDI (File)

**플랫폼 구성 요소**  
- LLM1, LLM2  
- RAG/Vector DB  
- MCP

**주요 메모(노란 강조 텍스트)**  
- 프롬프트 외 Input 방식은?  
- 보고서의 범위를 한정하면 쉽지 않을까? 취합으로?  
- Voice 방식 제공? 단순 파일 업로드만?  
- 자신의 업무 TOOL 연계한 업무일지 자동생성 → 주간보고 → 월간보고??

----------------------

## Mermaid 다이어그램 (논리구조)

```mermaid
flowchart TD
    subgraph 제조 AI Platform
        LLM1
        LLM2
        RAG_DB[RAG/Vector DB]
        MCP
    end

    subgraph Report Agent
        A1[양식 필요 데이터 확인]
        A2[Data 소스 읽기<br/>- 파일/voice<br/>- RAG/DB/ITS]
        A3[보고서 작성<br/>- 로컬/원격]
    end

    TOOL[TOOL]
    FILE[File 접근<br/>One Drive/MCP]
    VOICE[Voice]
    공용Repo[공용 Repo<br/>- 각종 양식<br/>- One Drive]
    운영자PC[운영자 PC/VDI<br/>FILE]

    LLM1 --> Report Agent
    LLM2 --> Report Agent
    RAG_DB --> Report Agent
    MCP --> Report Agent

    Report Agent --> TOOL
    TOOL --> FILE
    TOOL --> VOICE
    FILE --> 공용Repo
    FILE --> 운영자PC

    classDef highlight fill:#fff2cc,stroke:#d6b656,stroke-width:2px;
    classDef note fill:#fcf8e3,stroke:#fabd01,stroke-width:1px;

    %% (주요 주석 및 추가 질문 요소는 MD 주석 또는 별도 표시)
```