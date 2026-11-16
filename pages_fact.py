# -*- coding: utf-8 -*-
"""
FACT&DO — 검증 대상 · 외부 후기 · 공공기록 · 제보 안내 페이지 생성기
build.py 가 불러 씁니다. 데이터는 data/targets.json, reviews.json, records.json 입니다.
'공개' 상태인 항목만 페이지로 만들어집니다.
"""
import html
from urllib.parse import urlparse

E = html.escape

KIND_CLS = {"유료 강의": "k-course", "강의 플랫폼": "k-platform", "무료 특강·강연": "k-talk",
            "커뮤니티·모임": "k-group", "주제": "k-topic"}


def host(url):
    try:
        h = urlparse(url).netloc
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""


def ext(url, label, cls=""):
    if not url:
        return ""
    return f'<a class="{cls}" href="{E(url)}" target="_blank" rel="noopener nofollow">{E(label)}</a>'


def src_link(url):
    return f' <a class="src" href="{E(url)}" target="_blank" rel="noopener nofollow">출처 · {E(host(url))}</a>' if url else ""


def public(items):
    return [i for i in items if i.get("status") == "공개"]


def reviews_of(reviews, tid):
    out = [r for r in public(reviews) if r.get("target_id") == tid]
    return sorted(out, key=lambda r: (r.get("read_level") != "본문 확인", r.get("posted") or ""), reverse=False)


def target_card(t, reviews):
    n_rv = len(reviews_of(reviews, t["id"]))
    cats = "".join(f"<span>{E(c)}</span>" for c in t.get("category", []))
    return f"""<article class="card fact-card" data-kind="{E(t.get('kind',''))}" data-cat="{E('|'.join(t.get('category', [])))}" data-q="{E((t['name'] + ' ' + t.get('summary','') + ' ' + t.get('provider','')).lower())}">
  <div class="ex-top"><span class="layer-tag {KIND_CLS.get(t.get('kind',''), '')}">{E(t.get('kind',''))}</span><span class="mono dim">확인 {E(t.get('checked',''))}</span></div>
  <h3><a href="/fact/{E(t['id'])}/">{E(t['name'])}</a></h3>
  <p class="ex-desc">{E(t.get('summary',''))}</p>
  <div class="ex-tags">{cats}</div>
  <ul class="fact-counts mono">
    <li><b>{len(t.get('claims', []))}</b>주장</li><li><b>{len(t.get('facts', []))}</b>확인</li>
    <li><b>{len(t.get('unknowns', []))}</b>미확인</li><li><b>{n_rv}</b>외부 후기</li>
  </ul>
  <div class="ex-foot"><span class="state-tag">{E(t.get('verdict','판정 전'))}</span><a class="btn-mini" href="/fact/{E(t['id'])}/">자세히 보기</a></div>
</article>"""


def review_card(r, targets_by_id, show_target=True):
    t = targets_by_id.get(r.get("target_id"))
    tlink = (f'<a class="rv-target" href="/fact/{E(t["id"])}/">{E(t["name"])}</a>' if (t and show_target) else "")
    read_ok = r.get("read_level") == "본문 확인"
    meta = " · ".join(x for x in [r.get("platform", ""), ("게시 " + r["posted"]) if r.get("posted") else "게시일 미확인",
                                  "수집 " + r.get("collected", "")] if x)
    chips = f'<span class="e-chip">E0 · 미인증</span><span class="rl-chip {"ok" if read_ok else "no"}">{E(r.get("read_level",""))}</span>'
    if read_ok and r.get("tone"):
        chips += f'<span class="tone-chip">{E(r["tone"])}</span>'
    extra = ""
    if read_ok:
        extra = f'<p class="rv-rel mono">결제: {E(r.get("paid","미확인"))} · 관계: {E(r.get("relation","미확인"))}</p>'
    return f"""<article class="card rv-ext" data-read="{'1' if read_ok else '0'}">
  <div class="rv-chips">{chips}</div>
  {tlink}
  <h3>{E(r.get('title',''))}</h3>
  <p>{E(r.get('summary',''))}</p>
  {extra}
  <div class="ex-foot"><span class="mono dim">{E(meta)}</span>{ext(r.get('url',''), '원문 보기', 'btn-mini')}</div>
</article>"""


