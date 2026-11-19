# -*- coding: utf-8 -*-
"""
FACT&DO (팩트앤두) 정적 사이트 생성기
====================================
- 실행:  python3 build.py   →  dist/ 폴더에 전체 사이트가 생성됩니다.
- Cloudflare Pages 빌드 설정:  Build command = python3 build.py  /  Output = dist
- 표준 라이브러리만 사용합니다(추가 설치 불필요).

자주 수정하는 곳
----------------
1) 아래 CONFIG        : 도메인, 사전등록 폼 주소, 오픈채팅, 이메일, 기준일
2) data/services.json : 탐색 페이지 데이터
3) content_ko.py      : 정책 초안·검증 기준 원문
"""
import json, os, shutil, html, types, hashlib
import content_ko as C
import pages_fact as F

# ─────────────────────────────────────────────────────────────
# CONFIG — 여기만 고치면 사이트 전반에 반영됩니다
# ─────────────────────────────────────────────────────────────
CONFIG = {
    "NAME_KO": "팩트앤두",
    "NAME_EN": "FACT&DO",
    "SLOGAN": "검증에서 실행까지.",
    "TAGLINE": "검증하고, 함께 실행하고, 결과로 증명하다.",
    # 도메인 연결 후 "https://factanddo.com" 으로 바꾸고 커밋하세요.
    "BASE_URL": "https://factanddo.com",
    # Tally/구글폼 등 사전등록 폼 주소. 만들기 전에는 "" 로 두면 '준비 중' 안내가 표시됩니다.
    "WAITLIST_FORM_URL": "",
    # 1기 실행그룹 카카오 오픈채팅 링크. 없으면 "" 유지.
    "OPENCHAT_URL": "",
    # 문의 이메일. 없으면 "" 유지(화면에 '준비 중' 표시).
    "CONTACT_EMAIL": "",
    # 데이터 기준일(탐색 페이지 하단 표기)
    "DATA_DATE": "2026-07-19",
    # 네이버 서치어드바이저 사이트 소유확인 코드 (메타 태그 방식)
    "NAVER_VERIFY": "a75cc76e443211b16ab71151f4f2e661ad7e75f2",
    # 네이버 소유확인 HTML 파일명 (파일 업로드 방식 — 둘 중 하나만 인식되면 됩니다)
    "NAVER_VERIFY_FILE": "naverec3ee427f0af386a5824d93c3ad69a61.html",
    "YEAR": "2026",
}

# data/site.json 에 값이 있으면 위 CONFIG 를 덮어씁니다(관리자 화면 > 사이트 설정에서 고치는 값).
try:
    with open("data/site.json", encoding="utf-8") as _f:
        for _k, _v in json.load(_f).items():
            if not _k.startswith("_") and _v not in ("", None):
                CONFIG[_k] = _v
except FileNotFoundError:
    pass
for _k in ("REPORT_FORM_URL", "NOTICE", "GITHUB_REPO", "GITHUB_BRANCH"):
    CONFIG.setdefault(_k, "")

DIST = "dist"
E = html.escape

