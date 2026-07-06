#!/usr/bin/env python3
with open('/home/team/shared/backend/templates/index.html', 'r') as f:
    c = f.read()

# Part 1: Add purchase questions CSS
old_css = ".intent-rec-badge { display: inline-block; padding: 1px 7px; border-radius: 4px; font-size: 9px; font-weight: 700; background: var(--sage); color: #fff; margin-left: 6px; vertical-align: middle; }"
new_css = old_css + """

              /* Purchase questions */
              .pq-wrap { display: none; padding: 0; }
              .pq-wrap.active { display: block; }
              .pq-card { border-radius: var(--radius-sm); border: 1px solid var(--border-light); background: var(--bg-card); padding: 16px 18px; margin-bottom: 10px; }
              .pq-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; color: var(--text-muted); margin-bottom: 8px; }
              .pq-options { display: flex; gap: 8px; }
              .pq-opt { flex: 1; padding: 10px 12px; border-radius: var(--radius-xs); border: 1.5px solid var(--border-light); cursor: pointer; text-align: center; font-size: 13px; font-weight: 600; color: var(--text-secondary); transition: all 0.2s; }
              .pq-opt.pq-active { border-color: var(--terracotta); background: var(--terracotta-soft); color: var(--terracotta); }
              .pq-seg { display: flex; gap: 8px; margin-bottom: 14px; }
              .pq-seg-btn { flex: 1; padding: 12px 8px; border-radius: var(--radius-xs); border: 1.5px solid var(--border-light); cursor: pointer; text-align: center; font-size: 12px; font-weight: 600; color: var(--text-secondary); transition: all 0.2s; }
              .pq-seg-btn.pq-active { border-color: var(--terracotta); background: var(--terracotta-soft); color: var(--terracotta); }
              .pq-submit { display: block; width: 100%; padding: 14px; border-radius: var(--radius-sm); border: none; background: var(--terracotta); color: #fff; font-size: 16px; font-weight: 700; cursor: pointer; text-align: center; }"""
c = c.replace(old_css, new_css)

# Part 2: Replace submitWithIntent
# Find the exact submitWithIntent function
old_fn_start = '    /* ── Submit With Intent ── */\n    async function submitWithIntent(intent) {'
old_fn_end = '} catch (e) { alert("⚠️ " + e.message); goHome(); }\n    }'

# Extract exact function text
idx_start = c.find(old_fn_start)
idx_end = c.find(old_fn_end, idx_start) + len(old_fn_end)

old_fn = c[idx_start:idx_end]

new_fn = '''    /* ── Submit With Intent ── */
    function submitWithIntent(intent) {
      if (intent === "purchase") { showPurchaseQuestions(); }
      else { doSubmitIntent(intent); }
    }

    /* Purchase questions state */
    let _pqAnswers = { focus:"exact", scale:"composition", space:"existing", styling:"rich", budget:"design" };

    /* Show purchase questions form */
    function showPurchaseQuestions() {
      document.getElementById("loadingWrap").classList.remove("active");
      document.getElementById("resultsWrap").classList.remove("active");
      const html = '<div class="pq-wrap active">' +
        '<div class="pq-card"><div class="pq-label">Focus</div><div class="pq-options">' +
          '<div class="pq-opt pq-active" data-pq="focus_exact">Exact dezelfde look</div>' +
          '<div class="pq-opt" data-pq="focus_style">Zelfde stijl, andere uitvoering</div></div></div>' +
        '<div class="pq-card"><div class="pq-label">Schaal</div><div class="pq-options">' +
          '<div class="pq-opt" data-pq="scale_item">Alleen dit item</div>' +
          '<div class="pq-opt pq-active" data-pq="scale_composition">Complete compositie</div></div></div>' +
        '<div class="pq-card"><div class="pq-label">Ruimte</div><div class="pq-options">' +
          '<div class="pq-opt pq-active" data-pq="space_existing">Past in mijn interieur</div>' +
          '<div class="pq-opt" data-pq="space_new">Vrij nieuw ontwerp</div></div></div>' +
        '<div class="pq-card"><div class="pq-label">Styling</div><div class="pq-options">' +
          '<div class="pq-opt" data-pq="styling_minimal">Minimalistisch & strak</div>' +
          '<div class="pq-opt pq-active" data-pq="styling_rich">Rijk & sfeervol</div></div></div>' +
        '<div class="pq-card"><div class="pq-label">Budget</div><div class="pq-seg">' +
          '<div class="pq-seg-btn" data-pq="budget_budget">Budget: €10-€80</div>' +
          '<div class="pq-seg-btn pq-active" data-pq="budget_design">Design: €80-€500</div>' +
          '<div class="pq-seg-btn" data-pq="budget_luxe">Luxe: €500+</div></div></div>' +
        '<button class="pq-submit" id="pqSubmitBtn">Genereer advies</button></div>';
      document.getElementById("resultContent").innerHTML = html;
      document.querySelectorAll(".pq-opt").forEach(el => {
        el.addEventListener("click", function() {
          const k = this.dataset.pq.split("_")[0];
          const v = this.dataset.pq.split("_")[1];
          _pqAnswers[k] = v;
          document.querySelectorAll('[data-pq^="' + k + '_"]').forEach(x => x.classList.remove("pq-active"));
          this.classList.add("pq-active");
        });
      });
      document.querySelectorAll(".pq-seg-btn").forEach(el => {
        el.addEventListener("click", function() {
          _pqAnswers.budget = this.dataset.pq.split("_")[1];
          document.querySelectorAll(".pq-seg-btn").forEach(x => x.classList.remove("pq-active"));
          this.classList.add("pq-active");
        });
      });
      document.getElementById("pqSubmitBtn").addEventListener("click", function() { doSubmitIntent("purchase", _pqAnswers); });
    }

    /* Actual API call with optional user answers */
    async function doSubmitIntent(intent, userAnswers) {
      document.getElementById("loadingWrap").classList.add("active");
      document.getElementById("resultsWrap").classList.remove("active");
      try {
        const body = { image: imageBase64, mode: "inspiration", step: "advise", session_id: currentSessionId, user_intent: intent };
        if (userAnswers) body.user_answers = userAnswers;
        const resp = await fetch("/api/analyze", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        const result = await resp.json();
        if (result.error) throw new Error(result.error);
        const pResp = await fetch("/api/providers");
        providers = await pResp.json();
        document.getElementById("loadingWrap").classList.remove("active");
        document.getElementById("resultsWrap").classList.add("active");
        document.querySelector(".dash-footer").style.display = "none";
        showInspirationAdvice(result);
        addTryAnotherButton();
      } catch (e) { alert("⚠️ " + e.message); goHome(); }
    }'''

c = c[:idx_start] + new_fn + c[idx_end:]

with open('/home/team/shared/backend/templates/index.html', 'w') as f:
    f.write(c)
print("Frontend: OK")