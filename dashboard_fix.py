#!/usr/bin/env python3
"""Apply all approved dashboard visual improvements to index.html."""
import re

path = "/home/team/shared/backend/templates/index.html"
with open(path, "r") as f:
    html = f.read()

# 1. Add tagline under logo
old_logo = '<div class="logo-title-sm">HouseFix</div>'
new_logo = '<div style="display:flex;flex-direction:column;gap:2px">\n                  <div class="logo-title-sm">HouseFix</div>\n                  <div class="logo-sub-sm">Jouw slimme klus- en interieurmaatje</div>\n                </div>'
html = html.replace(old_logo, new_logo, 1)

# 2. Remove ::after underline from mode-active, add glow + lift
old_after = '.mode-btn.mode-active::after { content: ""; position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%); width: 40px; height: 3px; border-radius: 2px; background: var(--terracotta); }'
html = html.replace(old_after, '', 1)

# Update mode-active to have glow + lift
old_active = '.mode-btn.mode-active { border-color: var(--terracotta); background: var(--terracotta-soft); box-shadow: 0 0 0 1px var(--terracotta), 0 2px 8px rgba(196,98,74,0.1); color: var(--terracotta); position: relative; }'
new_active = '.mode-btn.mode-active { border-color: var(--terracotta); background: var(--terracotta-soft); box-shadow: 0 0 0 1px var(--terracotta), 0 4px 16px rgba(196,98,74,0.15); color: var(--terracotta); transform: translateY(-1px); }'
html = html.replace(old_active, new_active, 1)

# 3. Premium carousel cards
old_card = '.hc-card { flex: 0 0 260px; height: 280px; border-radius: 16px; scroll-snap-align: center; position: relative; overflow: hidden; cursor: default; transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 4px 12px rgba(0,0,0,0.08); background: #1F1E1C; border: 1px solid rgba(51, 49, 46, 0.15); }'
new_card = '.hc-card { flex: 0 0 260px; height: 280px; border-radius: 20px; scroll-snap-align: center; position: relative; overflow: hidden; cursor: default; transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 8px 24px rgba(0,0,0,0.1); background: #1F1E1C; }'
html = html.replace(old_card, new_card, 1)

# Clickable card hover: deeper shadow
old_click = '.hc-card.clickable:hover, .hc-card.clickable:active { transform: scale(1.03); box-shadow: 0 16px 32px rgba(0,0,0,0.25); }'
new_click = '.hc-card.clickable:hover, .hc-card.clickable:active { transform: scale(1.03); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }'
html = html.replace(old_click, new_click, 1)

# 4. More subtle overlay gradient
old_overlay = '.hc-card-overlay { position: absolute; inset: 0; background: linear-gradient(to bottom, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.3) 40%, rgba(0,0,0,0.85) 100%); }'
new_overlay = '.hc-card-overlay { position: absolute; inset: 0; background: linear-gradient(to bottom, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0.25) 40%, rgba(0,0,0,0.8) 100%); }'
html = html.replace(old_overlay, new_overlay, 1)

# 5. Better spacing for hc-wrap
old_hc = '.hc-wrap { padding: 0 4px; overflow: hidden; width: 100%; }'
new_hc = '.hc-wrap { padding: 0 8px; overflow: hidden; width: 100%; }'
html = html.replace(old_hc, new_hc, 1)

# 6. More spacing between groups
# dg-1: add margin-bottom
old_dg1 = '.dg-1 { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; position: relative; }'
new_dg1 = '.dg-1 { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; position: relative; }'
# After the mode-selector, add margin-bottom. We'll adjust dg-2 spacing and dg-3 spacing
html = html.replace(
    '.dg-2 { display: flex; flex-direction: column; gap: 6px; flex: 1; justify-content: center; padding: 4px 0; overflow: hidden; }',
    '.dg-2 { display: flex; flex-direction: column; gap: 6px; flex: 1; justify-content: center; padding: 8px 0 4px; overflow: hidden; }',
    1
)
html = html.replace(
    '.dg-3 { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }',
    '.dg-3 { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; padding-top: 6px; }',
    1
)