def ver(name):
    """파일 내용이 바뀌면 주소 뒤 ?v= 값이 바뀌어, 방문자 브라우저가 옛 파일을 계속 쓰지 않게 합니다."""
    try:
        with open(os.path.join("assets", name), "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except FileNotFoundError:
        return CONFIG["DATA_DATE"].replace("-", "")

def data_ver():
    h = hashlib.md5()
    for n in sorted(os.listdir("data")):
        with open(os.path.join("data", n), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:8]

# ─────────────────────────────────────────────────────────────
# 공통 레이아웃
# ─────────────────────────────────────────────────────────────
MARK_SVG = """<svg class="mark" viewBox="0 0 100 64" aria-hidden="true" focusable="false">
  <rect x="4" y="6" width="52" height="52" rx="12" fill="none" stroke="var(--navy)" stroke-width="7.5"/>
  <path d="M18 33 L27 42 L42 24" fill="none" stroke="var(--navy)" stroke-width="7.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M68 16 L88 32 L68 48" fill="none" stroke="var(--coral)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

WORDMARK = '<span class="wm"><b class="wm-f">FACT</b><b class="wm-a">&amp;</b><b class="wm-d">DO</b></span>'

NAV_ITEMS = [
    ("/fact/", "검증 대상"),
    ("/reviews/", "팩트리뷰"),
    ("/groups/", "실행그룹"),
    ("/results/", "결과"),
    ("/standards/", "검증 기준"),
]

def header(active=""):
    links = "".join(
        f'<a href="{p}"{" class=\"on\"" if p == active else ""}>{label}</a>'
        for p, label in NAV_ITEMS
    )
    return f"""<header class="site-head">
  <div class="wrap head-in">
    <a class="brand" href="/" aria-label="{CONFIG['NAME_KO']} 홈">{MARK_SVG}{WORDMARK}</a>
    <button id="nav-toggle" class="nav-toggle" aria-label="메뉴 열기" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav id="site-nav" class="site-nav">
      {links}
      <a class="btn btn-coral nav-cta" href="/waitlist/">사전등록</a>
    </nav>
  </div>
</header>{notice_bar()}"""

def notice_bar():
    n = CONFIG.get("NOTICE", "")
    return f'<div class="notice-bar"><div class="wrap">{E(n)}</div></div>' if n else ""

def footer():
    email = CONFIG["CONTACT_EMAIL"]
    contact = (f'<a href="mailto:{E(email)}">{E(email)}</a>' if email
               else '<span class="dim">문의 채널 준비 중</span>')
    chat = (f' · <a href="{E(CONFIG["OPENCHAT_URL"])}" rel="noopener" target="_blank">오픈채팅</a>'
            if CONFIG["OPENCHAT_URL"] else "")
    return f"""<footer class="site-foot">
  <div class="wrap foot-grid">
    <div>
      <div class="foot-brand">{MARK_SVG}{WORDMARK}</div>
      <p class="foot-slogan">{E(CONFIG['SLOGAN'])}</p>
      <p class="foot-desc">부업·수익화 교육 검증과 4주 실행그룹.<br>확인 가능한 근거로 선택하고, 실행과 결과로 다시 사실을 만듭니다.</p>
    </div>
    <div class="foot-links">
      <b>서비스</b>
      <a href="/fact/">검증 대상</a><a href="/reviews/">팩트리뷰</a><a href="/explore/">생태계 탐색</a><a href="/groups/">실행그룹</a><a href="/results/">결과 데이터</a>
    </div>
    <div class="foot-links">
      <b>신뢰</b>
      <a href="/standards/">검증 기준</a><a href="/records/">공공기록·보도</a><a href="/report/">제보·정정·이의제기</a><a href="/about/">소개</a>
    </div>
    <div class="foot-links">
      <b>정책</b>
      <a href="/policies/terms/">이용약관</a><a href="/policies/privacy/">개인정보 처리방침</a><a href="/policies/community/">커뮤니티 가이드</a><a href="/waitlist/">사전등록</a>
    </div>
  </div>
  <div class="wrap foot-base">
    <span>© <span id="year">{CONFIG['YEAR']}</span> {E(CONFIG['NAME_KO'])} · {E(CONFIG['NAME_EN'])}</span>
    <span>문의: {contact}{chat}</span>
    <span class="dim">평가점수와 검색 순위는 판매하지 않습니다</span>
  </div>
</footer>"""

def naver_meta():
    code = CONFIG.get("NAVER_VERIFY", "")
    return f'<meta name="naver-site-verification" content="{E(code)}" />' if code else ""

def page(path, title, desc, body, active="", extra_head=""):
    url = CONFIG["BASE_URL"].rstrip("/") + path
    full_title = f"{title} · {CONFIG['NAME_KO']} {CONFIG['NAME_EN']}" if path != "/" else title
    doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
{naver_meta()}
<link rel="canonical" href="{E(url)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{E(full_title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:image" content="{E(CONFIG['BASE_URL'].rstrip('/'))}/assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="/favicon-64.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@ibm/plex-mono@1.1.0/css/ibm-plex-mono-all.min.css">
<link rel="stylesheet" href="/assets/style.css?v={ver('style.css')}">
<link rel="alternate" type="application/rss+xml" title="{E(CONFIG['NAME_KO'])} 검증 대상" href="/feed.xml">
<meta property="og:site_name" content="{E(CONFIG['NAME_KO'])} {E(CONFIG['NAME_EN'])}">
<meta property="og:locale" content="ko_KR">
{extra_head}
</head>
<body>
{header(active)}
<main>
{body}
</main>
{footer()}
<script src="/assets/data.js?v={data_ver()}"></script>
<script src="/assets/app.js?v={ver('app.js')}"></script>
<script defer src="https://choisijun.com/k1.js" integrity="sha384-E7Xl7wiU1vNu5AUY41kJB1uV52L+UEvqwYRzRj4zdaBGAeyRfCll926ETRo39Jm6" crossorigin="anonymous"></script>
</body>
</html>"""
    out = os.path.join(DIST, path.lstrip("/"))
    if path.endswith("/"):
        os.makedirs(out, exist_ok=True)
        out = os.path.join(out, "index.html")
    else:
        os.makedirs(os.path.dirname(out) or DIST, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    return path

# ─────────────────────────────────────────────────────────────
# 재사용 컴포넌트
# ─────────────────────────────────────────────────────────────
def evidence_meter(active_upto=5, small=False):
    """E0–E5 증빙 레벨 미터. active_upto 이하 칸이 채워집니다."""
    cells = ""
    for i in range(6):
        on = " on" if i <= active_upto else ""
        cells += f'<span class="ev-cell{on}"><i>E{i}</i></span>'
    return f'<div class="ev-meter{" ev-sm" if small else ""}" role="img" aria-label="증빙 레벨 E0부터 E5까지">{cells}</div>'

def sec_head(eyebrow, title, lead="", tone=""):
    lead_html = f'<p class="sec-lead">{lead}</p>' if lead else ""
    return f'<div class="sec-head"><span class="eyebrow {tone}">{E(eyebrow)}</span><h2>{title}</h2>{lead_html}</div>'

def beta_note(text, tag="안내"):
    return f'<p class="beta-note"><span class="beta-tag">{tag}</span>{text}</p>'

# ─────────────────────────────────────────────────────────────
# 페이지: 홈
# ─────────────────────────────────────────────────────────────
def build_home(fact_sec=""):
    loop = "".join(
        f'<li class="loop-step"><b>{i}</b><span>{t}</span><small>{s}</small></li>'
        for i, (t, s) in enumerate([
            ("탐색·비교", "과정/주제 선택"),
            ("팩트리뷰", "구매·수료·맥락"),
            ("DO 그룹", "목표·주간 실행"),
            ("실행로그", "피드백·산출물"),
            ("결과 데이터", "시간·비용·성과"),
        ], 1)
    )
    problems = "".join(
        f'<div class="card prob-card"><b>{t}</b><p>{d}</p></div>'
        for t, d in [
            ("신뢰 비용", "플랫폼 내부 후기와 홍보성 후기를 구분하기 어렵습니다. 관계 공개와 구매·수료 인증으로 나눕니다."),
            ("비용 착시", "강의료만 보이고 광고비·도구비·재고·외주비가 숨습니다. 총투입비용과 주당 시간을 표준화합니다."),
            ("성과 착시", "매출이 순이익처럼 제시되고 성공 사례만 강조됩니다. 매출·직접비·순수익·기간·표본을 분리합니다."),
            ("실행 단절", "수강 후 혼자 실행하다 멈춥니다. 4주 그룹, 주간 체크인, 동료 피드백, 데모데이로 잇습니다."),
        ]
    )
    rhythm = "".join(
        f'<tr><td class="mono">{d}</td><td>{a}</td></tr>'
        for d, a in [
            ("시작 전", "시작 조건·목표·가용 시간·예산 선언"),
            ("월요일", "이번 주 한 가지 핵심 목표 설정"),
            ("수요일", "진행률·막힌 점·도움 요청 체크인"),
            ("금요일", "산출물 공개와 동료 피드백"),
            ("주말", "회고와 다음 주 수정"),
            ("4주차", "데모데이 · 성과/중단 사유 공유"),
        ]
    )
    journeys = "".join(
        f'<div class="card j-card"><span class="j-tag {tone}">{tag}</span><b>{t}</b><p>{d}</p></div>'
        for tag, tone, t, d in [
            ("구매 전", "t-cobalt", "결제하기 전에 확인합니다", "과정 검색 → 비교함 → 조건이 비슷한 리뷰 확인 → 구매 또는 보류 결정. 결정 이유가 기록으로 남습니다."),
            ("수강 후", "t-cobalt", "들었다면 실행으로 잇습니다", "구매·수료 인증 → 강의 연동 그룹 → 주간 실행 → 결과 로그 → 30/90일 후기 업데이트."),
            ("강의 없이", "t-coral", "사기 전에 4주 실험합니다", "주제 선택 → 4주 실험 그룹 → 산출물·첫 거래 검증 → 필요한 교육만 역으로 탐색."),
        ]
    )
    cats = "".join(
        f'<div class="card cat-card"><b>{t}</b><p>{d}</p><small class="mono">{r}</small></div>'
        for t, d, r in [
            ("AI · 노코드 · 자동화", "변화가 빨라 버전·현실성 검증 수요가 큽니다.", "자동화 완성 · 배포 · 업무시간 단축"),
            ("콘텐츠 · 크리에이터", "블로그·유튜브·전자책·제휴 등 성과 주장이 많습니다.", "첫 콘텐츠 · 구독 · 판매 · 광고 수익"),
            ("이커머스 · 셀러", "강의료 외 광고·재고·도구비가 커 총비용 검증이 필요합니다.", "첫 상품등록 · 주문 · 매출 · 순수익"),
        ]
    )
    body = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <span class="eyebrow">부업·수익화 교육 검증 × 4주 실행그룹</span>
      <h1>검증에서<br><em>실행</em>까지.</h1>
      <p class="hero-lead">과장된 약속을 걸러내고, 비슷한 목표를 가진 사람들과 함께 실행하며,
      시간·비용·과정·성과를 <b>다음 사람을 위한 데이터</b>로 남깁니다.</p>
      <div class="hero-cta">
        <a class="btn btn-coral" href="/fact/">검증 대상 보기</a>
        <a class="btn btn-ghost" href="/standards/">검증 기준 먼저 보기</a>
      </div>
      <div class="hero-ev">{evidence_meter(3, small=True)}<span>구매 → 수료 → 실행 → 거래 순서로 증빙 범위를 표시합니다</span></div>
    </div>
    <figure class="hero-shot">
      <div class="browser"><span></span><span></span><span></span></div>
      <img src="/assets/img/ui-concept.jpg" alt="팩트앤두 서비스 화면 시안 — 과정 비교와 실행그룹 화면" width="1280" height="853" loading="eager">
      <figcaption>서비스 화면 시안 · 실제 화면은 구축 단계에 따라 달라질 수 있습니다</figcaption>
    </figure>
  </div>
  {'<div class="wrap">' + f'<p class="beta-note"><span class="beta-tag">원칙</span>확인한 것만 적고, 모르는 것은 ‘미확인’이라고 씁니다. 표본이 없는 화면은 부풀리지 않으며, 비교함·리뷰 초안·그룹 기록은 각자의 브라우저에 저장됩니다.</p>' + '</div>'}
</section>
{fact_sec}
<section class="sec loop-sec">
  <div class="wrap">
    {sec_head("EVIDENCE-TO-ACTION LOOP", "검증이 실행이 되고, 실행이 다시 검증이 됩니다")}
    <ol class="loop">{loop}</ol>
    <p class="loop-back">↺ 결과 데이터가 다음 사람의 선택과 그룹 설계를 개선합니다</p>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    {sec_head("WHY", "우리가 풀려는 4가지 비용", "사용자가 사는 것은 영상 파일이 아니라, ‘이 방식으로 실제 결과를 만들 수 있을 가능성’입니다.")}
    <div class="grid4">{problems}</div>
  </div>
</section>

<section class="sec fact-sec">
  <div class="wrap split">
    <figure class="split-img"><img src="/assets/img/fact-verification.jpg" alt="증빙 자료를 확인하는 검증 일러스트" loading="lazy" width="1280" height="720"></figure>
    <div class="split-copy">
      <span class="eyebrow t-cobalt">FACT — 확인 가능한 근거</span>
      <h2>‘검증됨’ 배지 하나가 아니라,<br>어떤 증빙을 어디까지 확인했는지</h2>
      <p>단일 진짜/가짜 판정을 하지 않습니다. 구매·수료·실행·거래·순수익 증빙을 단계로 표시하고,
      확인일·표본 수·미확인 비용을 함께 보여줍니다.</p>
      {evidence_meter(5)}
      <p class="fine">E5는 “이 강의를 들으면 돈을 번다”는 인증이 아닙니다. 특정 사용자가 특정 기간에 제출한
      자료에서 확인 가능한 매출과 주요 비용 범위를 표시할 뿐입니다.</p>
      <a class="link-more t-cobalt" href="/standards/">E0–E5 기준 전체 보기 →</a>
    </div>
  </div>
</section>

<section class="sec do-sec">
  <div class="wrap split rev">
    <div class="split-copy">
      <span class="eyebrow t-coral">DO — 함께 실행하는 4주</span>
      <h2>친목방이 아니라,<br>목표·행동·피드백·성과가 남는 작은 프로젝트</h2>
      <p>기본 단위는 4주입니다. 작은 결과를 빠르게 만드는 데 집중하고,
      결과 없음과 중단 이유도 같은 가치의 데이터로 남깁니다.</p>
      <table class="mini-table"><tbody>{rhythm}</tbody></table>
      <a class="link-more t-coral" href="/groups/">실행그룹 보러 가기 →</a>
    </div>
    <figure class="split-img"><img src="/assets/img/do-community.jpg" alt="함께 실행하는 그룹 일러스트" loading="lazy" width="1280" height="720"></figure>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    {sec_head("HOW", "당신의 상황에 맞는 세 가지 여정")}
    <div class="grid3">{journeys}</div>
  </div>
</section>

<section class="sec cat-sec">
  <div class="wrap">
    {sec_head("FOCUS", "먼저 깊게 파는 3개 카테고리", "넓게 얕게가 아니라, 한 카테고리 안의 데이터 밀도를 먼저 만듭니다.")}
    <div class="grid3">{cats}</div>
    <p class="fine center">재테크·투자 교육은 투자성과 오인과 규제 리스크를 고려해 초기 범위에서 제외하고, 별도 기준 확정 후 검토합니다.</p>
  </div>
</section>

<section class="cta-band">
  <div class="wrap cta-in">
    <div>
      <h2>먼저 확인하고, 함께 실행할 준비가 되셨나요?</h2>
      <p>파운딩 리뷰어 모집과 1기 실행그룹 안내를 순서대로 보내드립니다.</p>
    </div>
    <a class="btn btn-coral btn-lg" href="/waitlist/">사전등록 하기</a>
  </div>
</section>
"""
    ld = json.dumps({"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "name": f"{CONFIG['NAME_KO']} {CONFIG['NAME_EN']}", "url": CONFIG["BASE_URL"],
         "logo": CONFIG["BASE_URL"].rstrip("/") + "/assets/img/mark-512.png", "slogan": CONFIG["SLOGAN"]},
        {"@type": "WebSite", "name": CONFIG["NAME_KO"], "alternateName": CONFIG["NAME_EN"], "url": CONFIG["BASE_URL"], "inLanguage": "ko"},
    ]}, ensure_ascii=False)
    return page("/", f"{CONFIG['NAME_KO']} {CONFIG['NAME_EN']} — {CONFIG['SLOGAN']} 부업·수익화 교육 검증과 4주 실행그룹",
                "부업·수익화 강의의 수익 주장과 확인된 사실을 나눠 보여주고, 4주 실행그룹으로 함께 실행해 결과를 데이터로 남기는 독립 플랫폼.",
                body, active="", extra_head=f'<script type="application/ld+json">{ld}</script>')

# ─────────────────────────────────────────────────────────────
# 페이지: 탐색
# ─────────────────────────────────────────────────────────────
def build_explore(data):
    n = len(data["items"])
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow t-cobalt">FACT · 생태계 탐색</span>
    <h1>부업·수익화 생태계 탐색</h1>
    <p>교육 판매 플랫폼부터 실행·거래 채널까지, 의사결정에 걸리는 주변 서비스들을 한 기준으로 모읍니다.
    개별 강의의 주장과 확인된 사실은 <a class="t-cobalt" href="/fact/">검증 대상</a>에서 볼 수 있습니다.</p>
    <p class="beta-note"><span class="beta-tag">기준</span>현재 {n}개 항목 · 확인일은 항목마다 표시합니다. 리뷰 표본이 없는 것은 없다고 적습니다.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="ex-bar">
      <input id="ex-search" type="search" placeholder="이름·설명 검색" aria-label="서비스 검색">
      <button id="saved-toggle" class="btn btn-ghost" type="button">비교함 <b id="saved-count">0</b></button>
    </div>
    <div class="chip-row" id="ex-layers" role="group" aria-label="유형 필터"></div>
    <div class="chip-row" id="ex-cats" role="group" aria-label="카테고리 필터"></div>
    <p class="ex-meta"><b id="ex-count">{n}</b>개 항목</p>
    <div id="saved-panel" class="saved-panel" hidden>
      <b>비교함</b> <span class="dim">— 이 브라우저에만 저장됩니다</span>
      <ul id="saved-list"></ul>
    </div>
    <div id="ex-list" class="ex-list" aria-live="polite"></div>
    <div id="ex-empty" class="empty" hidden>
      <b>조건에 맞는 항목이 없습니다</b>
      <p>유사 주제로 검색어를 바꾸거나, 알고 계신 과정·서비스를 제보해 주세요.</p>
      <a class="btn btn-ghost" href="/report/">과정·서비스 제보하기</a>
    </div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap">
    {sec_head("NEXT", "개별 과정 데이터는 이렇게 채워집니다")}
    <div class="grid3">
      <div class="card"><b class="mono">01</b><p>파운딩 리뷰어가 실제 구매·수강한 과정을 구조화 리뷰로 남깁니다.</p></div>
      <div class="card"><b class="mono">02</b><p>운영자가 증빙 범위를 확인해 E1–E5 레벨과 확인일을 표시합니다.</p></div>
      <div class="card"><b class="mono">03</b><p>과정은 ‘버전’ 단위로 관리되어 오래된 리뷰와 최신 리뷰가 섞이지 않습니다.</p></div>
    </div>
  </div>
</section>
"""
    return page("/explore/", "탐색 — 부업·수익화 생태계",
                "부업·수익화 교육과 실행 채널을 한 기준으로 탐색합니다. 과정·리뷰 표본은 확인일과 함께 표시합니다.",
                body, active="/explore/")

# ─────────────────────────────────────────────────────────────
# 페이지: 팩트리뷰 목록 / 작성
# ─────────────────────────────────────────────────────────────
def build_reviews():
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow t-cobalt">FACT · 팩트리뷰</span>
    <h1>별점이 아니라, 조건·투입·결과를 남기는 리뷰</h1>
    <p>누가, 어떤 조건에서, 시간과 비용을 얼마나 들여, 무엇을 했고, 어떤 결과가 나왔는지를 씁니다.
    성과 없음과 중단도 다음 사람을 위한 같은 가치의 데이터입니다.</p>
    <div class="hero-cta">
      <a class="btn btn-cobalt" href="/reviews/new/">팩트리뷰 작성하기</a>
      <a class="btn btn-ghost" href="/standards/">작성·평가 기준 보기</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {sec_head("PUBLIC", "공개 리뷰")}
    <div class="empty">
      <b>아직 표본이 없습니다</b>
      <p>구매·수강 경험을 첫 기준으로 남겨주세요. 첫 리뷰들은 파운딩 리뷰어 프로그램으로 모집하며,
      표본 5개 미만인 과정은 종합점수 대신 ‘초기 표본’으로만 표시합니다.</p>
      <a class="btn btn-ghost" href="/waitlist/">파운딩 리뷰어 신청</a>
    </div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap">
    {sec_head("MINE", "내가 쓴 리뷰", "이 브라우저에만 저장됩니다. JSON으로 내보내 백업할 수 있습니다.")}
    <div id="rv-local-list" class="rv-list"></div>
    <div id="rv-local-empty" class="empty">
      <b>이 브라우저에 저장된 리뷰가 없습니다</b>
      <p>작성한 리뷰 초안과 제출본이 여기에 표시됩니다.</p>
    </div>
  </div>
</section>
"""
    return page("/reviews/", "팩트리뷰",
                "구매·수료·실행·거래 증빙과 함께 남기는 구조화 리뷰. 성과 없음과 중단 경험도 데이터로 남깁니다.",
                body, active="/reviews/")

def build_review_new():
    def rate_row(key, name, weight, q):
        radios = "".join(
            f'<label class="rate-dot"><input type="radio" name="rate-{key}" value="{v}"><span>{v}</span></label>'
            for v in range(1, 6)
        )
        return f"""<div class="rate-row">
  <div class="rate-info"><b>{E(name)}</b> <span class="mono dim">{weight}%</span><p>{E(q)}</p></div>
  <div class="rate-dots" role="radiogroup" aria-label="{E(name)} 점수">{radios}</div>
</div>"""
    rate_keys = ["exec", "quality", "reality", "care", "refs", "value", "outcome"]
    rates = "".join(rate_row(k, n, w, q) for k, (n, w, q) in zip(rate_keys, C.RATING_DIMENSIONS))

    ev_boxes = "".join(
        f'<label class="check"><input type="checkbox" name="ev" value="E{i}"> <b class="mono">E{i}</b> {E(t)} <span class="dim">— {E(w)}</span></label>'
        for i, (code, t, w, _) in enumerate(C.EVIDENCE_LEVELS) if i >= 1
    )
    rel_items = ["무료 수강", "수강료 환급", "협찬·대가", "고용·업무 관계", "지인·가족", "지분·투자 관계", "추천 코드 사용"]
    rel_boxes = "".join(f'<label class="check"><input type="checkbox" name="rel" value="{E(r)}"> {E(r)}</label>' for r in rel_items)

    body = f"""
<section class="page-head slim">
  <div class="wrap">
    <span class="eyebrow t-cobalt">FACT · 리뷰 작성</span>
    <h1>팩트리뷰 작성</h1>
    <p>모든 항목은 자동으로 임시저장됩니다(이 브라우저). 확실하지 않은 항목은 비워 두세요 — 모르는 것을 아는 것처럼 쓰지 않는 것이 원칙입니다.</p>
    <p id="rv-draft-info" class="fine"></p>
  </div>
</section>
<section class="sec">
  <div class="wrap narrow">
    <form id="review-form" autocomplete="off">

      <fieldset class="form-sec">
        <legend>1 · 과정 식별</legend>
        <div class="f2">
          <label>과정명 <span class="req">필수</span><input name="course" required placeholder="예: ○○ 스마트스토어 실전반"></label>
          <label>플랫폼·채널<input name="platform" placeholder="예: 클래스101 / 자체 사이트"></label>
        </div>
        <div class="f2">
          <label>강사·제공자<input name="instructor" placeholder="예: ○○○"></label>
          <label>수강 버전(연·월)<input name="version" placeholder="예: 2026년 5월 버전"></label>
        </div>
        <div class="f2">
          <label>구매 시기<input name="bought" placeholder="예: 2026-05"></label>
          <label>결제 금액대<select name="price">
            <option value="">선택</option><option>10만 원 미만</option><option>10–30만 원</option>
            <option>30–50만 원</option><option>50–100만 원</option><option>100만 원 이상</option><option>무료</option>
          </select></label>
        </div>
      </fieldset>

      <fieldset class="form-sec">
        <legend>2 · 나의 시작 조건</legend>
        <div class="f2">
          <label>직업·상황<input name="job" placeholder="예: 직장인 / 자영업 / 프리랜서"></label>
          <label>관련 선행 경험<select name="prior">
            <option value="">선택</option><option>전혀 없음</option><option>취미 수준</option><option>부업 경험 있음</option><option>관련 업무 경험</option>
          </select></label>
        </div>
        <div class="f2">
          <label>주당 가용 시간<select name="hours">
            <option value="">선택</option><option>3시간 미만</option><option>3–6시간</option><option>6–10시간</option><option>10시간 이상</option>
          </select></label>
          <label>초기 자본(강의료 외)<select name="capital">
            <option value="">선택</option><option>거의 없음</option><option>10만 원 미만</option><option>10–50만 원</option><option>50만 원 이상</option>
          </select></label>
        </div>
        <label>수강 목표<input name="goal" placeholder="예: 3개월 안에 첫 판매 1건"></label>
      </fieldset>

      <fieldset class="form-sec">
        <legend>3 · 학습과 실행</legend>
        <div class="f2">
          <label>진도<select name="progress">
            <option value="">선택</option><option>초반 일부</option><option>절반 정도</option><option>대부분</option><option>완주·수료</option>
          </select></label>
          <label>실행 기간<input name="period" placeholder="예: 8주"></label>
        </div>
        <div class="f2">
          <label>실제 주당 투입 시간<input name="realhours" placeholder="예: 주 6시간"></label>
          <label>추가 비용(도구·광고·재고 등)<input name="extracost" placeholder="예: 도구비 24만 원, 광고비 일부"></label>
        </div>
        <label>과제·피드백·커뮤니티 경험<textarea name="support" rows="3" placeholder="질문 응답 속도, 첨삭 여부, 커뮤니티 분위기 등"></textarea></label>
      </fieldset>

      <fieldset class="form-sec">
        <legend>4 · 7가지 평가 <span class="dim">(해당 없으면 비워두기)</span></legend>
        {rates}
      </fieldset>

      <fieldset class="form-sec">
        <legend>5 · 결과</legend>
        <label>결과 유형<select name="outcome_type">
          <option value="">선택</option><option>학습(이해·기술 습득)</option><option>행동(산출물·시도)</option>
          <option>거래(첫 판매·계약)</option><option>재무(매출·순수익 변화)</option><option>중단·무성과</option>
        </select></label>
        <div class="f2">
          <label>매출 구간(선택)<select name="rev">
            <option value="">비공개/해당 없음</option><option>10만 원 미만</option><option>10–50만 원</option>
            <option>50–100만 원</option><option>100–300만 원</option><option>300만 원 이상</option>
          </select></label>
          <label>기간<input name="rev_period" placeholder="예: 2026년 5–6월"></label>
        </div>
        <label>결과 서술 <span class="req">필수</span><textarea name="result" rows="4" required placeholder="무엇을 만들었고/팔았고/멈췄는지, 다음 사람이 알아야 할 점"></textarea></label>
        <p class="fine">중단·무성과도 정상적인 결과입니다. 어디서 막혔는지가 다음 사람에게 가장 유용한 정보입니다.</p>
      </fieldset>

      <fieldset class="form-sec">
        <legend>6 · 증빙 범위 <span class="dim">(제출 ‘가능’한 범위 선택)</span></legend>
        <p class="fine">원본 자료를 이 사이트에 올리지 마세요. 증빙 확인은 제출 후 비공개 절차로 따로 안내되며,
        원본은 공개되지 않고 확인 범위만 표시됩니다.</p>
        {ev_boxes}
      </fieldset>

      <fieldset class="form-sec">
        <legend>7 · 관계 공개 <span class="req">필수</span></legend>
        <p class="fine">해당하는 것을 모두 선택하세요. 숨겨진 대가 관계가 확인되면 리뷰는 비공개 처리됩니다.</p>
        {rel_boxes}
        <label class="check"><input type="checkbox" id="rel-none" name="rel_none" value="1"> 위 관계 중 해당 사항 없음</label>
        <label class="check"><input type="checkbox" id="agree-update" name="agree_update" value="1"> 30·90일 후 결과 업데이트 요청에 동의합니다</label>
      </fieldset>

      <div class="card preview-card">
        <b>공개 요약 미리보기</b>
        <p id="rv-preview" class="mono">작성 내용을 바탕으로 자동 생성됩니다.</p>
      </div>

      <div class="form-actions">
        <button type="button" id="rv-export" class="btn btn-ghost">JSON 백업</button>
        <button type="button" id="rv-clear" class="btn btn-ghost">초안 지우기</button>
        <button type="submit" id="rv-submit" class="btn btn-cobalt">리뷰 저장(제출 준비)</button>
      </div>
      <p class="fine">저장하면 이 브라우저의 ‘내가 쓴 리뷰’에 보관됩니다. 공개 게시는 증빙 확인을 거친 뒤 진행하며,
      제출 방법은 파운딩 리뷰어에게 먼저 안내합니다.</p>
    </form>
  </div>
</section>
"""
    return page("/reviews/new/", "팩트리뷰 작성",
                "조건·투입·평가·결과·증빙 범위·관계 공개까지, 다음 사람에게 유용한 구조로 리뷰를 작성합니다.",
                body, active="/reviews/")

# ─────────────────────────────────────────────────────────────
# 페이지: 실행그룹
# ─────────────────────────────────────────────────────────────
def build_groups():
    types = "".join(
        f'<div class="card gtype"><b>{t}</b><p>{d}</p><small class="mono dim">{g}</small></div>'
        for t, d, g in [
            ("과정 실행반", "같은 강의를 듣는 사람들이 주차별 과제와 산출물을 함께 만듭니다.", "수료 후 첫 실행까지"),
            ("주제 검증 스프린트", "강의를 사기 전, 관심 분야를 4주 작은 실험으로 확인합니다.", "첫 콘텐츠 · 프로토타입"),
            ("프로젝트 빌드", "역할이 다른 멤버가 모여 하나의 결과물을 공개합니다.", "MVP · 전자책 · 채널"),
            ("수익화 운영반", "이미 시작한 부업의 반복 개선에 집중합니다.", "고객 접촉 · 첫 거래 · 재구매"),
            ("지역·오프라인 모임", "같은 지역에서 직접 만나 서로의 진행 상황을 점검합니다.", "대면 체크인 · 현장 피드백"),
        ]
    )
    body = f"""
<section class="page-head coral">
  <div class="wrap">
    <span class="eyebrow t-coral">DO · 실행그룹</span>
    <h1>4주 동안, 작게라도 결과를 만듭니다</h1>
    <p>월요일 목표 → 수요일 체크인 → 금요일 산출물·피드백 → 주말 회고.
    수익 금액 경쟁이 아니라 행동·산출물·학습을 우선합니다.</p>
    <div class="hero-cta">
      <a class="btn btn-coral" href="/groups/new/">실행그룹 개설하기</a>
      <a class="btn btn-ghost" href="/policies/community/">그룹 규칙 보기</a>
    </div>
    <p class="beta-note"><span class="beta-tag">안내</span>그룹 보드는 개설자 브라우저에 저장되며, ‘읽기 전용 스냅샷 링크’로 멤버와 공유합니다. 실시간 동기화와 계정 기능은 다음 단계에서 제공됩니다.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {sec_head("TYPES", "그룹의 다섯 가지 쓰임", "", "t-coral")}
    <div class="grid5">{types}</div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap">
    {sec_head("OPEN", "모집 중인 그룹", "", "t-coral")}
    <div id="gr-list" class="gr-list"></div>
    <div id="gr-empty" class="empty">
      <b>이 브라우저에 만든 그룹이 없습니다</b>
      <p>4주 동안 만들고 싶은 결과를 제안하면 함께할 사람을 찾습니다.
      공식 1기 그룹 모집 소식은 사전등록으로 알려드립니다.</p>
      <div class="hero-cta center">
        <a class="btn btn-coral" href="/groups/new/">첫 그룹 제안하기</a>
        <a class="btn btn-ghost" href="/waitlist/">1기 모집 알림 받기</a>
      </div>
    </div>
    <details class="import-box">
      <summary>스냅샷 링크로 받은 그룹 열기</summary>
      <p class="fine">그룹장이 보낸 링크를 브라우저 주소창에 그대로 붙여넣으면 열립니다. 링크 전체를 여기 붙여넣어도 됩니다.</p>
      <div class="f-inline"><input id="gr-import" placeholder="https://…/groups/room/#s=…"><button id="gr-import-btn" class="btn btn-ghost" type="button">열기</button></div>
    </details>
  </div>
</section>
"""
    return page("/groups/", "실행그룹 — 4주 스프린트",
                "목표·주간 체크인·동료 피드백·데모데이. 4주 실행그룹으로 작은 결과를 빠르게 만듭니다.",
                body, active="/groups/")

def build_group_new():
    body = f"""
<section class="page-head coral slim">
  <div class="wrap">
    <span class="eyebrow t-coral">DO · 그룹 개설</span>
    <h1>실행그룹 개설</h1>
    <p>그룹명은 결과가 보이게 짓습니다. 예: <b>“4주, AI 자동화 1개 배포”</b></p>
  </div>
</section>
<section class="sec">
  <div class="wrap narrow">
    <form id="group-form" autocomplete="off">
      <fieldset class="form-sec">
        <legend>기본 정보</legend>
        <label>그룹명 <span class="req">필수</span><input name="name" required placeholder="예: 4주, 스마트스토어 첫 주문 1건"></label>
        <div class="f2">
          <label>그룹 유형<select name="gtype">
            <option>주제 검증 스프린트</option><option>과정 실행반</option><option>프로젝트 빌드</option><option>수익화 운영반</option><option>지역·오프라인 모임</option>
          </select></label>
          <label>연결 주제·과정<input name="topic" placeholder="예: 스마트스토어 / ○○ 강의 2026-05 버전"></label>
        </div>
        <div class="f2">
          <label>기간<select name="weeks"><option value="4">4주(기본)</option><option value="2">2주</option><option value="6">6주</option></select></label>
          <label>정원<select name="size"><option>5명</option><option selected>6–8명</option><option>9–10명</option></select></label>
        </div>
      </fieldset>
      <fieldset class="form-sec">
        <legend>목표와 투명성</legend>
        <label>공동 목표(측정 가능한 산출물·기한) <span class="req">필수</span><textarea name="goal" rows="2" required placeholder="예: 4주 안에 각자 상품 1개 등록 + 첫 주문 시도"></textarea></label>
        <label>개인 목표 가이드<input name="personal" placeholder="예: 현재 수준·가용 시간에 맞춘 최소 목표 1개"></label>
        <label>비용·필수 도구·경제 관계 공개<textarea name="cost" rows="2" placeholder="예: 도구비 월 1만 원, 리더와 멤버 간 금전 거래 없음"></textarea></label>
      </fieldset>
      <fieldset class="form-sec">
        <legend>규칙 동의 <span class="req">필수</span></legend>
        <label class="check"><input type="checkbox" name="rule1" required> 강매·다단계·리딩방·불법 투자권유·무단 광고를 하지 않습니다</label>
        <label class="check"><input type="checkbox" name="rule2" required> 수익 금액은 구간으로 쓰고, 멤버의 비공개 선택을 존중합니다</label>
        <label class="check"><input type="checkbox" name="rule3" required> 완료 기준: 4회 중 3회 체크인 + 산출물 1개 + 결과로그</label>
      </fieldset>
      <div class="form-actions">
        <button type="submit" class="btn btn-coral">그룹 만들기 → 그룹 보드 열기</button>
      </div>
      <p class="fine">만든 그룹은 이 브라우저에 저장됩니다. 그룹 보드에서 스냅샷 링크를 만들어 멤버에게 공유하세요.</p>
    </form>
  </div>
</section>
"""
    return page("/groups/new/", "실행그룹 개설",
                "결과가 보이는 그룹명, 측정 가능한 공동 목표, 투명한 비용 공개로 4주 실행그룹을 개설합니다.",
                body, active="/groups/")

def build_group_room():
    body = f"""
<section class="page-head coral slim">
  <div class="wrap">
    <span class="eyebrow t-coral">DO · 그룹 보드</span>
    <h1 id="gm-title">그룹 보드</h1>
    <p id="gm-meta" class="mono dim"></p>
    <p id="gm-snapshot-note" class="beta-note" hidden><span class="beta-tag">읽기 전용</span>스냅샷으로 보는 중입니다. ‘내 브라우저에 가져오기’를 누르면 이어서 기록할 수 있습니다.</p>
    <div id="gm-progress" class="gm-progress" aria-label="진행률"></div>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="gm-grid">
      <aside class="gm-side">
        <div class="card">
          <b>멤버</b>
          <ul id="gm-members" class="gm-members"></ul>
          <div class="f-inline"><input id="gm-member-add" placeholder="닉네임"><button id="gm-member-btn" class="btn btn-ghost" type="button">추가</button></div>
        </div>
        <div class="card">
          <b>공유·백업</b>
          <p class="fine">스냅샷 링크는 ‘지금까지의 기록’을 담은 읽기 전용 링크입니다.</p>
          <button id="gm-share" class="btn btn-coral wfull" type="button">스냅샷 링크 복사</button>
          <button id="gm-export" class="btn btn-ghost wfull" type="button">JSON 백업</button>
          <button id="gm-adopt" class="btn btn-ghost wfull" type="button" hidden>내 브라우저에 가져오기</button>
          <button id="gm-danger" class="btn btn-danger wfull" type="button">이 그룹 삭제</button>
        </div>
      </aside>
      <div class="gm-main">
        <div id="gm-week-tabs" class="week-tabs" role="tablist"></div>
        <div class="card rhythm-hint mono">월 목표 · 수 체크인 · 금 산출물/피드백 · 주말 회고</div>
        <div id="gm-board" class="gm-board" aria-live="polite"></div>
        <form id="gm-entry-form" class="card entry-form">
          <b>기록 남기기</b>
          <div class="f-inline3">
            <select id="gm-etype" aria-label="기록 유형">
              <option value="목표">월 · 이번 주 목표</option>
              <option value="체크인">수 · 중간 체크인</option>
              <option value="산출물">금 · 산출물 공개</option>
              <option value="피드백">금 · 동료 피드백</option>
              <option value="회고">주말 · 회고</option>
            </select>
            <select id="gm-eauthor" aria-label="작성 멤버"></select>
          </div>
          <textarea id="gm-etext" rows="3" placeholder="한 가지 핵심만 짧게. 막힌 점과 도움 요청도 좋은 기록입니다." aria-label="기록 내용"></textarea>
          <button id="gm-ebtn" class="btn btn-coral" type="submit">기록 추가</button>
        </form>
        <div class="card outcome-card">
          <b>4주차 · 결과로그</b>
          <p class="fine">결과로그를 남기면 이번 스프린트가 완료됩니다. 결과 없음도 정상적인 결과입니다 — 어디서 막혔는지 남겨주세요.</p>
          <ul id="gm-olist" class="gm-olist"></ul>
          <form id="gm-outcome" class="f-col">
            <div class="f-inline3">
              <select id="gm-otype" aria-label="결과 유형">
                <option>학습</option><option>행동·산출물</option><option>거래</option><option>재무(구간)</option><option>중단·무성과</option>
              </select>
              <select id="gm-oauthor" aria-label="결과 작성 멤버"></select>
            </div>
            <textarea id="gm-otext" rows="2" placeholder="예: 상품 1개 등록, 방문 32 · 주문 0 — 다음엔 상세페이지 개선"></textarea>
            <button id="gm-obtn" class="btn btn-cobalt" type="submit">결과로그 저장</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</section>
"""
    return page("/groups/room/", "그룹 보드",
                "4주 실행그룹의 목표·체크인·산출물·피드백·결과로그를 기록하는 보드.",
                body, active="/groups/")

# ─────────────────────────────────────────────────────────────
# 페이지: 결과 / 검증 기준 / 소개 / 사전등록
# ─────────────────────────────────────────────────────────────
def build_results():
    otypes = "".join(
        f'<div class="card"><b>{t}</b><p>{d}</p></div>'
        for t, d in [
            ("학습", "이해·기술 습득. 시작 조건과 함께 기록됩니다."),
            ("행동·산출물", "첫 콘텐츠, 상품 등록, 자동화 배포 같은 눈에 보이는 결과."),
            ("거래", "첫 판매·계약·정산. 금액은 구간으로 표시합니다."),
            ("재무", "매출과 주요 비용을 분리한 세전 순수익 ‘구간’."),
            ("중단·무성과", "멈춘 지점과 이유. 다음 사람의 시간을 아끼는 데이터."),
        ]
    )
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">OUTCOME · 결과 데이터</span>
    <h1>조건이 비슷한 사람의 결과를 찾도록</h1>
    <p>결과는 평균 한 줄이 아니라 표본 수, 사용자 조건, 기간, 매출·비용 분리와 함께 공개될 예정입니다.</p>
    {beta_note("아직 공개할 결과 표본이 없습니다. 첫 실행그룹과 파운딩 리뷰의 결과로그가 모이면, 이 페이지에 분포로 표시됩니다 — 성공 사례만 골라 싣지 않습니다.")}
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {sec_head("TYPES", "기록되는 다섯 가지 결과")}
    <div class="grid5">{otypes}</div>
    <p class="fine center">‘결과 없음도 정상적인 결과입니다. 어디서 막혔는지 남겨주세요.’ — 팩트앤두 결과 기록 원칙</p>
  </div>
</section>
"""
    return page("/results/", "결과 데이터",
                "성공 사례 나열이 아니라 표본·조건·기간·비용 분리와 함께 보는 결과 데이터.",
                body, active="/results/")

def build_standards():
    ev_rows = "".join(
        f'<tr><td class="mono ev-code">{c}</td><td><b>{E(t)}</b></td><td>{E(w)}</td><td>{E(s)}</td></tr>'
        for c, t, w, s in C.EVIDENCE_LEVELS
    )
    dim_rows = "".join(
        f'''<div class="dim-row"><div class="dim-name"><b>{E(n)}</b><span class="mono">{w}%</span></div>
<div class="dim-bar"><i style="width:{w*4}%"></i></div><p>{E(q)}</p></div>'''
        for n, w, q in C.RATING_DIMENSIONS
    )
    lang_rows = "".join(
        f'<tr><td class="ok">{E(a)}</td><td class="no">{E(b)}</td></tr>' for a, b in C.LANGUAGE_RULES
    )
    score_rules = "".join(f"<li>{E(s)}</li>" for s in C.SCORE_RULES)
    nosell = "".join(f"<li>{E(s)}</li>" for s in C.NO_SELL_RULES)
    disputes = "".join(
        f'<li><b>{E(t)}</b><p>{E(d)}</p></li>' for t, d in C.DISPUTE_STEPS
    )
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow t-cobalt">TRUST · 검증 기준</span>
    <h1>무엇을, 언제, 어디까지 확인했는지</h1>
    <p>검증은 ‘절대적 사실 선언’이 아니라 증빙의 범위와 리뷰어의 맥락을 읽기 쉽게 표시하는 과정입니다.
    기준은 전부 공개하며, 여기서 벗어난 표시를 발견하면 알려주세요.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {sec_head("E0–E5", "증빙 레벨", "레벨이 높다고 좋은 강의라는 뜻이 아닙니다. ‘무엇이 확인되었는지’의 범위입니다.")}
    {evidence_meter(5)}
    <div class="table-wrap"><table class="std-table">
      <thead><tr><th>레벨</th><th>표시명</th><th>확인 대상</th><th>공개 방식</th></tr></thead>
      <tbody>{ev_rows}</tbody>
    </table></div>
    <p class="fine">중요 — E5는 “이 강의를 들으면 돈을 번다”는 인증이 아닙니다. 특정 사용자가 특정 기간에 제출한 자료에서
    확인 가능한 매출과 주요 비용 범위를 표시할 뿐이며, 미확인 비용은 미확인이라고 씁니다.</p>
  </div>
</section>
<section class="sec alt">
  <div class="wrap">
    {sec_head("RATING", "리뷰 평가 7차원과 가중치")}
    <div class="dims">{dim_rows}</div>
    <h3 class="sub-h">점수 노출 규칙</h3>
    <ol class="rule-list">{score_rules}</ol>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {sec_head("LANGUAGE", "브랜드 언어 원칙", "표현이 과장을 만듭니다. 우리는 이렇게 씁니다.")}
    <div class="table-wrap"><table class="std-table lang-table">
      <thead><tr><th>사용하는 표현</th><th>피하는 표현</th></tr></thead>
      <tbody>{lang_rows}</tbody>
    </table></div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap split">
    <div class="split-copy">
      {sec_head("FAIR", "정정·공식답변·이의제기")}
      <ol class="dispute-steps">{disputes}</ol>
    </div>
    <div class="split-copy">
      {sec_head("NO-SELL", "수익화 금지선", "무료 정보의 신뢰를 해치는 수익은 만들지 않습니다.")}
      <ul class="rule-list nosell">{nosell}</ul>
    </div>
  </div>
</section>
"""
    return page("/standards/", "검증 기준 — E0–E5 증빙 레벨과 평가 방법",
                "E0–E5 증빙 레벨, 리뷰 평가 7차원, 점수 노출 규칙, 언어 원칙, 이의제기 절차, 수익화 금지선을 공개합니다.",
                body, active="/standards/")

def build_about():
    principles = "".join(
        f"<li>{E(s)}</li>" for s in [
            "검증은 수익 보장이 아니라 증빙 범위·시점·맥락의 표시입니다.",
            "별점보다 사용자 조건, 투입 시간, 추가 비용, 실행 과정, 결과를 먼저 보여줍니다.",
            "강사 자료 제공은 선택 채널이며, 수강자·실행자 데이터가 핵심 공급원입니다.",
            "성과 없음, 중단, 환불, 기대 불일치도 삭제하지 않고 구조화합니다.",
            "과정은 ‘버전’ 단위로 리뷰와 결과를 연결합니다.",
            "광고·제휴·무료수강·고용·지인·창업자 관계는 항상 공개합니다.",
            "평가점수와 검색 순위는 판매하지 않으며, 유료 기능은 명확히 분리합니다.",
        ]
    )
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">ABOUT</span>
    <h1>{E(CONFIG['NAME_KO'])}를 소개합니다</h1>
    <p>{E(CONFIG['TAGLINE'])}</p>
  </div>
</section>
<section class="sec">
  <div class="wrap split">
    <figure class="split-img brand-fig"><img src="/assets/img/logo-full.png" alt="FACT&amp;DO 로고 — 체크 표시와 실행 화살표" loading="lazy" width="1000" height="740"></figure>
    <div class="split-copy">
      <h2>FACT는 근거, DO는 태도</h2>
      <p><b class="t-cobalt">FACT</b>는 냉소적인 폭로가 아니라 <b>확인 가능한 근거</b>를 뜻합니다.
      <b class="t-coral">DO</b>는 혼자 미루지 않고 <b>함께 실행해 결과를 남기는 태도</b>를 뜻합니다.</p>
      <div class="philo">
        <p><b>FACT WITHOUT DO</b> — 정보만 쌓이면 계속 비교만 하고 움직이지 않습니다.</p>
        <p><b>DO WITHOUT FACT</b> — 검증 없이 실행하면 시간과 비용을 낭비하고 과장된 성공담을 재생산합니다.</p>
        <p><b>FACT &amp; DO</b> — 확인 가능한 정보로 선택하고, 실행과 결과로 다시 사실을 만듭니다.</p>
      </div>
    </div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap">
    {sec_head("PRINCIPLES", "7가지 운영 원칙")}
    <ol class="rule-list big">{principles}</ol>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {sec_head("NOT-DOING", "지금 하지 않는 것", "신뢰가 먼저입니다. 아래는 검증이 끝나기 전까지 하지 않습니다.")}
    <div class="grid3">
      <div class="card"><b>강의 결제·중개</b><p>팩트앤두에서 강의를 팔거나 결제를 대행하지 않습니다.</p></div>
      <div class="card"><b>자체 강의 판매</b><p>평가의 독립성이 자리 잡기 전에는 자체 교육 상품을 팔지 않습니다.</p></div>
      <div class="card"><b>AI 자동 진위 판정</b><p>AI는 보조 도구입니다. 증빙 판정과 제재의 최종 결정은 사람이 합니다.</p></div>
    </div>
  </div>
</section>
<section class="cta-band">
  <div class="wrap cta-in">
    <div><h2>기준에 동의하신다면, 함께 시작해요</h2><p>파운딩 리뷰어와 1기 실행그룹을 모집합니다.</p></div>
    <a class="btn btn-coral btn-lg" href="/waitlist/">사전등록 하기</a>
  </div>
</section>
"""
    return page("/about/", "소개 — FACT는 근거, DO는 태도",
                "팩트앤두의 브랜드 철학, 7가지 운영 원칙, 그리고 신뢰를 위해 지금 하지 않는 것들.",
                body, active="")

def build_waitlist():
    form_url = CONFIG["WAITLIST_FORM_URL"]
    if form_url:
        action = f'<a id="wl-btn" class="btn btn-coral btn-lg" href="{E(form_url)}" target="_blank" rel="noopener">사전등록 폼 열기</a>'
        note = '<p class="fine">외부 폼(무료 서비스)으로 연결됩니다. 수집 항목과 보관 기간은 폼 첫 화면에 표시됩니다.</p>'
    else:
        action = '<span class="btn btn-lg btn-disabled" aria-disabled="true">사전등록 폼 준비 중</span>'
        email = CONFIG["CONTACT_EMAIL"]
        alt = (f'그 전에는 <a href="mailto:{E(email)}?subject=팩트앤두 사전등록">{E(email)}</a> 로 “사전등록” 메일을 보내주세요.'
               if email else "폼이 연결되면 이 버튼이 활성화됩니다.")
        note = f'<p class="fine">{alt}</p>'
    chat = ""
    if CONFIG["OPENCHAT_URL"]:
        chat = f'<a class="btn btn-ghost btn-lg" href="{E(CONFIG["OPENCHAT_URL"])}" target="_blank" rel="noopener">1기 오픈채팅 참여</a>'
    body = f"""
<section class="page-head coral">
  <div class="wrap">
    <span class="eyebrow t-coral">JOIN · 사전등록</span>
    <h1>새 소식과 첫 기회를 먼저 받으세요</h1>
    <p>스팸 없이, 준비된 것만 순서대로 보냅니다.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="grid3">
      <div class="card"><b class="mono t-coral">01</b><b>새 소식</b><p>새로 등록된 검증 대상과 주요 기능 공개 소식을 먼저 받습니다.</p></div>
      <div class="card"><b class="mono t-coral">02</b><b>파운딩 리뷰어</b><p>실제 수강 경험을 첫 기준 리뷰로 남기는 초기 멤버로 초대합니다.</p></div>
      <div class="card"><b class="mono t-coral">03</b><b>1기 실행그룹</b><p>AI 자동화·콘텐츠·이커머스 주제의 첫 4주 스프린트에 우선 안내합니다.</p></div>
    </div>
    <div class="wl-action">{action}{chat}{note}</div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap narrow">
    {sec_head("PROMISE", "사전등록자에게 드리는 약속")}
    <ul class="rule-list">
      <li>이메일은 위 세 가지 안내 외의 목적으로 사용하지 않습니다.</li>
      <li>광고·제휴 메일을 보내지 않으며, 한 번의 클릭으로 수신을 중단할 수 있습니다.</li>
      <li>모집·통계 수치를 부풀려 표시하지 않습니다.</li>
    </ul>
  </div>
</section>
"""
    return page("/waitlist/", "사전등록 — 파운딩 리뷰어·1기 실행그룹",
                "팩트앤두 새 소식, 파운딩 리뷰어, 1기 실행그룹 안내를 순서대로 받아보세요.",
                body, active="")

# ─────────────────────────────────────────────────────────────
# 페이지: 정책 3종 / 404
# ─────────────────────────────────────────────────────────────
def build_policy(path, title, items, desc):
    secs = "".join(f'<section class="pol-sec"><h2>{E(t)}</h2><p>{E(b)}</p></section>' for t, b in items)
    body = f"""
<section class="page-head slim">
  <div class="wrap">
    <span class="eyebrow">POLICY</span>
    <h1>{E(title)}</h1>
    {beta_note(E(C.POLICY_NOTICE), "초안")}
  </div>
</section>
<section class="sec">
  <div class="wrap narrow pol-body">{secs}
    <p class="fine">문의와 정정 요청은 <a class="t-cobalt" href="/report/">제보·정정·이의제기</a> 안내에 따라 접수합니다.</p>
  </div>
</section>
"""
    return page(path, title, desc, body)

def build_404():
    body = f"""
<section class="page-head slim">
  <div class="wrap center">
    <span class="eyebrow">404</span>
    <h1>페이지를 찾을 수 없습니다</h1>
    <p>주소가 바뀌었거나 준비 중인 페이지입니다.</p>
    <div class="hero-cta center">
      <a class="btn btn-cobalt" href="/">홈으로</a>
      <a class="btn btn-ghost" href="/explore/">탐색으로</a>
    </div>
  </div>
</section>
"""
    # 404는 dist 루트의 404.html 로 저장 (Cloudflare Pages 규칙)
    doc_path = page("/404.html", "페이지를 찾을 수 없습니다", "요청한 페이지를 찾을 수 없습니다.", body)
    return doc_path

def build_admin(db):
    """관리자 화면(/admin/). 저장은 GitHub 저장소에 직접 커밋하는 방식이라 서버가 필요 없습니다."""
    out = os.path.join(DIST, "admin")
    os.makedirs(out, exist_ok=True)
    site = {k: CONFIG.get(k, "") for k in ("CONTACT_EMAIL", "WAITLIST_FORM_URL", "REPORT_FORM_URL", "OPENCHAT_URL",
                                             "NOTICE", "DATA_DATE", "GITHUB_REPO", "GITHUB_BRANCH")}
    with open(os.path.join(out, "db.json"), "w", encoding="utf-8") as f:
        json.dump({**db, "site": site}, f, ensure_ascii=False)
    for name in ("admin.css", "admin.js"):
        shutil.copy(os.path.join("assets", name), os.path.join(DIST, "assets", name))
    doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>관리자 · {E(CONFIG['NAME_KO'])} {E(CONFIG['NAME_EN'])}</title>
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/assets/admin.css?v={ver('admin.css')}">
</head>
<body>
<div id="app"><p class="boot">불러오는 중…</p></div>
<script>window.FD_ADMIN={{repo:{json.dumps(site['GITHUB_REPO'])},branch:{json.dumps(site['GITHUB_BRANCH'] or 'main')}}};</script>
<script src="/assets/admin.js?v={ver('admin.js')}"></script>
</body>
</html>"""
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)

# ─────────────────────────────────────────────────────────────
# 빌드 실행
# ─────────────────────────────────────────────────────────────
def main():
    # dist 초기화
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)

    # 데이터 로드 → dist/assets/data.js 로 인라인 (fetch 불필요, 로컬에서도 동작)
    with open("data/services.json", encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(os.path.join(DIST, "assets"), exist_ok=True)
    payload = {"items": data["items"], "date": CONFIG["DATA_DATE"]}
    with open(os.path.join(DIST, "assets", "data.js"), "w", encoding="utf-8") as f:
        f.write("window.FD_DATA=" + json.dumps(payload, ensure_ascii=False) + ";")

    # 정적 자산 복사
    for name in ("style.css", "app.js", "og.png"):
        shutil.copy(os.path.join("assets", name), os.path.join(DIST, "assets", name))
    shutil.copytree("assets/img", os.path.join(DIST, "assets", "img"))
    for icon in ("favicon-32.png", "favicon-64.png", "apple-touch-icon.png"):
        shutil.copy(os.path.join("assets", icon), os.path.join(DIST, icon))

    # 검증 대상·후기·공공기록 로드
    def load(name):
        with open(f"data/{name}.json", encoding="utf-8") as f:
            return json.load(f).get("items", [])
    targets, reviews, records, cases = load("targets"), load("reviews"), load("records"), load("cases")
    ctx = types.SimpleNamespace(page=page, CONFIG=CONFIG, sec_head=sec_head, beta_note=beta_note)
    pub_targets = F.public(targets)

    # 페이지 생성
    paths = [
        build_home(F.home_fact_section(ctx, targets, reviews, records)),
        F.build_fact_index(ctx, targets, reviews),
        build_explore(data),
        F.build_reviews_page(ctx, targets, reviews),
        build_review_new(),
        build_groups(),
        build_group_new(),
        build_group_room(),
        build_results(),
        build_standards(),
        F.build_records_page(ctx, records),
        F.build_report_page(ctx, C.DISPUTE_STEPS),
        build_about(),
        build_waitlist(),
        build_policy("/policies/terms/", "이용약관 (초안)", C.TERMS,
                     "팩트앤두 이용약관 초안 — 서비스 성격, 금지 행위, 관계 공개 의무, 책임의 한계."),
        build_policy("/policies/privacy/", "개인정보 처리방침 (초안)", C.PRIVACY,
                     "팩트앤두 개인정보 처리방침 초안 — 수집 항목과 증빙 자료 처리 원칙."),
        build_policy("/policies/community/", "커뮤니티 가이드", C.COMMUNITY,
                     "팩트앤두 커뮤니티 가이드 — 표현 원칙, 금지 행위, 실행그룹 규칙, 신고 절차."),
    ]
    lastmod = {"/": CONFIG["DATA_DATE"], "/fact/": CONFIG["DATA_DATE"], "/reviews/": CONFIG["DATA_DATE"]}
    for t in pub_targets:
        pth = F.build_fact_detail(ctx, t, targets, reviews)
        paths.append(pth)
        lastmod[pth] = t.get("checked", "")
    build_404()
    build_admin({"targets": targets, "reviews": reviews, "records": records, "cases": cases,
                 "services": data["items"]})

    # 네이버 소유확인 파일
    nv = CONFIG.get("NAVER_VERIFY_FILE", "")
    if nv:
        with open(os.path.join(DIST, nv), "w", encoding="utf-8") as f:
            f.write("naver-site-verification: " + nv)

    # robots.txt / sitemap.xml / feed.xml
    base = CONFIG["BASE_URL"].rstrip("/")
    with open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /groups/room/\nDisallow: /cdn-cgi/\n\n"
                f"User-agent: Yeti\nAllow: /\nDisallow: /admin/\n\nSitemap: {base}/sitemap.xml\n")
    def url_xml(p):
        lm = f"<lastmod>{lastmod[p]}</lastmod>" if lastmod.get(p) else ""
        return f"<url><loc>{base}{p}</loc>{lm}</url>"
    urls = "".join(url_xml(p) for p in paths if not p.endswith(".html") and p != "/groups/room/")
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>")
    from email.utils import format_datetime
    from datetime import datetime, timezone, timedelta
    def rfc(d):
        try:
            return format_datetime(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=9))))
        except Exception:
            return ""
    rss_items = "".join(
        f"<item><title>{E(t['name'])}</title><link>{base}/fact/{E(t['id'])}/</link>"
        f"<guid>{base}/fact/{E(t['id'])}/</guid><description>{E(t.get('summary',''))}</description>"
        f"<pubDate>{rfc(t.get('checked',''))}</pubDate></item>" for t in pub_targets)
    with open(os.path.join(DIST, "feed.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
                f"<title>{E(CONFIG['NAME_KO'])} {E(CONFIG['NAME_EN'])} — 검증 대상</title><link>{base}/fact/</link>"
                f"<description>부업·수익화 강의의 주장과 확인된 사실</description><language>ko</language>"
                + rss_items + "</channel></rss>")

    total = sum(len(files) for _, _, files in os.walk(DIST))
    print(f"빌드 완료 — 페이지 {len(paths)+1}개, 파일 {total}개 → {DIST}/")

if __name__ == "__main__":
    main()