# ─────────────────────────────────────────────────────────────
def build_fact_index(ctx, targets, reviews):
    items = public(targets)
    kinds = []
    for t in items:
        if t.get("kind") and t["kind"] not in kinds:
            kinds.append(t["kind"])
    cats = []
    for t in items:
        for c in t.get("category", []):
            if c not in cats:
                cats.append(c)
    kchips = '<button type="button" class="chip on" data-v="">전체</button>' + "".join(
        f'<button type="button" class="chip" data-v="{E(k)}">{E(k)}</button>' for k in kinds)
    cchips = '<button type="button" class="chip on" data-v="">전체</button>' + "".join(
        f'<button type="button" class="chip" data-v="{E(c)}">{E(c)}</button>' for c in cats)
    cards = "".join(target_card(t, reviews) for t in items)
    n_rv = len(public(reviews))
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow t-cobalt">FACT · 검증 대상</span>
    <h1>무엇을 주장하고, 무엇이 확인됐는지</h1>
    <p>수익을 약속하는 강의·클래스·특강을 하나씩 열어, 판매 페이지의 주장과 우리가 직접 확인한 사실,
    아직 확인하지 못한 것을 나눠 적습니다. 좋다·나쁘다는 판정은 근거가 쌓인 뒤에만 붙입니다.</p>
    <p class="beta-note"><span class="beta-tag">기준</span>현재 {len(items)}개 대상 · 외부 공개 후기 {n_rv}건 · 기준일 {E(ctx.CONFIG['DATA_DATE'])}.
    모든 대상은 ‘판정 전’ 상태이며, 공개된 정보만 출처와 함께 정리했습니다.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="ex-bar"><input id="fx-search" type="search" placeholder="이름·설명 검색" aria-label="검증 대상 검색"></div>
    <div class="chip-row" id="fx-kinds" role="group" aria-label="유형 필터">{kchips}</div>
    <div class="chip-row" id="fx-cats" role="group" aria-label="카테고리 필터">{cchips}</div>
    <p class="ex-meta"><b id="fx-count">{len(items)}</b>개 대상</p>
    <div id="fx-list" class="ex-list">{cards}</div>
    <div id="fx-empty" class="empty" hidden>
      <b>조건에 맞는 대상이 없습니다</b>
      <p>확인이 필요한 강의나 채널을 알고 계시면 알려 주세요. 직접 조사해 등록합니다.</p>
      <a class="btn btn-ghost" href="/report/">검증 요청하기</a>
    </div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap">
    {ctx.sec_head("HOW TO READ", "이 목록을 읽는 법")}
    <div class="grid3">
      <div class="card"><b>주장 ≠ 사실</b><p>‘주장’은 판매 페이지에 적힌 문구를 그대로 옮긴 것입니다. 우리가 사실이라고 확인했다는 뜻이 아닙니다.</p></div>
      <div class="card"><b>미확인은 미확인으로</b><p>가격·환불·성과 중 확인하지 못한 것은 빈칸으로 두지 않고 ‘미확인’이라고 적습니다.</p></div>
      <div class="card"><b>틀린 내용은 고칩니다</b><p>당사자와 이용자 누구나 정정을 요청할 수 있습니다. 접수부터 회신까지의 절차를 공개합니다.</p>
      <a class="link-more t-cobalt" href="/report/">정정·이의제기 안내 →</a></div>
    </div>
    <p class="fine center">교육 판매 플랫폼, 실행 모임, 거래 채널 같은 주변 서비스는 <a class="t-cobalt" href="/explore/">생태계 탐색</a>에서 볼 수 있습니다.</p>
  </div>
