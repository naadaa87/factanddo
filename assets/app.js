/* ============================================================
   FACT&DO (팩트앤두) — app.js
   베타 원칙: 모든 사용자 기록은 이 브라우저(localStorage)에만 저장되며,
   화면에 그 사실을 항상 고지합니다. 허위 수치·가짜 표본을 만들지 않습니다.
   저장 키: fd2:saved / fd2:review:draft / fd2:review:queue / fd2:groups
   ============================================================ */
(function () {
  "use strict";
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var store = {
    get: function (k, fb) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : fb; } catch (e) { return fb; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } },
    del: function (k) { try { localStorage.removeItem(k); } catch (e) {} }
  };
  var fmtD = function (ts) { var d = new Date(ts); return (d.getMonth() + 1) + "/" + d.getDate(); };
  var b64e = function (str) {
    return btoa(unescape(encodeURIComponent(str))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  };
  var b64d = function (s) {
    s = s.replace(/-/g, "+").replace(/_/g, "/");
    while (s.length % 4) s += "=";
    return decodeURIComponent(escape(atob(s)));
  };
  var download = function (name, obj) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" }));
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
  };

  /* ---------- 공통: 모바일 메뉴 · 연도 · 스크롤 리빌 ---------- */
  var tg = $("#nav-toggle"), nav = $("#site-nav");
  if (tg && nav) tg.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    tg.setAttribute("aria-expanded", open ? "true" : "false");
  });
  var yr = $("#year"); if (yr) yr.textContent = new Date().getFullYear();
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    $$(".card, .sec-head, .split-copy, .split-img, .loop-step").forEach(function (el) {
      el.classList.add("reveal"); io.observe(el);
    });
  }

  /* ============================================================
     탐색 페이지
     ============================================================ */
  var exList = $("#ex-list");
  if (exList && window.FD_DATA) {
    var items = window.FD_DATA.items || [];
    var LKEY = "fd2:saved";
    var state = { q: "", layer: "전체", cat: "전체" };
    var layerCls = { "교육 판매": "lt-edu", "실행 모임": "lt-do", "수익 실행": "lt-earn" };

    var uniq = function (arr) { return arr.filter(function (v, i) { return arr.indexOf(v) === i; }); };
    var layers = ["전체"].concat(uniq(items.map(function (i) { return i.layer; })));
    var cats = ["전체"].concat(uniq([].concat.apply([], items.map(function (i) { return i.category || []; }))));

    var chips = function (host, list, key) {
      host.innerHTML = list.map(function (v) {
        return '<button type="button" class="chip' + (state[key] === v ? " on" : "") + '" data-v="' + esc(v) + '">' + esc(v) + "</button>";
      }).join("");
      $$(".chip", host).forEach(function (b) {
        b.addEventListener("click", function () { state[key] = b.dataset.v; render(); });
      });
    };

    var savedIds = function () { return store.get(LKEY, []); };
    var renderSaved = function () {
      var ids = savedIds();
      $("#saved-count").textContent = ids.length;
      var ul = $("#saved-list");
      ul.innerHTML = ids.map(function (id) {
        var it = items.filter(function (x) { return x.id === id; })[0];
        return it ? "<li><span>" + esc(it.name) + '</span><button type="button" data-id="' + esc(id) + '" aria-label="비교함에서 제거">×</button></li>' : "";
      }).join("") || '<li><span class="dim">담긴 항목이 없습니다</span></li>';
      $$("button", ul).forEach(function (b) {
        b.addEventListener("click", function () {
          store.set(LKEY, savedIds().filter(function (x) { return x !== b.dataset.id; }));
          renderSaved(); render();
        });
      });
    };

    var card = function (it) {
      var saved = savedIds().indexOf(it.id) >= 0;
      var tags = (it.category || []).map(function (c) { return "<span>" + esc(c) + "</span>"; }).join("");
      var link = it.url ? '<a class="btn-mini" href="' + esc(it.url) + '" target="_blank" rel="noopener">공식 사이트</a>'
                        : '<span class="state-tag">공식 URL 확인 필요</span>';
      return '<article class="card ex-card">' +
        '<div class="ex-top"><span class="layer-tag ' + (layerCls[it.layer] || "") + '">' + esc(it.layer) + "</span>" +
        '<span class="mono dim">확인 ' + esc(it.checked || "") + "</span></div>" +
        "<h3>" + esc(it.name) + "</h3>" +
        '<p class="ex-desc">' + esc(it.desc) + "</p>" +
        '<div class="ex-tags">' + tags + "</div>" +
        '<div class="ex-foot"><span class="state-tag">' + esc(it.review_state || "리뷰 표본 없음") + "</span><span>" + link +
        '<button type="button" class="btn-mini save-btn' + (saved ? " saved" : "") + '" data-id="' + esc(it.id) + '">' +
        (saved ? "비교함에 담김 ✓" : "비교함 담기") + "</button></span></div></article>";
    };

    var render = function () {
      var q = state.q.trim().toLowerCase();
      var out = items.filter(function (it) {
        if (state.layer !== "전체" && it.layer !== state.layer) return false;
        if (state.cat !== "전체" && (it.category || []).indexOf(state.cat) < 0) return false;
        if (q && (it.name + " " + it.desc).toLowerCase().indexOf(q) < 0) return false;
        return true;
      });
      exList.innerHTML = out.map(card).join("");
      $("#ex-count").textContent = out.length;
      $("#ex-empty").hidden = out.length > 0;
      chips($("#ex-layers"), layers, "layer");
      chips($("#ex-cats"), cats, "cat");
      $$(".save-btn", exList).forEach(function (b) {
        b.addEventListener("click", function () {
          var ids = savedIds(), i = ids.indexOf(b.dataset.id);
          if (i >= 0) ids.splice(i, 1); else ids.push(b.dataset.id);
          store.set(LKEY, ids); renderSaved(); render();
        });
      });
    };

    $("#ex-search").addEventListener("input", function (e) { state.q = e.target.value; render(); });
    $("#saved-toggle").addEventListener("click", function () {
      var p = $("#saved-panel"); p.hidden = !p.hidden;
    });
    renderSaved(); render();
  }

  /* ============================================================
     팩트리뷰 — 목록(내 브라우저)
     ============================================================ */
  var rvList = $("#rv-local-list");
  if (rvList) {
    var QKEY = "fd2:review:queue";
    var renderQ = function () {
      var q = store.get(QKEY, []);
      $("#rv-local-empty").hidden = q.length > 0;
      rvList.innerHTML = q.slice().reverse().map(function (r) {
        return '<article class="rv-item"><h3>' + esc(r.course || "(과정명 없음)") + "</h3>" +
          '<p class="rv-sum">' + esc(r.summary || "") + "</p>" +
          '<div class="rv-row"><span class="mono dim">저장 ' + fmtD(r.ts) + ' · 이 브라우저에만 저장됨</span>' +
          '<span><button type="button" class="btn-mini" data-act="dl" data-id="' + r.id + '">JSON 내려받기</button> ' +
          '<button type="button" class="btn-mini" data-act="rm" data-id="' + r.id + '">삭제</button></span></div></article>';
      }).join("");
      $$("button", rvList).forEach(function (b) {
        b.addEventListener("click", function () {
          var q2 = store.get(QKEY, []);
          var it = q2.filter(function (x) { return String(x.id) === b.dataset.id; })[0];
          if (b.dataset.act === "dl" && it) download("factanddo-review-" + it.id + ".json", it);
          if (b.dataset.act === "rm" && it && confirm("이 리뷰 기록을 삭제할까요? 되돌릴 수 없습니다.")) {
            store.set(QKEY, q2.filter(function (x) { return String(x.id) !== b.dataset.id; }));
            renderQ();
          }
        });
      });
    };
    renderQ();
  }

  /* ============================================================
     팩트리뷰 — 작성 폼
     ============================================================ */
  var rf = $("#review-form");
  if (rf) {
    var DKEY = "fd2:review:draft", QKEY2 = "fd2:review:queue";
    var info = $("#rv-draft-info");

    var collect = function () {
      var o = { rates: {}, ev: [], rel: [] };
      $$("input, select, textarea", rf).forEach(function (el) {
        if (!el.name) return;
        if (el.type === "checkbox") {
          if (el.name === "ev") { if (el.checked) o.ev.push(el.value); }
          else if (el.name === "rel") { if (el.checked) o.rel.push(el.value); }
          else o[el.name] = el.checked;
        } else if (el.type === "radio") {
          if (el.checked) o.rates[el.name.replace("rate-", "")] = el.value;
        } else o[el.name] = el.value;
      });
      return o;
    };
    var restore = function () {
      var o = store.get(DKEY, null); if (!o) return;
      $$("input, select, textarea", rf).forEach(function (el) {
        if (!el.name) return;
        if (el.type === "checkbox") {
          if (el.name === "ev") el.checked = (o.ev || []).indexOf(el.value) >= 0;
          else if (el.name === "rel") el.checked = (o.rel || []).indexOf(el.value) >= 0;
          else el.checked = !!o[el.name];
        } else if (el.type === "radio") {
          el.checked = (o.rates || {})[el.name.replace("rate-", "")] === el.value;
        } else if (o[el.name] != null) el.value = o[el.name];
      });
      if (o._ts) info.textContent = "임시저장 복원됨 · " + new Date(o._ts).toLocaleString("ko-KR");
    };
    var summary = function (o) {
      var p = [];
      p.push(o.ev && o.ev.length ? "증빙 제출 가능: " + o.ev.join("·") : "미인증(E0)");
      if (o.version) p.push(o.version);
      if (o.hours || o.period) p.push([o.hours ? "주 " + o.hours.replace("시간", "") + "시간대" : "", o.period ? o.period + " 실행" : ""].filter(Boolean).join(", "));
      if (o.extracost) p.push("추가비용 " + o.extracost);
      if (o.outcome_type) p.push("결과: " + o.outcome_type);
      if (o.rev) p.push("매출 구간 " + o.rev + (o.rev_period ? " (" + o.rev_period + ")" : ""));
      p.push(o.rel && o.rel.length ? "관계: " + o.rel.join(", ") : (o.rel_none ? "리뷰어는 해당 과정과 경제적 관계 없음" : "관계 공개 미선택"));
      return p.join(" · ");
    };
    var save = function () {
      var o = collect(); o._ts = Date.now();
      store.set(DKEY, o);
      info.textContent = "자동 임시저장됨 · " + new Date().toLocaleTimeString("ko-KR") + " (이 브라우저)";
      $("#rv-preview").textContent = summary(o);
    };
    rf.addEventListener("input", save);
    rf.addEventListener("change", function (e) {
      // '해당 없음'과 개별 관계는 동시 선택 불가
      var none = $("#rel-none");
      if (e.target === none && none.checked) $$('input[name="rel"]', rf).forEach(function (c) { c.checked = false; });
      if (e.target.name === "rel" && e.target.checked && none) none.checked = false;
      save();
    });
    $("#rv-export").addEventListener("click", function () { download("factanddo-review-draft.json", collect()); });
    $("#rv-clear").addEventListener("click", function () {
      if (!confirm("작성 중인 초안을 지울까요?")) return;
      store.del(DKEY); rf.reset(); save(); info.textContent = "초안을 지웠습니다.";
    });
    rf.addEventListener("submit", function (e) {
      e.preventDefault();
      var o = collect();
      if (!(o.rel && o.rel.length) && !o.rel_none) {
        alert("관계 공개는 필수입니다. 해당 관계가 없다면 ‘해당 사항 없음’을 선택해 주세요.");
        return;
      }
      o.id = Date.now(); o.ts = o.id; o.summary = summary(o);
      var q = store.get(QKEY2, []); q.push(o); store.set(QKEY2, q);
      store.del(DKEY);
      location.href = "/reviews/";
    });
    restore(); save();
  }

  /* ============================================================
     실행그룹 — 목록 · 개설 · 보드
     ============================================================ */
  var GKEY = "fd2:groups";
  var groups = function () { return store.get(GKEY, {}); };
  var saveGroups = function (g) { store.set(GKEY, g); };

  // ---- 목록 ----
  var grList = $("#gr-list");
  if (grList) {
    var g = groups(), arr = Object.keys(g).map(function (k) { return g[k]; })
      .sort(function (a, b) { return b.created - a.created; });
    $("#gr-empty").hidden = arr.length > 0;
    grList.innerHTML = arr.map(function (it) {
      return '<article class="card gr-card">' +
        '<div class="ex-top"><span class="j-tag t-coral">' + esc(it.gtype) + '</span>' +
        '<span class="mono dim">' + it.weeks + "주 · " + esc(it.size) + "</span></div>" +
        "<h3>" + esc(it.name) + "</h3>" +
        '<p class="ex-desc">' + esc(it.goal) + "</p>" +
        '<div class="ex-foot"><span class="state-tag">이 브라우저 · 기록 ' + (it.entries || []).length + "개</span>" +
        '<a class="btn btn-ghost" href="/groups/room/?id=' + esc(it.id) + '">보드 열기</a></div></article>';
    }).join("");
    var imBtn = $("#gr-import-btn");
    if (imBtn) imBtn.addEventListener("click", function () {
      var v = ($("#gr-import").value || "").trim();
      var m = v.match(/#s=([A-Za-z0-9_-]+)/);
      if (m) location.href = "/groups/room/#s=" + m[1];
      else alert("링크에서 스냅샷 코드(#s=…)를 찾지 못했습니다. 링크 전체를 붙여넣어 주세요.");
    });
  }

  // ---- 개설 ----
  var gf = $("#group-form");
  if (gf) gf.addEventListener("submit", function (e) {
    e.preventDefault();
    var f = new FormData(gf);
    var id = Date.now().toString(36);
    var g = groups();
    g[id] = {
      id: id, name: f.get("name"), gtype: f.get("gtype"), topic: f.get("topic") || "",
      weeks: parseInt(f.get("weeks"), 10) || 4, size: f.get("size"),
      goal: f.get("goal"), personal: f.get("personal") || "", cost: f.get("cost") || "",
      created: Date.now(), members: ["그룹장"], entries: [], outcomes: []
    };
    saveGroups(g);
    location.href = "/groups/room/?id=" + id;
  });

  // ---- 보드 ----
  var board = $("#gm-board");
  if (board) {
    var params = new URLSearchParams(location.search);
    var snapMatch = location.hash.match(/#s=([A-Za-z0-9_-]+)/);
    var readonly = false, G = null, gid = params.get("id");

    if (snapMatch) {
      try { G = JSON.parse(b64d(snapMatch[1])); readonly = true; } catch (e) { G = null; }
    } else if (gid) {
      G = groups()[gid] || null;
    }

    var TYPES = ["목표", "체크인", "산출물", "피드백", "회고"];
    var wk = 1;

    if (!G) {
      $("#gm-title").textContent = "그룹을 찾을 수 없습니다";
      $("#gm-meta").textContent = "링크가 잘못되었거나, 이 브라우저에 없는 그룹입니다. 그룹장이 보낸 스냅샷 링크로 다시 열어주세요.";
      board.innerHTML = '<div class="board-empty"><a class="btn btn-ghost" href="/groups/">그룹 목록으로</a></div>';
      $$("#gm-entry-form, #gm-outcome").forEach(function (f) { f.style.display = "none"; });
      $$("#gm-share, #gm-export, #gm-danger, #gm-member-btn").forEach(function (b) { if (b) b.style.display = "none"; });
    } else {
      G.entries = G.entries || []; G.outcomes = G.outcomes || []; G.members = G.members && G.members.length ? G.members : ["그룹장"];
      var curWeek = Math.min(G.weeks, Math.max(1, Math.floor((Date.now() - G.created) / 6048e5) + 1));
      wk = curWeek;

      var persist = function () { if (readonly) return; var g = groups(); g[G.id] = G; saveGroups(g); };

      var renderHead = function () {
        $("#gm-title").textContent = G.name;
        $("#gm-meta").textContent = [G.gtype, G.topic, G.weeks + "주 · " + (G.size || ""), "시작 " + new Date(G.created).toLocaleDateString("ko-KR")]
          .filter(Boolean).join("  ·  ");
        var done = G.entries.length, oc = G.outcomes.length;
        $("#gm-progress").innerHTML = '<div class="prog-bar"><i style="width:' + Math.round(curWeek / G.weeks * 100) + '%"></i></div>' +
          '<span class="mono dim">' + curWeek + "주차 · 기록 " + done + "개 · 결과로그 " + oc + "개</span>";
        if (readonly) { $("#gm-snapshot-note").hidden = false; $("#gm-adopt").hidden = false; $("#gm-danger").style.display = "none"; }
      };

      var renderMembers = function () {
        $("#gm-members").innerHTML = G.members.map(function (m, i) {
          return "<li><span>" + esc(m) + "</span>" + (readonly || G.members.length <= 1 ? "" :
            '<button type="button" data-i="' + i + '" aria-label="멤버 삭제">×</button>') + "</li>";
        }).join("");
        $$("#gm-members button").forEach(function (b) {
          b.addEventListener("click", function () { G.members.splice(+b.dataset.i, 1); persist(); renderMembers(); renderAuthors(); });
        });
        renderAuthors();
      };
      var renderAuthors = function () {
        var opts = G.members.map(function (m) { return "<option>" + esc(m) + "</option>"; }).join("");
        $("#gm-eauthor").innerHTML = opts; $("#gm-oauthor").innerHTML = opts;
      };

      var renderTabs = function () {
        var host = $("#gm-week-tabs");
        var html = "";
        for (var i = 1; i <= G.weeks; i++) {
          var cnt = G.entries.filter(function (e) { return e.w === i; }).length;
          html += '<button type="button" class="wtab' + (i === wk ? " on" : "") + '" data-w="' + i + '" role="tab" aria-selected="' + (i === wk) + '">' +
            i + "주" + (cnt ? '<span class="cnt">' + cnt + "</span>" : "") + "</button>";
        }
        host.innerHTML = html;
        $$(".wtab", host).forEach(function (b) {
          b.addEventListener("click", function () { wk = +b.dataset.w; renderTabs(); renderBoard(); });
        });
      };

      var renderBoard = function () {
        var list = G.entries.map(function (e, idx) { e._i = idx; return e; })
          .filter(function (e) { return e.w === wk; });
        if (!list.length) {
          board.innerHTML = '<div class="board-empty">이번 주 기록이 아직 없습니다. 월요일엔 ‘한 가지 핵심 목표’부터 남겨보세요.</div>';
          return;
        }
        board.innerHTML = TYPES.map(function (t) {
          var es = list.filter(function (e) { return e.type === t; });
          if (!es.length) return "";
          return '<div class="gm-day"><b class="e-tag e-' + t + '">' + t + "</b>" + es.map(function (e) {
            return '<div class="gm-entry"><span class="e-meta mono">' + esc(e.author) + " · " + fmtD(e.ts) + "</span><p>" + esc(e.text) + "</p>" +
              (readonly ? "" : '<button type="button" class="e-del" data-i="' + e._i + '" aria-label="기록 삭제">×</button>') + "</div>";
          }).join("") + "</div>";
        }).join("");
        $$(".e-del", board).forEach(function (b) {
          b.addEventListener("click", function () {
            if (!confirm("이 기록을 삭제할까요?")) return;
            G.entries.splice(+b.dataset.i, 1); persist(); renderTabs(); renderBoard(); renderHead();
          });
        });
      };

      var renderOutcomes = function () {
        $("#gm-olist").innerHTML = G.outcomes.map(function (o) {
          return '<li><span class="e-meta">' + esc(o.type) + " · " + esc(o.author) + " · " + fmtD(o.ts) + "</span>" + esc(o.text) + "</li>";
        }).join("");
      };

      var ef = $("#gm-entry-form");
      ef.addEventListener("submit", function (e) {
        e.preventDefault();
        if (readonly) return;
        var txt = $("#gm-etext").value.trim(); if (!txt) return;
        G.entries.push({ w: wk, type: $("#gm-etype").value, author: $("#gm-eauthor").value, text: txt, ts: Date.now() });
        $("#gm-etext").value = "";
        persist(); renderTabs(); renderBoard(); renderHead();
      });
      $("#gm-outcome").addEventListener("submit", function (e) {
        e.preventDefault();
        if (readonly) return;
        var txt = $("#gm-otext").value.trim(); if (!txt) return;
        G.outcomes.push({ type: $("#gm-otype").value, author: $("#gm-oauthor").value, text: txt, ts: Date.now() });
        $("#gm-otext").value = "";
        persist(); renderOutcomes(); renderHead();
      });
      $("#gm-member-btn").addEventListener("click", function () {
        if (readonly) return;
        var v = $("#gm-member-add").value.trim(); if (!v) return;
        if (G.members.indexOf(v) < 0) G.members.push(v);
        $("#gm-member-add").value = "";
        persist(); renderMembers();
      });
      $("#gm-share").addEventListener("click", function () {
        var snap = JSON.parse(JSON.stringify(G));
        var url = location.origin + "/groups/room/#s=" + b64e(JSON.stringify(snap));
        var done = function () { $("#gm-share").textContent = "복사됨 ✓ (읽기 전용 링크)"; setTimeout(function () { $("#gm-share").textContent = "스냅샷 링크 복사"; }, 2200); };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(done, function () { prompt("아래 링크를 복사하세요", url); });
        else prompt("아래 링크를 복사하세요", url);
      });
      $("#gm-export").addEventListener("click", function () { download("factanddo-group-" + G.id + ".json", G); });
      $("#gm-adopt").addEventListener("click", function () {
        var g = groups(); var nid = G.id && !g[G.id] ? G.id : Date.now().toString(36);
        G.id = nid; g[nid] = G; saveGroups(g);
        location.href = "/groups/room/?id=" + nid;
      });
      $("#gm-danger").addEventListener("click", function () {
        if (!confirm("그룹과 모든 기록을 삭제할까요? 되돌릴 수 없습니다.")) return;
        var g = groups(); delete g[G.id]; saveGroups(g);
        location.href = "/groups/";
      });
      if (readonly) {
        $$("#gm-entry-form input, #gm-entry-form select, #gm-entry-form textarea, #gm-entry-form button, #gm-outcome select, #gm-outcome textarea, #gm-outcome button, #gm-member-add, #gm-member-btn")
          .forEach(function (el) { el.disabled = true; });
      }
      renderHead(); renderMembers(); renderTabs(); renderBoard(); renderOutcomes();
    }
  }
})();