# 7. Premium CTA buttons - dark style like results pages
old_cta = '.cta-btn { border: none; color: #fff; background: var(--terracotta); letter-spacing: 0.2px; box-shadow: var(--shadow-md); }'
new_cta = '.cta-btn { border: 1px solid rgba(255,255,255,0.1); color: #FFFFFF; background: #1F1E1C; letter-spacing: 0.8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }'
html = html.replace(old_cta, new_cta, 1)

old_cta_hover = '.cta-btn:hover { background: #b05842; box-shadow: var(--shadow-lg); }'
new_cta_hover = '.cta-btn:hover { background: #2D2A24; border-color: rgba(255,255,255,0.2); box-shadow: 0 4px 16px rgba(0,0,0,0.2); }'
html = html.replace(old_cta_hover, new_cta_hover, 1)

# 8. Gallery button more subtle
old_gallery = '.gallery-btn { border: 1px solid rgba(0,0,0,0.08); background: var(--bg-card); color: #33312E; }'
new_gallery = '.gallery-btn { border: 1px solid rgba(0,0,0,0.06); background: var(--bg-card); color: var(--text-secondary); }'
html = html.replace(old_gallery, new_gallery, 1)

old_gallery_hover = '.gallery-btn:hover { background: #f5f3ef; border-color: rgba(0,0,0,0.12); color: #33312E; }'
new_gallery_hover = '.gallery-btn:hover { background: #f5f3ef; border-color: rgba(0,0,0,0.1); color: var(--text-primary); }'
html = html.replace(old_gallery_hover, new_gallery_hover, 1)

# 9. Menu/history icons premium hover - terracotta accent
old_menu_btn = '.menu-btn { position: absolute; top: 6px; right: 0; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #33312E; font-size: 16px; font-weight: 300; transition: opacity 0.15s ease, transform 0.25s ease; z-index: 5; opacity: 0.7; border: none; background: none; padding: 0; }'
new_menu_btn = '.menu-btn { position: absolute; top: 6px; right: 0; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #33312E; font-size: 16px; font-weight: 300; transition: color 0.2s ease, transform 0.25s ease; z-index: 5; opacity: 0.7; border: none; background: none; padding: 0; }'
html = html.replace(old_menu_btn, new_menu_btn, 1)

# menu-btn hover: terracotta
old_menu_hover = '.menu-btn:hover { opacity: 1; }'
new_menu_hover = '.menu-btn:hover { color: var(--terracotta); opacity: 1; }'
html = html.replace(old_menu_hover, new_menu_hover, 1)

# 10. Remove .mode-active-bar (it's not used in HTML, but let's keep it for safety)
# Actually, it is used in JS: `document.getElementById("modeActiveBar").style.opacity = "0";` at line 2406
# So keep it, just make it less intrusive

# 11. Make hc-scroll padding more generous
html = html.replace(
    '.hc-scroll { display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; padding: 4px 16px 8px; scrollbar-width: none; }',
    '.hc-scroll { display: flex; gap: 16px; overflow-x: auto; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; padding: 8px 20px 12px; scrollbar-width: none; }',
    1
)

# 12. Slightly larger card label with more padding
html = html.replace(
    '.hc-card-label { position: absolute; bottom: 18px; left: 18px; right: 18px; color: #FFFFFF; font-size: 17px; font-weight: 700; letter-spacing: 0.3px; text-shadow: 0 2px 12px rgba(0,0,0,0.5); z-index: 2; font-family: Georgia, serif; }',
    '.hc-card-label { position: absolute; bottom: 22px; left: 22px; right: 22px; color: #FFFFFF; font-size: 18px; font-weight: 700; letter-spacing: 0.3px; text-shadow: 0 2px 16px rgba(0,0,0,0.6); z-index: 2; font-family: Georgia, serif; }',
    1
)

with open(path, "w") as f:
    f.write(html)

# Verify JS syntax
import subprocess, os
result = subprocess.run(["node", "-e", "const fs=require('fs'); const s=fs.readFileSync('"+path+"','utf8'); const m=s.match(/<script>([\s\S]*?)<\/script>/); if(!m)process.exit(1); try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS_ERROR:',e.message);process.exit(1)}"], capture_output=True, text=True)
print(result.stdout.strip())
if result.returncode != 0:
    print("STDERR:", result.stderr.strip())