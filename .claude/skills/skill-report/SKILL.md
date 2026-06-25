---
name: skill-report
description: skill 사용 기록(.claude/skill-usage.log)을 분석해 화려한 HTML 리포트를 만들고 브라우저로 띄운다. 사용자가 "skill 사용 리포트", "skill 기록 보여줘", "리포트 띄워줘"라고 요청할 때 사용한다.
user-invocable: true
allowed-tools:
  - Bash(python3:*)
---

# /skill-report — skill 사용 리포트 스킬

`hook`이 남긴 `.claude/skill-usage.log`를 읽어, 통계 카드 · skill별 사용량 막대그래프 ·
전체 타임라인이 담긴 화려한 HTML 리포트를 생성하고 기본 브라우저로 연다.

HTML 생성과 브라우저 열기는 함께 번들된 `generate_report.py`가 모두 처리한다.
스킬이 할 일은 이 스크립트를 실행하고 결과를 사용자에게 보고하는 것뿐이다.

---

## 진행 순서

### 1. 리포트 생성 스크립트 실행
프로젝트 루트에서 아래를 실행한다. 스크립트는 자기 위치로 프로젝트 루트를 찾으므로
실행 디렉터리는 상관없다.

```
python3 .claude/skills/skill-report/generate_report.py
```

### 2. 결과 보고
스크립트가 stdout으로 출력하는 요약(전체 호출 수, 고유 skill 수, 상위 사용 skill,
리포트 경로, 브라우저 열기 성공 여부)을 사용자에게 그대로 정리해 전달한다.

- 브라우저가 자동으로 열렸으면 그 사실을 알린다.
- 브라우저 열기에 실패했으면 출력된 리포트 경로(`.claude/skill-usage-report.html`)를
  직접 열도록 안내한다.

---

## 예외 처리

- **로그 파일이 없거나 비어 있을 때**: 스크립트가 "기록이 비어 있습니다" 경고를 출력한다.
  이 경우 아직 skill을 사용한 적이 없거나 기록 hook이 활성화되지 않은 것이다.
  사용자에게 skill을 한 번 사용한 뒤 다시 실행하라고 안내한다.
  (hook은 `.claude/settings.json`의 `PreToolUse`/`Skill` 매처에 정의되어 있다.)
- **생성된 리포트 파일(`.claude/skill-usage-report.html`)**: 매번 덮어쓰는 산출물이라
  `.gitignore`에 포함되어 커밋되지 않는다.
