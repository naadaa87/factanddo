/* ============================================================
   FACT&DO 관리자 화면 (/admin/)
   - 서버 없이 동작합니다. 데이터는 GitHub 저장소의 data/*.json 이고,
     [사이트에 반영]을 누르면 저장소에 커밋 → Cloudflare Pages가 1~2분 안에 다시 배포합니다.
   - 저장하려면 이 저장소에만 쓰기 권한이 있는 GitHub 토큰이 필요합니다(이 브라우저에만 보관).
   - 토큰이 없으면 '읽기 전용'으로 열립니다. 고친 내용은 백업 파일로만 내려받을 수 있습니다.
   ============================================================ */
(function () {
  "use strict";
  var CFG = window.FD_ADMIN || {};
  var REPO = CFG.repo || "", BR = CFG.branch || "main";
  var API = "https://api.github.com/repos/" + REPO;
  var FILES = { targets: "data/targets.json", reviews: "data/reviews.json", records: "data/records.json",
                cases: "data/cases.json", services: "data/services.json", site: "data/site.json" };
  var TKEY = "fd_admin_token";
  var S = { raw: {}, sha: {}, dirty: {}, source: "", token: "", commits: null, q: "", f: "", msg: "" };
  try { S.token = localStorage.getItem(TKEY) || ""; } catch (e) {}

  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var esc = function (v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var today = function (plus) {
    var d = new Date(Date.now() + (plus || 0) * 864e5);
    return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  };
  var b64e = function (str) { return btoa(unescape(encodeURIComponent(str))); };
  var b64d = function (s) { return decodeURIComponent(escape(atob(String(s).replace(/\s/g, "")))); };
  var items = function (name) { return (S.raw[name] && S.raw[name].items) || []; };
  var get = function (o, path) { return path.split(".").reduce(function (a, k) { return a == null ? a : a[k]; }, o); };
  var set = function (o, path, v) {
    var ks = path.split("."), last = ks.pop();
    var t = ks.reduce(function (a, k) { if (a[k] == null || typeof a[k] !== "object") a[k] = {}; return a[k]; }, o);
    t[last] = v;
  };

  /* ---------- 화면 정의(스키마) ---------- */
  var ST_T = ["후보", "접수", "초안", "공개", "보류", "반려"];
  var SCHEMA = {
    targets: {
      label: "검증 대상", one: "검증 대상", statusKey: "status", statuses: ST_T,
      cols: [["name", "이름"], ["kind", "유형"], ["status", "상태"], ["verdict", "판정"], ["checked", "확인일"], ["next_check", "다음 점검"]],
      blank: function () {
        return { id: "", name: "", kind: "유료 강의", provider: "", category: [], url: "", status: "후보", verdict: "판정 전",
                 summary: "", claims: [], facts: [], unknowns: [], price: "미확인", refund: "미확인", internal_reviews: "",
                 sources: [], checked: today(), next_check: today(182), ad_checked: false,
                 notice: { state: "미통보", date: "", memo: "" }, registered_via: "직접 조사", note: "" };
      },
      fields: [
        { sec: "기본 정보" },
        { k: "name", label: "이름", req: 1, ph: "예: ○○클래스 ‘△△ 수익화’ 강의" },
        { k: "id", label: "주소용 ID", req: 1, ph: "영문 소문자·숫자·하이픈 (예: abc-class)", help: "페이지 주소 /fact/ID/ 에 쓰입니다. 공개한 뒤에는 바꾸지 마세요." },
        { k: "kind", label: "유형", type: "select", opts: ["유료 강의", "강의 플랫폼", "무료 특강·강연", "커뮤니티·모임", "주제"] },
        { k: "provider", label: "운영 주체", ph: "사이트 하단 표기 그대로" },
        { k: "category", label: "카테고리", type: "tags", ph: "쉼표로 구분: AI·자동화, 콘텐츠 수익화, 이커머스, 공통" },
        { k: "url", label: "공식 URL", ph: "https://" },
        { k: "summary", label: "한 줄 소개", type: "area", rows: 3, help: "평가 없이 ‘무엇을 파는 곳인지’만 적습니다." },
        { sec: "주장 → 사실 → 미확인" },
        { k: "claims", label: "판매 페이지의 주장", type: "rows", cols: [["text", "주장(화면에 적힌 그대로 옮기기)", 3], ["src", "출처 URL", 2]] },
        { k: "facts", label: "직접 확인한 사실", type: "rows", cols: [["label", "항목", 1], ["value", "확인한 내용", 3], ["src", "출처 URL", 2]] },
        { k: "unknowns", label: "미확인 항목", type: "lines", rows: 4, help: "한 줄에 하나씩. 모르는 것을 빈칸으로 두지 않습니다." },
        { k: "price", label: "가격", ph: "확인일과 함께. 모르면 ‘미확인’" },
        { k: "refund", label: "환불", ph: "요약. 모르면 ‘미확인’" },
        { k: "internal_reviews", label: "판매처 안의 후기", type: "area", rows: 2 },
        { k: "sources", label: "출처 목록", type: "rows", cols: [["title", "제목", 2], ["url", "URL", 3], ["date", "확인일", 1]] },
        { sec: "상태와 공개" },
        { k: "status", label: "상태", type: "select", opts: ST_T, help: "‘공개’만 사이트에 나옵니다." },
        { k: "verdict", label: "판정", type: "select", opts: ["판정 전", "주장 확인됨", "일부 확인", "근거 부족", "주장과 다름"], help: "‘판정 전’이 아닌 값은 당사자 통보 뒤에만 공개할 수 있습니다." },
        { k: "checked", label: "확인일", type: "date" },
        { k: "next_check", label: "다음 점검일", type: "date" },
        { k: "ad_checked", label: "광고·협찬 관계 없음 확인", type: "check", help: "이 대상에게서 대가를 받은 사실이 없음을 확인했습니다." },
        { k: "registered_via", label: "등록 경로", type: "select", opts: ["직접 조사", "제보", "사업자 자체 등록"] },
        { sec: "당사자 통보" },
        { k: "notice.state", label: "통보 상태", type: "select", opts: ["미통보", "통보함", "답변 받음", "해당 없음"] },
        { k: "notice.date", label: "통보일", type: "date" },
        { k: "notice.memo", label: "통보 메모", type: "area", rows: 2 },
        { k: "note", label: "내부 메모", type: "area", rows: 2, help: "저장소가 공개 상태이면 이 메모도 GitHub에서 보입니다. 민감한 내용은 적지 마세요." }
      ]
    },
    reviews: {
      label: "외부 후기", one: "후기", statusKey: "status", statuses: ["초안", "공개", "비공개"],
      cols: [["title", "제목"], ["target_id", "대상"], ["platform", "출처"], ["read_level", "확인 수준"], ["posted", "게시일"], ["status", "상태"]],
      blank: function () {
        return { id: nextId("reviews", "rv-", 3), target_id: "", title: "", url: "", platform: "", posted: "", collected: today(),
                 read_level: "본문 확인", tone: "미분류", paid: "", relation: "표기 없음", summary: "", evidence: "E0", status: "초안" };
      },
      fields: [
        { sec: "출처" },
        { k: "target_id", label: "검증 대상", type: "target", req: 1 },
        { k: "title", label: "글 제목", req: 1 },
        { k: "url", label: "원문 URL", req: 1, ph: "https://" },
        { k: "platform", label: "출처 종류", ph: "네이버 블로그 / 티스토리 / 브런치 / 인프런 수강평 / 유튜브 …" },
        { k: "posted", label: "게시일", type: "date" },
        { k: "collected", label: "수집일", type: "date" },
        { sec: "내용" },
        { k: "read_level", label: "확인 수준", type: "select", opts: ["본문 확인", "제목·게시일만 확인"] },
        { k: "tone", label: "논조", type: "select", opts: ["미분류", "긍정", "중립", "부정", "혼합"] },
        { k: "paid", label: "결제 여부(작성자 서술)", ph: "예: 직접 결제했다고 서술 / 무료 수강 / 미확인" },
        { k: "relation", label: "판매처와의 관계", ph: "예: 표기 없음 / 협찬 표기 / 제휴 링크 포함" },
        { k: "summary", label: "요약", type: "area", rows: 5, help: "원문을 옮겨 적지 말고 내 말로 요약합니다. 금액은 매출인지 순이익인지 구분해 적습니다." },
        { k: "evidence", label: "증빙 레벨", type: "select", opts: ["E0", "E1", "E2", "E3", "E4", "E5"], help: "외부에서 수집한 글은 E0입니다." },
        { k: "status", label: "상태", type: "select", opts: ["초안", "공개", "비공개"] },
        { k: "id", label: "ID", req: 1 }
      ]
    },
    records: {
      label: "공공기록·보도", one: "기록", statusKey: "status", statuses: ["초안", "공개", "비공개"],
      cols: [["title", "제목"], ["org", "기관·매체"], ["type", "종류"], ["date", "날짜"], ["status", "상태"]],
      blank: function () { return { id: nextId("records", "rc-", 3), org: "", type: "언론 보도", title: "", date: "", url: "", summary: "", status: "초안" }; },
      fields: [
        { k: "title", label: "제목", req: 1 }, { k: "org", label: "기관·매체", req: 1 },
        { k: "type", label: "종류", type: "select", opts: ["공공 통계", "공공기관 발표", "언론 보도", "방송 보도", "판결·결정", "플랫폼 정책"] },
        { k: "date", label: "날짜", type: "date" }, { k: "url", label: "원문 URL", req: 1 },
        { k: "summary", label: "요약", type: "area", rows: 4 },
        { k: "status", label: "상태", type: "select", opts: ["초안", "공개", "비공개"] }, { k: "id", label: "ID", req: 1 }
      ]
    },
    cases: {
      label: "제보·이의제기", one: "접수 건", statusKey: "stage", statuses: ["접수", "검토", "결정", "회신 완료", "재심"],
      warn: "이름·연락처·메일 주소 같은 개인정보는 여기에 적지 않습니다. 원문은 메일함에 두고, 여기에는 처리 경과만 남깁니다.",
      cols: [["id", "접수번호"], ["type", "종류"], ["target_id", "대상"], ["received", "접수일"], ["due", "회신 기한"], ["stage", "단계"]],
      blank: function () {
        return { id: nextId("cases", "C-" + today().slice(0, 4) + "-", 3), type: "정정 요청", target_id: "", received: today(),
                 due: today(10), stage: "접수", issue: "", result: "", decided: "" };
      },
      fields: [
        { k: "id", label: "접수번호", req: 1 },
        { k: "type", label: "종류", type: "select", opts: ["검증 요청·제보", "정정 요청", "이의제기", "공식 답변", "권리침해 신고"] },
        { k: "target_id", label: "관련 대상", type: "target" },
        { k: "received", label: "접수일", type: "date" },
        { k: "due", label: "회신 기한", type: "date", help: "접수 확인은 48시간, 1차 판단은 7영업일이 목표입니다." },
        { k: "stage", label: "단계", type: "select", opts: ["접수", "검토", "결정", "회신 완료", "재심"] },
        { k: "issue", label: "쟁점 요약", type: "area", rows: 3, help: "개인정보 없이 쟁점만." },
        { k: "result", label: "결정과 조치", type: "area", rows: 3 },
        { k: "decided", label: "결정일", type: "date" }
      ]
    },
    services: {
      label: "생태계 서비스", one: "서비스", statusKey: "layer", statuses: ["교육 판매", "비교·리뷰", "커뮤니티", "실행 모임", "수익 실행"],
      cols: [["name", "이름"], ["layer", "유형"], ["url", "URL"], ["checked", "확인일"]],
      blank: function () { return { id: nextId("services", "p", 3), kind: "platform", name: "", layer: "교육 판매", category: ["공통"], url: "", desc: "", checked: today(), review_state: "리뷰 표본 없음" }; },
      fields: [
        { k: "name", label: "이름", req: 1 },
        { k: "layer", label: "유형", type: "select", opts: ["교육 판매", "비교·리뷰", "커뮤니티", "실행 모임", "수익 실행"] },
        { k: "category", label: "카테고리", type: "tags" }, { k: "url", label: "공식 URL" },
        { k: "desc", label: "설명", type: "area", rows: 2 }, { k: "checked", label: "확인일", type: "date" },
        { k: "review_state", label: "리뷰 상태", type: "select", opts: ["리뷰 표본 없음", "초기 표본", "수집 중"] }, { k: "id", label: "ID", req: 1 }
      ]
    }
  };
  var SITE_FIELDS = [
    { k: "CONTACT_EMAIL", label: "문의·접수 메일 주소", ph: "예: help@factanddo.com", help: "푸터, 정책, 제보·이의제기 페이지에 표시됩니다. 비워 두면 ‘준비 중’으로 나옵니다." },
    { k: "REPORT_FORM_URL", label: "제보·이의제기 접수 양식 URL", ph: "구글폼·탈리 등 (선택)" },
    { k: "WAITLIST_FORM_URL", label: "사전등록 양식 URL", ph: "구글폼·탈리 등" },
    { k: "OPENCHAT_URL", label: "오픈채팅 URL", ph: "선택" },
    { k: "NOTICE", label: "상단 공지 한 줄", ph: "비우면 표시하지 않음" },
    { k: "DATA_DATE", label: "데이터 기준일", type: "date" }
  ];
  function nextId(name, prefix, pad) {
    var max = 0;
    items(name).forEach(function (it) {
      if (String(it.id).indexOf(prefix) === 0) { var n = parseInt(String(it.id).slice(prefix.length), 10); if (n > max) max = n; }
    });
    return prefix + ("0000" + (max + 1)).slice(-pad);
  }

  /* ---------- 공개 게이트 ---------- */
  function gate(name, it) {
    var out = [], ok = function (label, pass) { out.push({ label: label, pass: !!pass }); };
    if (name === "targets") {
      var rows = (it.claims || []).concat(it.facts || []);
      ok("이름·유형·한 줄 소개가 있다", it.name && it.kind && it.summary);
      ok("주장 또는 확인된 사실이 1개 이상이고, 모두 출처 URL이 있다", rows.length > 0 && rows.every(function (r) { return /^https?:\/\//.test(r.src || ""); }));
      ok("출처 목록과 확인일이 있다", (it.sources || []).length > 0 && it.checked);
      ok("미확인 항목을 적었다", (it.unknowns || []).length > 0);
      ok("광고·협찬 관계가 없음을 확인했다", it.ad_checked);
      var needNotice = it.verdict && it.verdict !== "판정 전";
      var st = (it.notice || {}).state;
      ok(needNotice ? "판정을 붙였으므로 당사자에게 통보했다(통보일 기재)" : "판정 전 — 공개 정보 정리만 싣는다",
         !needNotice || ((st === "통보함" || st === "답변 받음") && (it.notice || {}).date));
    } else if (name === "reviews") {
      ok("검증 대상과 연결돼 있다", it.target_id);
      ok("제목과 원문 URL이 있다", it.title && /^https?:\/\//.test(it.url || ""));
      ok("수집일이 있다", it.collected);
      ok("본문을 확인했다면 요약이 있다", it.read_level !== "본문 확인" || (it.summary || "").length >= 20);
    } else if (name === "records") {
      ok("제목·기관·원문 URL이 있다", it.title && it.org && /^https?:\/\//.test(it.url || ""));
    }
    return out;
  }
  var gateFail = function (name, it) { return gate(name, it).filter(function (g) { return !g.pass; }); };

  /* ---------- GitHub 입출력 ---------- */
  function gh(path, opt) {
    opt = opt || {};
    var h = { "Accept": "application/vnd.github+json" };
    if (S.token) h["Authorization"] = "Bearer " + S.token;
    if (opt.body) h["Content-Type"] = "application/json";
    return fetch(API + path, { method: opt.method || "GET", headers: h, body: opt.body ? JSON.stringify(opt.body) : undefined, cache: "no-store" })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok) { var e = new Error(j.message || ("HTTP " + r.status)); e.status = r.status; throw e; }
          return j;
        });
      });
  }
  function loadAll() {
    var names = Object.keys(FILES);
    return Promise.all(names.map(function (n) {
      return gh("/contents/" + FILES[n] + "?ref=" + encodeURIComponent(BR)).then(function (j) {
        S.raw[n] = JSON.parse(b64d(j.content)); S.sha[n] = j.sha;
      });
    })).then(function () { S.source = "github"; }).catch(function (err) {
      // GitHub에서 못 읽으면(요청 한도 등) 배포된 사본으로 엽니다 — 이 경우 저장은 막습니다.
      return fetch("/admin/db.json", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (db) {
        names.forEach(function (n) { S.raw[n] = n === "site" ? db.site : { items: db[n] || [] }; });
        S.source = "snapshot"; S.loadErr = err.message;
      });
    });
  }
  function saveAll() {
    var names = Object.keys(S.dirty).filter(function (n) { return S.dirty[n]; });
    if (!names.length) return Promise.resolve(0);
    if (!S.token) return Promise.reject(new Error("GitHub 토큰이 연결돼 있지 않습니다."));
    if (S.source !== "github") return Promise.reject(new Error("최신 데이터를 읽지 못한 상태입니다. 새로고침 후 다시 시도하세요."));
    var label = names.map(function (n) { return n === "site" ? "사이트 설정" : SCHEMA[n].label; }).join(", ");
    var chain = Promise.resolve();
    names.forEach(function (n) {
      chain = chain.then(function () {
        return gh("/contents/" + FILES[n], { method: "PUT", body: {
          message: "관리자: " + label + " 수정", branch: BR, sha: S.sha[n],
          content: b64e(JSON.stringify(S.raw[n], null, 2) + "\n") } });
      }).then(function (j) { S.sha[n] = j.content.sha; S.dirty[n] = false; });
    });
    return chain.then(function () { S.commits = null; return names.length; });
  }
  function loadCommits() {
    if (S.commits) return Promise.resolve(S.commits);
    return gh("/commits?path=data&per_page=8&sha=" + encodeURIComponent(BR)).then(function (j) {
      S.commits = j.map(function (c) { return { msg: c.commit.message.split("\n")[0], date: c.commit.author.date, url: c.html_url }; });
      return S.commits;
    }).catch(function () { S.commits = []; return S.commits; });
  }

  /* ---------- 공통 UI ---------- */
  var NAV = [["home", "현황판"], ["targets", "검증 대상"], ["reviews", "외부 후기"], ["records", "공공기록·보도"],
             ["cases", "제보·이의제기"], ["services", "생태계 서비스"], ["site", "사이트 설정"], ["connect", "연결·백업"]];
  function dirtyCount() { return Object.keys(S.dirty).filter(function (n) { return S.dirty[n]; }).length; }
  function shell(view, inner) {
    var d = dirtyCount();
    var conn = S.token ? (S.source === "github" ? '<span class="pill ok">저장 가능</span>' : '<span class="pill warn">사본 열람 중</span>')
                       : '<span class="pill">읽기 전용</span>';
    return '<div class="adm">' +
      '<aside class="side"><a class="logo" href="/" title="사이트로">FACT<b>&amp;</b>DO<small>관리자</small></a><nav>' +
      NAV.map(function (n) { return '<a href="#' + n[0] + '"' + (view === n[0] ? ' class="on"' : "") + ">" + n[1] + "</a>"; }).join("") +
      '</nav><p class="side-foot">' + esc(REPO) + " · " + esc(BR) + "</p></aside>" +
      '<div class="main"><header class="top">' + conn +
      '<span class="top-msg">' + (d ? "저장하지 않은 변경이 " + d + "개 파일에 있습니다." : "모든 변경이 반영돼 있습니다.") + "</span>" +
      '<button id="btn-save" class="btn pri"' + (d && S.token && S.source === "github" ? "" : " disabled") + ">사이트에 반영</button></header>" +
      (S.source === "snapshot" ? '<p class="banner warn">GitHub에서 최신 데이터를 읽지 못해 배포된 사본을 보고 있습니다. 잠시 뒤 새로고침하세요. 이 상태에서는 저장할 수 없습니다.</p>' : "") +
      (S.msg ? '<p class="banner">' + esc(S.msg) + "</p>" : "") +
      '<div class="body">' + inner + "</div></div></div>";
  }
  function mount(view, inner) {
    $("#app").innerHTML = shell(view, inner);
    var b = $("#btn-save");
    if (b) b.addEventListener("click", function () {
      b.disabled = true; b.textContent = "반영하는 중…";
      saveAll().then(function (n) {
        S.msg = n + "개 파일을 저장소에 반영했습니다. 사이트에는 1~2분 뒤에 나타납니다."; route();
      }).catch(function (e) {
        S.msg = "저장하지 못했습니다: " + e.message + (e.status === 409 || e.status === 422 ? " — 다른 곳에서 먼저 수정된 것 같습니다. 백업을 내려받고 새로고침하세요." : "");
        route();
      });
    });
  }
  function targetName(id) {
    var t = items("targets").filter(function (x) { return x.id === id; })[0];
    return t ? t.name : (id || "—");
  }

  /* ---------- 현황판 ---------- */
  function viewHome() {
    var T = items("targets"), R = items("reviews"), C = items("cases");
    var by = function (arr, k) { var o = {}; arr.forEach(function (x) { o[x[k]] = (o[x[k]] || 0) + 1; }); return o; };
    var ts = by(T, "status"), soon = today(14);
    var todo = [];
    T.forEach(function (t) {
      if (t.status === "공개" && gateFail("targets", t).length) todo.push(["공개 기준 미달", t.name, "#targets/" + t.id]);
      if (t.status === "공개" && t.next_check && t.next_check <= soon) todo.push(["재점검 " + t.next_check, t.name, "#targets/" + t.id]);
      if (t.verdict && t.verdict !== "판정 전" && (t.notice || {}).state === "미통보") todo.push(["당사자 통보 필요", t.name, "#targets/" + t.id]);
      if (["접수", "초안"].indexOf(t.status) >= 0) todo.push(["작성 중 · " + t.status, t.name, "#targets/" + t.id]);
    });
    C.forEach(function (c) { if (c.stage !== "회신 완료") todo.push(["회신 기한 " + (c.due || "미정"), c.id + " · " + c.type, "#cases/" + c.id]); });
    if (!get(S.raw.site || {}, "CONTACT_EMAIL")) todo.unshift(["설정 필요", "문의·접수 메일 주소가 비어 있습니다", "#site"]);
    var tile = function (n, l, s) { return '<div class="tile"><b>' + n + "</b><span>" + l + "</span>" + (s ? "<small>" + s + "</small>" : "") + "</div>"; };
    var html = "<h1>현황판</h1><div class=\"tiles\">" +
      tile(ts["공개"] || 0, "공개 중인 대상", "전체 " + T.length) +
      tile((ts["후보"] || 0) + (ts["접수"] || 0) + (ts["초안"] || 0), "준비 중인 대상", "후보 " + (ts["후보"] || 0) + " · 접수 " + (ts["접수"] || 0) + " · 초안 " + (ts["초안"] || 0)) +
      tile(R.filter(function (r) { return r.status === "공개"; }).length, "공개 후기", "본문 확인 " + R.filter(function (r) { return r.status === "공개" && r.read_level === "본문 확인"; }).length) +
      tile(C.filter(function (c) { return c.stage !== "회신 완료"; }).length, "처리 중인 접수", "전체 " + C.length) + "</div>" +
      '<div class="cols"><section class="panel"><h2>오늘 할 일</h2>' +
      (todo.length ? "<ul class=\"todo\">" + todo.slice(0, 30).map(function (t) {
        return '<li><span class="tag">' + esc(t[0]) + '</span><a href="' + t[2] + '">' + esc(t[1]) + "</a></li>"; }).join("") + "</ul>"
        : '<p class="muted">지금 처리할 일이 없습니다.</p>') + "</section>" +
      '<section class="panel"><h2>최근 반영 기록</h2><div id="commits"><p class="muted">불러오는 중…</p></div></section></div>' +
      '<section class="panel"><h2>운영 원칙</h2><ul class="rules"><li>확인한 것만 적고, 모르는 것은 ‘미확인’으로 남깁니다.</li>' +
      "<li>판정은 당사자에게 알리고 답변 기회를 준 뒤에만 공개합니다.</li><li>후기는 원문을 옮기지 않고 요약과 링크만 싣습니다.</li>" +
      "<li>대가를 받고 내용을 바꾸지 않습니다. 광고·제휴는 따로 표시합니다.</li></ul></section>";
    mount("home", html);
    loadCommits().then(function (cs) {
      var el = $("#commits"); if (!el) return;
      el.innerHTML = cs.length ? "<ul class=\"todo\">" + cs.map(function (c) {
        return '<li><span class="tag">' + esc(c.date.slice(0, 10)) + '</span><a href="' + esc(c.url) + '" target="_blank" rel="noopener">' + esc(c.msg) + "</a></li>"; }).join("") + "</ul>"
        : '<p class="muted">기록을 불러오지 못했습니다.</p>';
    });
  }

  /* ---------- 목록 ---------- */
  function viewList(name) {
    var sc = SCHEMA[name], list = items(name);
    var q = S.q.toLowerCase();
    var rows = list.filter(function (it) {
      if (S.f && it[sc.statusKey] !== S.f) return false;
      return !q || JSON.stringify(it).toLowerCase().indexOf(q) >= 0;
    });
    var cell = function (it, k) {
      var v = it[k];
      if (k === "target_id") v = targetName(v);
      if (k === sc.statusKey) return '<span class="st st-' + esc(String(v).replace(/[^가-힣a-zA-Z]/g, "")) + '">' + esc(v) + "</span>";
      if (k === "url" && v) return '<span class="muted">' + esc(String(v).replace(/^https?:\/\//, "").slice(0, 34)) + "</span>";
      return esc(v == null ? "" : String(v).slice(0, 60));
    };
    var html = "<h1>" + sc.label + ' <small class="muted">' + rows.length + " / " + list.length + "</small></h1>" +
      (sc.warn ? '<p class="banner warn">' + esc(sc.warn) + "</p>" : "") +
      '<div class="bar"><input id="q" type="search" placeholder="검색" value="' + esc(S.q) + '">' +
      '<select id="f"><option value="">전체 ' + (name === "cases" ? "단계" : name === "services" ? "유형" : "상태") + "</option>" +
      sc.statuses.map(function (s) { return "<option" + (S.f === s ? " selected" : "") + ">" + esc(s) + "</option>"; }).join("") + "</select>" +
      '<span class="grow"></span><button id="csv" class="btn">CSV 내려받기</button><a class="btn pri" href="#' + name + '/new">+ 새 ' + sc.one + "</a></div>" +
      '<div class="tbl-wrap"><table class="tbl"><thead><tr>' + sc.cols.map(function (c) { return "<th>" + c[1] + "</th>"; }).join("") +
      (name === "targets" || name === "reviews" ? "<th>공개 기준</th>" : "") + "</tr></thead><tbody>" +
      (rows.length ? rows.map(function (it) {
        var g = (name === "targets" || name === "reviews") ? gateFail(name, it).length : -1;
        return '<tr data-id="' + esc(it.id) + '">' + sc.cols.map(function (c) { return "<td>" + cell(it, c[0]) + "</td>"; }).join("") +
          (g >= 0 ? "<td>" + (g ? '<span class="st st-warn">' + g + "개 미달</span>" : '<span class="st st-ok">충족</span>') + "</td>" : "") + "</tr>";
      }).join("") : '<tr><td colspan="9" class="muted">항목이 없습니다.</td></tr>') + "</tbody></table></div>";
    mount(name, html);
    $("#q").addEventListener("input", function (e) { S.q = e.target.value; var p = e.target.selectionStart; viewList(name); var n = $("#q"); n.focus(); n.setSelectionRange(p, p); });
    $("#f").addEventListener("change", function (e) { S.f = e.target.value; viewList(name); });
    $$(".tbl tbody tr[data-id]").forEach(function (tr) {
      tr.addEventListener("click", function () { location.hash = "#" + name + "/" + encodeURIComponent(tr.dataset.id); });
    });
    $("#csv").addEventListener("click", function () {
      var keys = sc.cols.map(function (c) { return c[0]; }).concat(["url", "summary"]).filter(function (v, i, a) { return a.indexOf(v) === i; });
      var csv = "﻿" + keys.join(",") + "\n" + rows.map(function (it) {
        return keys.map(function (k) { var v = it[k]; if (Array.isArray(v)) v = v.join("|"); return '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"'; }).join(",");
      }).join("\n");
      dl(name + "-" + today() + ".csv", csv, "text/csv");
    });
  }
  function dl(fname, text, type) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: type || "application/json" }));
    a.download = fname; document.body.appendChild(a); a.click(); a.remove();
  }

  /* ---------- 편집 ---------- */
  function fieldHtml(f, it) {
    if (f.sec) return '<h3 class="fsec">' + esc(f.sec) + "</h3>";
    var v = get(it, f.k), id = "f-" + f.k.replace(/\./g, "_"), inner;
    var lab = '<label for="' + id + '">' + esc(f.label) + (f.req ? ' <i class="req">필수</i>' : "") + "</label>";
    if (f.type === "select") {
      var opts = f.opts.slice(); if (v && opts.indexOf(v) < 0) opts.unshift(v);
      inner = '<select id="' + id + '" data-k="' + f.k + '">' + opts.map(function (o) { return "<option" + (o === v ? " selected" : "") + ">" + esc(o) + "</option>"; }).join("") + "</select>";
    } else if (f.type === "target") {
      inner = '<select id="' + id + '" data-k="' + f.k + '"><option value="">— 선택 —</option>' + items("targets").map(function (t) {
        return '<option value="' + esc(t.id) + '"' + (t.id === v ? " selected" : "") + ">" + esc(t.name) + "</option>"; }).join("") + "</select>";
    } else if (f.type === "area") {
      inner = '<textarea id="' + id + '" data-k="' + f.k + '" rows="' + (f.rows || 3) + '">' + esc(v) + "</textarea>";
    } else if (f.type === "lines") {
      inner = '<textarea id="' + id + '" data-k="' + f.k + '" data-t="lines" rows="' + (f.rows || 4) + '">' + esc((v || []).join("\n")) + "</textarea>";
    } else if (f.type === "tags") {
      inner = '<input id="' + id + '" data-k="' + f.k + '" data-t="tags" value="' + esc((v || []).join(", ")) + '" placeholder="' + esc(f.ph || "") + '">';
    } else if (f.type === "check") {
      return '<div class="fld chk"><label><input type="checkbox" id="' + id + '" data-k="' + f.k + '" data-t="check"' + (v ? " checked" : "") + "> " + esc(f.label) + "</label>" +
        (f.help ? '<p class="help">' + esc(f.help) + "</p>" : "") + "</div>";
    } else if (f.type === "rows") {
      var rows = (v || []).concat([{}]);
      inner = '<div class="rows" data-k="' + f.k + '" data-t="rows">' + rows.map(function (r) {
        return '<div class="row">' + f.cols.map(function (c) {
          return '<input data-c="' + c[0] + '" style="flex:' + c[2] + '" placeholder="' + esc(c[1]) + '" value="' + esc(r[c[0]]) + '">'; }).join("") +
          '<button type="button" class="x" title="이 줄 지우기">×</button></div>'; }).join("") +
        '<button type="button" class="btn sm add">+ 줄 추가</button></div>';
      return '<div class="fld wide">' + lab + inner + (f.help ? '<p class="help">' + esc(f.help) + "</p>" : "") + "</div>";
    } else {
      inner = '<input id="' + id + '" data-k="' + f.k + '" type="' + (f.type === "date" ? "date" : "text") + '" value="' + esc(v) + '" placeholder="' + esc(f.ph || "") + '">';
    }
    return '<div class="fld' + (f.type === "area" || f.type === "lines" ? " wide" : "") + '">' + lab + inner + (f.help ? '<p class="help">' + esc(f.help) + "</p>" : "") + "</div>";
  }
  function readForm(form, fields, base) {
    var it = JSON.parse(JSON.stringify(base));
    fields.forEach(function (f) {
      if (f.sec) return;
      var el = form.querySelector('[data-k="' + f.k + '"]'); if (!el) return;
      var t = el.dataset.t, v;
      if (t === "check") v = el.checked;
      else if (t === "lines") v = el.value.split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
      else if (t === "tags") v = el.value.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      else if (t === "rows") {
        v = $$(".row", el).map(function (row) {
          var o = {}; $$("input", row).forEach(function (i) { o[i.dataset.c] = i.value.trim(); }); return o;
        }).filter(function (o) { return Object.keys(o).some(function (k) { return o[k]; }); });
      } else v = el.value.trim();
      set(it, f.k, v);
    });
    return it;
  }
  function gateHtml(name, it) {
    var g = gate(name, it); if (!g.length) return "";
    return '<section class="panel gate"><h2>공개 기준</h2><ul>' + g.map(function (x) {
      return '<li class="' + (x.pass ? "pass" : "fail") + '">' + (x.pass ? "✓" : "□") + " " + esc(x.label) + "</li>"; }).join("") +
      "</ul><p class=\"help\">상태를 ‘공개’로 두려면 모든 줄이 ✓여야 합니다.</p></section>";
  }
  function viewEdit(name, id) {
    var sc = SCHEMA[name], list = items(name), isNew = id === "new";
    var orig = isNew ? sc.blank() : list.filter(function (x) { return String(x.id) === id; })[0];
    if (!orig) { location.hash = "#" + name; return; }
    var html = '<p class="crumb"><a href="#' + name + '">← ' + sc.label + "</a></p><h1>" + (isNew ? "새 " + sc.one : esc(orig.name || orig.title || orig.id)) + "</h1>" +
      (sc.warn ? '<p class="banner warn">' + esc(sc.warn) + "</p>" : "") +
      '<div class="edit"><form id="ed" class="panel form" autocomplete="off">' + sc.fields.map(function (f) { return fieldHtml(f, orig); }).join("") +
      '<div class="actions"><button type="submit" class="btn pri">변경 담기</button><a class="btn" href="#' + name + '">취소</a>' +
      (isNew ? "" : '<span class="grow"></span><button type="button" id="del" class="btn danger">삭제</button>') + "</div>" +
      '<p class="help">‘변경 담기’는 이 화면에만 담아 둡니다. 위쪽 [사이트에 반영]을 눌러야 실제 사이트에 적용됩니다.</p></form>' +
      '<div class="aside" id="gate">' + gateHtml(name, orig) +
      (name === "targets" && !isNew ? '<section class="panel"><h2>연결된 후기</h2><p class="muted">' +
        items("reviews").filter(function (r) { return r.target_id === orig.id; }).length + '건</p><a class="btn sm" href="#reviews">후기 목록</a> ' +
        (orig.status === "공개" ? '<a class="btn sm" href="/fact/' + esc(orig.id) + '/" target="_blank" rel="noopener">공개 페이지 보기</a>' : "") + "</section>" : "") +
      "</div></div>";
    mount(name, html);
    var form = $("#ed");
    var refreshGate = function () { var cur = readForm(form, sc.fields, orig); var g = $("#gate .gate"); if (g) g.outerHTML = gateHtml(name, cur); };
    form.addEventListener("input", refreshGate); form.addEventListener("change", refreshGate);
    form.addEventListener("click", function (e) {
      var t = e.target, wrap = t.closest ? t.closest(".rows") : null;
      if (!wrap) return;
      var f = sc.fields.filter(function (x) { return x.k === wrap.dataset.k; })[0];
      var addRow = function () {
        var div = document.createElement("div"); div.className = "row";
        div.innerHTML = f.cols.map(function (c) { return '<input data-c="' + c[0] + '" style="flex:' + c[2] + '" placeholder="' + esc(c[1]) + '">'; }).join("") +
          '<button type="button" class="x" title="이 줄 지우기">×</button>';
        wrap.insertBefore(div, wrap.querySelector(".add"));
      };
      if (t.classList.contains("x")) { t.closest(".row").remove(); if (!$$(".row", wrap).length) addRow(); refreshGate(); }
      else if (t.classList.contains("add")) addRow();
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var it = readForm(form, sc.fields, orig), miss = sc.fields.filter(function (f) { return f.req && !get(it, f.k); });
      if (miss.length) { alertBox("필수 항목을 채워 주세요: " + miss.map(function (f) { return f.label; }).join(", ")); return; }
      if (name === "targets" && !/^[a-z0-9][a-z0-9-]*$/.test(it.id)) { alertBox("주소용 ID는 영문 소문자·숫자·하이픈만 쓸 수 있습니다."); return; }
      if (list.some(function (x) { return x !== orig && String(x.id) === String(it.id); })) { alertBox("같은 ID가 이미 있습니다."); return; }
      if (it.status === "공개") {
        var fails = gateFail(name, it);
        if (fails.length) { alertBox("공개 기준을 채우지 못해 ‘공개’로 둘 수 없습니다:\n· " + fails.map(function (g) { return g.label; }).join("\n· ") + "\n\n상태를 ‘초안’으로 바꾸거나 빠진 내용을 채워 주세요."); return; }
      }
      if (isNew) list.push(it); else list[list.indexOf(orig)] = it;
      S.dirty[name] = true; S.msg = "변경을 담았습니다. [사이트에 반영]을 누르면 적용됩니다."; location.hash = "#" + name;
    });
    var del = $("#del");
    if (del) del.addEventListener("click", function () {
      if (del.dataset.sure !== "1") { del.dataset.sure = "1"; del.textContent = "정말 삭제 — 한 번 더 누르기"; return; }
      if (name === "targets" && items("reviews").some(function (r) { return r.target_id === orig.id; })) { alertBox("연결된 후기가 있어 삭제할 수 없습니다. 상태를 ‘보류’나 ‘반려’로 바꾸세요."); return; }
      list.splice(list.indexOf(orig), 1); S.dirty[name] = true; location.hash = "#" + name;
    });
  }
  function alertBox(text) {
    var old = $(".alert"); if (old) old.remove();
    var d = document.createElement("div"); d.className = "alert"; d.setAttribute("role", "alert");
    d.innerHTML = "<pre>" + esc(text) + '</pre><button class="btn sm">닫기</button>';
    document.body.appendChild(d); d.querySelector("button").addEventListener("click", function () { d.remove(); });
  }

  /* ---------- 사이트 설정 ---------- */
  function viewSite() {
    var site = S.raw.site || {};
    mount("site", "<h1>사이트 설정</h1>" +
      '<form id="ed" class="panel form" autocomplete="off">' + SITE_FIELDS.map(function (f) { return fieldHtml(f, site); }).join("") +
      '<div class="actions"><button type="submit" class="btn pri">변경 담기</button></div>' +
      '<p class="help">비워 둔 항목은 사이트에서 ‘준비 중’으로 표시됩니다. 메일 주소를 넣으면 제보·이의제기 버튼이 바로 열립니다.</p></form>');
    $("#ed").addEventListener("submit", function (e) {
      e.preventDefault();
      var next = readForm(e.target, SITE_FIELDS, site);
      if (next.CONTACT_EMAIL && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(next.CONTACT_EMAIL)) { alertBox("메일 주소 형식을 확인해 주세요."); return; }
      S.raw.site = next; S.dirty.site = true; S.msg = "설정을 담았습니다. [사이트에 반영]을 누르면 적용됩니다."; route();
    });
  }

  /* ---------- 연결·백업 ---------- */
  function viewConnect() {
    mount("connect", "<h1>연결·백업</h1>" +
      '<section class="panel"><h2>GitHub 연결</h2><p>' + (S.token ? "토큰이 이 브라우저에 저장돼 있습니다. 고친 내용을 사이트에 반영할 수 있습니다."
        : "지금은 읽기 전용입니다. 아래 순서로 토큰을 만들어 붙여 넣으면 이 화면에서 바로 사이트를 고칠 수 있습니다.") + "</p>" +
      '<ol class="steps"><li>github.com에 로그인 → 오른쪽 위 프로필 → <b>Settings</b> → 맨 아래 <b>Developer settings</b></li>' +
      "<li><b>Personal access tokens → Fine-grained tokens → Generate new token</b></li>" +
      "<li>Repository access: <b>Only select repositories</b> → <b>" + esc(REPO) + "</b> 하나만 선택</li>" +
      "<li>Permissions → Repository permissions → <b>Contents: Read and write</b> (나머지는 그대로)</li>" +
      "<li>만료일을 정하고 Generate → 나온 토큰을 복사해 아래 칸에 붙여 넣기</li></ol>" +
      '<form id="tk" class="bar"><input id="tk-in" type="password" placeholder="github_pat_…" autocomplete="off" style="flex:1">' +
      '<button class="btn pri" type="submit">연결</button>' + (S.token ? '<button class="btn danger" type="button" id="tk-del">연결 해제</button>' : "") + "</form>" +
      '<p class="help">토큰은 이 컴퓨터의 이 브라우저에만 보관되고 다른 곳으로 보내지 않습니다. 공용 PC에서는 연결하지 마세요. 토큰이 유출되면 GitHub에서 바로 삭제할 수 있습니다.</p></section>' +
      '<section class="panel"><h2>백업</h2><p>지금 화면에 담긴 전체 데이터를 파일 하나로 내려받습니다. 주 1회 정도 받아 두면 좋습니다.</p>' +
      '<button id="bk" class="btn">전체 백업 내려받기 (JSON)</button></section>' +
      '<section class="panel"><h2>알아 둘 점</h2><ul class="rules"><li>데이터 원본은 GitHub 저장소 <b>' + esc(REPO) + "</b>의 data 폴더입니다. 저장소가 공개 상태이면 초안과 내부 메모도 GitHub에서 볼 수 있습니다. 비공개로 바꾸려면 저장소 Settings → Change visibility를 쓰세요(사이트 배포에는 영향이 없습니다).</li>" +
      "<li>반영 버튼을 누를 때마다 변경 기록이 남습니다. 잘못 고쳤다면 GitHub의 커밋 기록에서 되돌릴 수 있습니다.</li>" +
      "<li>방문자가 보내는 제보·이의제기는 메일이나 접수 양식으로 받습니다. 받은 건은 ‘제보·이의제기’ 메뉴에 경과만 기록합니다.</li></ul></section>");
    $("#tk").addEventListener("submit", function (e) {
      e.preventDefault();
      var v = $("#tk-in").value.trim(); if (!v) return;
      var prev = S.token; S.token = v;
      gh("").then(function (j) {
        if (!(j.permissions && j.permissions.push)) throw new Error("이 토큰에는 저장소 쓰기 권한이 없습니다. Contents: Read and write 를 확인하세요.");
        try { localStorage.setItem(TKEY, v); } catch (er) {}
        return loadAll();
      }).then(function () { S.msg = "연결됐습니다. 이제 [사이트에 반영]을 쓸 수 있습니다."; route(); })
        .catch(function (er) { S.token = prev; alertBox("연결하지 못했습니다: " + er.message); });
    });
    var d = $("#tk-del");
    if (d) d.addEventListener("click", function () { S.token = ""; try { localStorage.removeItem(TKEY); } catch (er) {} S.msg = "연결을 해제했습니다."; route(); });
    $("#bk").addEventListener("click", function () { dl("factanddo-backup-" + today() + ".json", JSON.stringify(S.raw, null, 2)); });
  }

  /* ---------- 라우터 ---------- */
  function route() {
    var h = (location.hash || "#home").slice(1).split("/"), v = h[0], id = h[1] ? decodeURIComponent(h[1]) : "";
    if (v !== route.last) { S.q = ""; S.f = ""; route.last = v; }
    if (SCHEMA[v]) { if (id) viewEdit(v, id); else viewList(v); }
    else if (v === "site") viewSite();
    else if (v === "connect") viewConnect();
    else viewHome();
    S.msg = "";
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  window.addEventListener("beforeunload", function (e) { if (dirtyCount()) { e.preventDefault(); e.returnValue = ""; } });
  window.FD_ADMIN_TEST = { gate: gate, S: S, SCHEMA: SCHEMA };
  loadAll().then(route).catch(function (e) {
    $("#app").innerHTML = '<p class="boot">데이터를 불러오지 못했습니다: ' + esc(e.message) + "</p>";
  });
})();
