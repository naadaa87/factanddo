# FACT&DO (팩트앤두) — factanddo.com

**검증에서 실행까지.**
① FACT — 부업·수익화 강의의 주장과 확인된 사실을 나눠 보여주는 검증 (E0–E5 증빙 레벨)
② DO — 4주 실행그룹 (목표 · 주간 체크인 · 산출물 · 결과로그)

GitHub `main` 브랜치에 커밋하면 Cloudflare Pages가 1~2분 안에 자동으로 다시 배포합니다.

---

## 1. 평소 운영은 관리자 화면에서

**https://factanddo.com/admin/**

| 메뉴 | 하는 일 |
|---|---|
| 현황판 | 공개·준비 중 대상 수, 오늘 할 일(재점검 도래·공개 기준 미달·통보 필요·회신 기한), 최근 반영 기록 |
| 검증 대상 | 강의·플랫폼·특강 등록과 수정. 주장 → 확인된 사실 → 미확인을 나눠 적고, 상태(후보·접수·초안·공개·보류·반려)를 관리 |
| 외부 후기 | 블로그·수강평 등 공개 후기를 출처 링크와 요약으로 등록 (원문 복사 금지) |
| 공공기록·보도 | 소비자원 통계, 언론 보도 등 |
| 제보·이의제기 | 받은 요청의 처리 경과 기록 (개인정보는 적지 않음) |
| 생태계 서비스 | `/explore/` 에 나오는 주변 서비스 목록 |
| 사이트 설정 | 문의 메일, 접수 양식 주소, 사전등록 양식, 상단 공지 |
| 연결·백업 | GitHub 토큰 연결, 전체 백업 내려받기 |

### 처음 한 번: GitHub 토큰 연결 (3분)

관리자 화면은 서버 없이 이 저장소에 직접 저장합니다. 그래서 **이 저장소에만 쓸 수 있는 토큰**이 필요합니다.

1. github.com 로그인 → 오른쪽 위 프로필 → **Settings** → 맨 아래 **Developer settings**
2. **Personal access tokens → Fine-grained tokens → Generate new token**
3. Repository access: **Only select repositories** → `naadaa87/factanddo` 만 선택
4. Permissions → Repository permissions → **Contents: Read and write**
5. Generate 후 나온 토큰을 관리자 화면 **연결·백업** 메뉴에 붙여 넣기

토큰은 그 브라우저에만 저장됩니다. 토큰이 없으면 관리자 화면은 읽기 전용으로 열립니다.

### 공개 기준 (자동 점검)

상태를 ‘공개’로 바꾸려면 아래가 모두 충족돼야 저장됩니다.

- 이름·유형·한 줄 소개가 있다
- 주장 또는 확인된 사실이 1개 이상이고 모두 출처 URL이 있다
- 출처 목록과 확인일이 있다
- 미확인 항목을 적었다
- 광고·협찬 관계가 없음을 확인했다
- **판정을 붙였다면 당사자에게 통보했다** (‘판정 전’이면 공개 정보 정리만 싣는 것이므로 통과)

---

## 2. 저장소 구성

| 경로 | 역할 |
|---|---|
| `data/targets.json` | 검증 대상 |
| `data/reviews.json` | 외부 공개 후기 (요약 + 링크) |
| `data/records.json` | 공공기록·보도 |
| `data/cases.json` | 제보·이의제기 처리 경과 |
| `data/services.json` | 생태계 서비스 |
| `data/site.json` | 사이트 설정 (메일·양식 주소·공지) |
| `build.py` | 사이트 생성기 (표준 라이브러리만 사용) |
| `pages_fact.py` | 검증 대상·후기·공공기록·제보 페이지 |
| `content_ko.py` | 정책 초안, E0–E5 기준, 평가 7차원 |
| `assets/` | 스타일·스크립트·이미지 (`admin.js`, `admin.css` 는 관리자 화면) |
| `dist/` | 빌드 결과물 (자동 생성, 커밋하지 않음) |

로컬 미리보기: `python3 build.py` → `cd dist && python3 -m http.server 8000`

Cloudflare Pages 빌드 설정: Build command `python3 build.py` · Output `dist` · `PYTHON_VERSION = 3.12` 이상

## 3. 생성되는 페이지

홈 `/` · 검증 대상 `/fact/` + 대상별 상세 `/fact/<id>/` · 팩트리뷰 `/reviews/` + 작성 `/reviews/new/` ·
실행그룹 `/groups/` · 결과 `/results/` · 검증 기준 `/standards/` · 공공기록·보도 `/records/` ·
제보·정정·이의제기 `/report/` · 생태계 탐색 `/explore/` · 소개 · 사전등록 · 정책 3종 · 관리자 `/admin/` ·
`sitemap.xml` · `feed.xml` · `robots.txt` · 네이버 소유확인 파일

## 4. 편집 원칙 (코드에 반영된 것)

- 주장과 확인된 사실을 분리하고, 모르는 것은 ‘미확인’으로 적는다
- 모든 사실에 출처 URL과 확인일을 붙인다
- 외부 후기는 원문을 옮기지 않고 요약과 링크만 싣는다. 본문을 못 읽은 글은 링크만 안내한다
- 수집한 후기는 모두 E0(미인증)으로 표시한다
- 판정은 당사자 통보 뒤에만 공개한다
- 허위 평점·이용자 수·후기 수를 만들지 않는다. 평가점수와 검색 순위는 판매하지 않는다

© 2026 팩트앤두 · FACT&DO
