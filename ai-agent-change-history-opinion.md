AI Agent 구축방안

Change Mgmt | 변경관리 자동화
정기/긴급 변경 요청서 등록, 변경계획 수립
테스트 시나리오 결과작성/동료평가/배포승인 요청/배포검토승인
소스배포, 배포후 점검(Test 및 배포점검Checklist 작성)

"A 시스템 성능 분석 해결"
"MEM/CPU 조정후 배포"
"replica 조정 후 배포"

✔ 반복/대화, 요청기반 동작

Change Mgmt
1) 변경 분석/요청
2) 변경계획서 작성
3) 테스트 시나리오 작성
4) 수동/자동테스트(✔)
5) 테스트 결과 작성
6) 동료평가/배포작성
7) 배포 승인
8) Check list 작성
9) 배포
10) 서비스 점검/Check list 점검

TOOL
변경요청등록
아래 ITS/보고서 Agent 활용 가능성
보고서작성/Local 파일 생성
동료평가/배포승인
Devops 배포
Service Monitoring Agent

제조 AI Platform
LLM1, LLM2, RAG/Vector DB, MCP

변경계획/시나리오/동료평가서/Check LIST

ITS 관리 시스템
SERVICE NOW MCP
크롤링

운영자 PC/VDI

Mail/SMS/Slack 등

✔ 각종 양식 표준화, MD 파일로?
✔ AI 코딩 도구를 활용한 문서작성 만으로 제한할지?
✔ 다양한 IT 관리 시스템
✔ 오프라인 관리 회사는?
✔ 시스템 학습? 산출물 RAG
✔ 소스 기반 분석? AI 코딩 도구
✔ 프로세스에 따른 동작
```

***

## 2. mermaid 다이어그램

```
graph TD
    A[변경요청등록] --> B[ITS/보고서 Agent]
    B --> C[보고서작성/Local 파일 생성]
    C --> D[동료평가/배포승인]
    D --> E[Devops 배포]
    E --> F[Service Monitoring Agent]
    F --> G[Mail/SMS/Slack 등]
    B --> H[ITS 관리 시스템]
    H --> I[SERVICE NOW]
    H --> J[MCP]
    H --> K[크롤링]
    D --> L[운영자 PC/VDI]
    L --> M[변경계획/시나리오/동료평가서/Check LIST]
    F --> N[제조 AI Platform]
    N --> O[LLM1]
    N --> P[LLM2]
    N --> Q[RAG/Vector DB]
    N --> R[MCP]
```

***

## 3. Markdown 파일 작성 예시 (`AI_Agent_Design.md`)

````markdown
# AI Agent 구축방안

## 1. 텍스트 요약

- 반복/대화, 요청기반 동작
- 변경관리 절차 (Change Mgmt)
    1. 변경 분석/요청
    2. 변경계획서 작성
    3. 테스트 시나리오 작성
    4. 수동/자동테스트
    5. 테스트 결과 작성
    6. 동료평가/배포작성
    7. 배포 승인
    8. Check list 작성
    9. 배포
    10. 서비스 점검/Check list 점검

- AI, DevOps, ITS 관리 시스템(SERVICE NOW, MCP 등)과 연동
- AI 코딩 도구, 시스템 학습/RAG, 문서 표준화(MD), 다양한 IT 관리 시스템 대응

---

## 2. 프로세스 다이어그램 (Mermaid)

```
graph TD
    A[변경요청등록] --> B[ITS/보고서 Agent]
    B --> C[보고서작성/Local 파일 생성]
    C --> D[동료평가/배포승인]
    D --> E[Devops 배포]
    E --> F[Service Monitoring Agent]
    F --> G[Mail/SMS/Slack 등]
    B --> H[ITS 관리 시스템]
    H --> I[SERVICE NOW]
    H --> J[MCP]
    H --> K[크롤링]
    D --> L[운영자 PC/VDI]
    L --> M[변경계획/시나리오/동료평가서/Check LIST]
    F --> N[제조 AI Platform]
    N --> O[LLM1]
    N --> P[LLM2]
    N --> Q[RAG/Vector DB]
    N --> R[MCP]
```
```