</section>
"""
    return ctx.page("/fact/", "검증 대상 — 부업·수익화 강의의 주장과 확인된 사실",
                    "부업·수익화 강의와 특강의 수익 주장, 확인된 가격·환불 규정, 미확인 항목, 외부 공개 후기를 출처와 함께 정리합니다.",
                    body, active="/fact/")


def build_fact_detail(ctx, t, targets, reviews):
    tb = {x["id"]: x for x in targets}
    rvs = reviews_of(reviews, t["id"])
    claims = "".join(f"<li>{E(c.get('text',''))}{src_link(c.get('src',''))}</li>" for c in t.get("claims", [])) \
        or '<li class="dim">수집된 주장이 없습니다.</li>'
    facts = "".join(
        f'<tr><th scope="row">{E(f.get("label",""))}</th><td>{E(f.get("value",""))}{src_link(f.get("src",""))}</td></tr>'
        for f in t.get("facts", [])) or '<tr><td colspan="2" class="dim">확인된 사실이 아직 없습니다.</td></tr>'
    unknowns = "".join(f"<li>{E(u)}</li>" for u in t.get("unknowns", [])) or '<li class="dim">없음</li>'
    sources = "".join(
        f'<li>{ext(s.get("url",""), s.get("title",""))} <span class="mono dim">확인 {E(s.get("date",""))}</span></li>'
        for s in t.get("sources", []))
    read = [r for r in rvs if r.get("read_level") == "본문 확인"]
    link_only = [r for r in rvs if r.get("read_level") != "본문 확인"]
    rv_html = "".join(review_card(r, tb, show_target=False) for r in read)
    if link_only:
        lis = "".join(
            f'<li>{ext(r.get("url",""), r.get("title",""))} <span class="mono dim">{E(r.get("platform",""))}'
            f'{(" · " + E(r["posted"])) if r.get("posted") else ""}</span>'
            f'{("<br><span class=dim>" + E(r.get("summary","")) + "</span>") if r.get("summary") else ""}</li>'
            for r in link_only)
        rv_html += f"""<div class="card rv-links"><b>본문을 확인하지 못한 후기 링크</b>
<p>아래 글은 도구 제한으로 본문을 읽지 못해 제목과 게시일만 확인했습니다. 내용은 요약하지 않았으니 직접 읽고 판단해 주세요.</p>
<ul>{lis}</ul></div>"""
    if not rvs:
        rv_html = '<div class="empty"><b>수집된 외부 후기가 없습니다</b><p>수강 경험이 있다면 팩트리뷰로 남겨 주세요.</p><a class="btn btn-ghost" href="/reviews/new/">팩트리뷰 작성</a></div>'
    internal = (f'<p class="fine"><b>판매처 안의 후기</b> — {E(t["internal_reviews"])}</p>' if t.get("internal_reviews") else "")
    official = ext(t.get("url", ""), "공식 페이지 열기", "btn btn-ghost") if t.get("url") else ""
    cats = "".join(f"<span>{E(c)}</span>" for c in t.get("category", []))
    body = f"""
<section class="page-head slim">
  <div class="wrap">
    <p class="crumb mono"><a href="/fact/">검증 대상</a> / {E(t.get('kind',''))}</p>
    <h1>{E(t['name'])}</h1>
    <p>{E(t.get('summary',''))}</p>
    <div class="fd-meta">
      <span class="layer-tag {KIND_CLS.get(t.get('kind',''), '')}">{E(t.get('kind',''))}</span>
      <span class="verdict-tag">{E(t.get('verdict','판정 전'))}</span>
      <span class="mono dim">확인일 {E(t.get('checked',''))}{(' · 다음 점검 ' + E(t['next_check'])) if t.get('next_check') else ''}</span>
    </div>
    <div class="ex-tags">{cats}</div>
    <div class="hero-cta">{official}<a class="btn btn-ghost" href="/report/?target={E(t['id'])}">정정·이의제기</a></div>
  </div>
</section>
<section class="sec">
  <div class="wrap fd-grid">
    <div class="fd-main">
      <div class="card fd-box claim-box">
        <span class="eyebrow t-coral">CLAIM · 판매 페이지의 주장</span>
        <p class="fine">판매 페이지에 적힌 내용을 옮긴 것입니다. 사실로 확인됐다는 뜻이 아닙니다.</p>
        <ul class="fd-list">{claims}</ul>
      </div>
      <div class="card fd-box fact-box">
        <span class="eyebrow t-cobalt">FACT · 직접 확인한 사실</span>
        <div class="table-wrap"><table class="fd-table"><tbody>{facts}</tbody></table></div>
      </div>
      <div class="card fd-box unk-box">
        <span class="eyebrow">UNKNOWN · 아직 확인하지 못한 것</span>
        <ul class="fd-list">{unknowns}</ul>
      </div>
      <div class="fd-reviews">
        {ctx.sec_head("REVIEWS", "외부에 공개된 후기", "블로그 등에 공개된 글을 요약했습니다. 구매·수료를 우리가 확인한 후기가 아니므로 모두 E0(미인증)입니다.")}
        {rv_html}
        {internal}
      </div>
    </div>
    <aside class="fd-side">
      <div class="card">
        <b>한눈에</b>
        <dl class="fd-dl">
          <dt>운영 주체</dt><dd>{E(t.get('provider','미확인') or '미확인')}</dd>
          <dt>가격</dt><dd>{E(t.get('price','미확인') or '미확인')}</dd>
          <dt>환불</dt><dd>{E(t.get('refund','미확인') or '미확인')}</dd>
          <dt>판정</dt><dd>{E(t.get('verdict','판정 전'))}</dd>
          <dt>등록 경로</dt><dd>{E(t.get('registered_via','직접 조사'))}</dd>
        </dl>
      </div>
      <div class="card">
        <b>출처</b>
        <ul class="fd-src">{sources or '<li class="dim">출처 없음</li>'}</ul>
      </div>
      <div class="card fd-notice">
        <b>당사자·이용자께</b>
        <p>사실과 다른 내용이 있으면 알려 주세요. 접수 → 검토 → 결정 → 회신 순서로 처리하고, 확인된 오류는 바로 고칩니다. 공식 답변을 보내 주시면 이 페이지에 분리해 싣습니다.</p>
        <a class="link-more t-cobalt" href="/report/?target={E(t['id'])}">정정·이의제기 방법 →</a>
      </div>
    </aside>
  </div>
</section>
"""
    return ctx.page(f"/fact/{t['id']}/", f"{t['name']} — 주장과 확인된 사실",
                    (t.get("summary", "") + " 판매 페이지의 주장, 확인된 사실, 미확인 항목, 외부 후기를 출처와 함께 정리했습니다.")[:155],
                    body, active="/fact/")


def build_reviews_page(ctx, targets, reviews):
    tb = {x["id"]: x for x in public(targets)}
    items = [r for r in public(reviews) if r.get("target_id") in tb]
    read = sorted([r for r in items if r.get("read_level") == "본문 확인"], key=lambda r: r.get("posted") or "", reverse=True)
    links = sorted([r for r in items if r.get("read_level") != "본문 확인"], key=lambda r: r.get("posted") or "", reverse=True)
    cards = "".join(review_card(r, tb) for r in read)
    link_lis = "".join(
        f'<li>{ext(r.get("url",""), r.get("title",""))} <span class="mono dim">{E(r.get("platform",""))}'
        f'{(" · " + E(r["posted"])) if r.get("posted") else ""}</span> — <a class="t-cobalt" href="/fact/{E(r["target_id"])}/">{E(tb[r["target_id"]]["name"])}</a></li>'
        for r in links)
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow t-cobalt">FACT · 팩트리뷰</span>
    <h1>별점이 아니라, 조건·투입·결과를 남기는 리뷰</h1>
    <p>누가, 어떤 조건에서, 시간과 비용을 얼마나 들여, 무엇을 했고, 어떤 결과가 나왔는지를 봅니다.
    성과가 없었거나 중간에 멈춘 경험도 다음 사람에게는 같은 가치의 정보입니다.</p>
    <div class="hero-cta">
      <a class="btn btn-cobalt" href="/reviews/new/">팩트리뷰 작성하기</a>
      <a class="btn btn-ghost" href="/standards/">작성·평가 기준 보기</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {ctx.sec_head("COLLECTED", "외부에 공개된 후기 모음", f"블로그·수강평 등에 공개된 글 {len(items)}건을 출처와 함께 정리했습니다. 원문을 옮기지 않고 요약만 싣습니다.")}
    <p class="beta-note"><span class="beta-tag">E0</span>여기 실린 후기는 구매·수료 여부를 팩트앤두가 확인하지 않은 글입니다.
    그래서 모두 ‘E0 · 미인증’으로 표시하고, 작성자가 밝힌 결제 여부와 판매처와의 관계를 함께 적습니다.</p>
    <div class="ex-list rv-ext-list">{cards}</div>
    {f'<div class="card rv-links"><b>본문을 확인하지 못한 후기 링크 {len(links)}건</b><p>제목과 게시일만 확인한 글입니다. 내용은 요약하지 않았습니다.</p><ul>{link_lis}</ul></div>' if links else ''}
  </div>
</section>
<section class="sec alt">
  <div class="wrap">
    {ctx.sec_head("VERIFIED", "인증 팩트리뷰")}
    <div class="empty">
      <b>아직 인증된 리뷰가 없습니다</b>
      <p>구매·수료·실행 증빙을 확인한 리뷰(E1 이상)는 파운딩 리뷰어와 함께 채워 갑니다.
      표본이 5개 미만인 과정은 종합점수 대신 ‘초기 표본’으로만 표시합니다.</p>
      <a class="btn btn-ghost" href="/waitlist/">파운딩 리뷰어 신청</a>
    </div>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {ctx.sec_head("MINE", "내가 쓴 리뷰", "작성한 리뷰는 이 브라우저에 저장됩니다. JSON으로 내보내 백업할 수 있습니다.")}
    <div id="rv-local-list" class="rv-list"></div>
    <div id="rv-local-empty" class="empty">
      <b>이 브라우저에 저장된 리뷰가 없습니다</b>
      <p>작성한 리뷰 초안과 제출본이 여기에 표시됩니다.</p>
    </div>
  </div>
</section>
"""
    return ctx.page("/reviews/", "팩트리뷰 — 외부 공개 후기와 인증 리뷰",
                    "부업·수익화 강의에 대해 외부에 공개된 후기를 출처와 함께 요약하고, 구매·수료 증빙을 확인한 팩트리뷰를 따로 모읍니다.",
                    body, active="/reviews/")


def build_records_page(ctx, records):
    items = sorted(public(records), key=lambda r: r.get("date") or "", reverse=True)
    rows = "".join(f"""<article class="card rec-card">
  <div class="ex-top"><span class="layer-tag">{E(r.get('type',''))}</span><span class="mono dim">{E(r.get('date',''))}</span></div>
  <h3>{E(r.get('title',''))}</h3>
  <p class="mono dim">{E(r.get('org',''))}</p>
  <p>{E(r.get('summary',''))}</p>
  <div class="ex-foot"><span></span>{ext(r.get('url',''), '원문 보기', 'btn-mini')}</div>
</article>""" for r in items)
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">RECORDS · 공공기록과 보도</span>
    <h1>통계와 보도로 보는 부업 강의 시장</h1>
    <p>공공기관이 발표한 통계와 언론 보도를 모았습니다. 대부분 특정 업체를 지목하지 않는 자료이며,
    어떤 대상을 먼저 살펴볼지 정하는 근거로 씁니다.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="ex-list">{rows}</div>
    <p class="fine center">피해가 발생했다면 소비자상담센터(국번 없이 1372)에 상담을 신청할 수 있습니다.</p>
  </div>
</section>
"""
    return ctx.page("/records/", "공공기록·보도 — 부업 강의 피해 통계와 언론 보도",
                    "한국소비자원 피해구제 통계, 방송·언론 보도 등 부업·수익화 강의 시장을 다룬 공개 기록을 모았습니다.",
                    body, active="")


def build_report_page(ctx, dispute_steps):
    C = ctx.CONFIG
    email, form = C.get("CONTACT_EMAIL", ""), C.get("REPORT_FORM_URL", "")
    if form:
        channel = f'<a class="btn btn-cobalt btn-lg" href="{E(form)}" target="_blank" rel="noopener">접수 양식 열기</a>'
        if email:
            channel += f'<p class="fine">양식이 어렵다면 <a class="t-cobalt" href="mailto:{E(email)}">{E(email)}</a> 로 보내셔도 됩니다.</p>'
    elif email:
        channel = (f'<a id="rp-mail" class="btn btn-cobalt btn-lg" href="mailto:{E(email)}?subject=%5B%ED%8C%A9%ED%8A%B8%EC%95%A4%EB%91%90%5D%20%EC%A0%9C%EB%B3%B4%C2%B7%EC%A0%95%EC%A0%95%20%EC%9A%94%EC%B2%AD">메일로 접수하기</a>'
                   f'<p class="fine">받는 주소: {E(email)} · 접수 후 48시간 안에 확인 메일을 드립니다.</p>')
    else:
        channel = ('<span class="btn btn-lg btn-disabled" aria-disabled="true">접수 창구 준비 중</span>'
                   '<p class="fine">접수 메일 주소를 준비하고 있습니다. 연결되면 이 버튼이 바로 열립니다.</p>')
    steps = "".join(f"<li><b>{E(t)}</b><p>{E(d)}</p></li>" for t, d in dispute_steps)
    body = f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow t-cobalt">REPORT · 제보 · 정정 · 이의제기</span>
    <h1>틀린 내용은 고치고, 반론은 절차로 받습니다</h1>
    <p>확인이 필요한 강의를 알려 주시거나, 실린 내용에 대한 정정·이의를 접수하는 곳입니다.
    누가 요청했는지에 따라 결과가 달라지지 않도록 같은 순서로 처리합니다.</p>
    <p id="rp-target" class="beta-note" hidden><span class="beta-tag">대상</span><span id="rp-target-name"></span></p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="grid3">
      <div class="card"><b class="mono t-cobalt">01</b><b>검증 요청·제보</b><p>수익을 약속하는 강의·특강·오픈채팅을 보셨다면 이름과 링크를 알려 주세요. 광고 캡처가 있으면 더 좋습니다.</p></div>
      <div class="card"><b class="mono t-cobalt">02</b><b>정정 요청</b><p>가격·환불 규정·운영 주체 등 사실 정보가 바뀌었거나 틀렸다면, 근거가 되는 페이지 주소와 함께 알려 주세요.</p></div>
      <div class="card"><b class="mono t-cobalt">03</b><b>이의제기·공식 답변</b><p>당사자(판매자·강사)는 실린 내용에 이의를 제기하거나 공식 답변을 보낼 수 있습니다. 답변은 해당 페이지에 분리해 싣습니다.</p></div>
    </div>
    <div class="wl-action">{channel}</div>
  </div>
</section>
<section class="sec alt">
  <div class="wrap split">
    <div class="split-copy">
      {ctx.sec_head("PROCESS", "처리 순서")}
      <ol class="dispute-steps">{steps}</ol>
    </div>
    <div class="split-copy">
      {ctx.sec_head("WHAT TO SEND", "보내실 때 적어 주세요")}
      <ul class="rule-list">
        <li>어떤 페이지의 어느 문장인지 (주소를 붙여 주세요)</li>
        <li>무엇이 어떻게 다른지, 그리고 근거가 되는 자료나 링크</li>
        <li>당사자인 경우 소속과 회신받을 연락처</li>
        <li>회신에 꼭 필요한 정보만 보내 주세요. 주민등록번호·계좌번호 같은 정보는 받지 않습니다.</li>
      </ul>
      <p class="fine">보내 주신 연락처는 회신 목적으로만 쓰고, 처리가 끝나면 보관 기한에 따라 지웁니다.
      접수 내용과 결정 이력은 분쟁에 대비해 보존합니다.</p>
    </div>
  </div>
</section>
"""
    return ctx.page("/report/", "제보·정정·이의제기",
                    "검증이 필요한 강의 제보, 사실 정보 정정 요청, 당사자 이의제기와 공식 답변 접수 방법과 처리 절차를 안내합니다.",
                    body, active="")


def home_fact_section(ctx, targets, reviews, records):
    items = public(targets)
    pick = items[:6]
    cards = "".join(target_card(t, reviews) for t in pick)
    return f"""
<section class="sec fact-home">
  <div class="wrap">
    {ctx.sec_head("NOW ON FACT&DO", "지금 살펴보고 있는 강의들", "판매 페이지의 주장과 확인된 사실, 아직 모르는 것을 나눠 적었습니다.")}
    <ul class="stat-row mono">
      <li><b>{len(items)}</b>검증 대상</li>
      <li><b>{len(public(reviews))}</b>외부 공개 후기</li>
      <li><b>{len(public(records))}</b>공공기록·보도</li>
      <li><b>0</b>인증 팩트리뷰<small>모집 중</small></li>
    </ul>
    <div class="ex-list">{cards}</div>
    <p class="center" style="margin-top:22px"><a class="btn btn-cobalt" href="/fact/">검증 대상 전체 보기</a></p>
  </div>
</section>
"""
