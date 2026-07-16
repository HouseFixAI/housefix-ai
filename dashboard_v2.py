#!/usr/bin/env python3
"""Apply dashboard visual refinements — v2 premium polish."""
import subprocess

path = "/home/team/shared/backend/templates/index.html"
with open(path, "r") as f:
    html = f.read()

# 1. Logo + icons on exact same horizontal line
# Currently: .dash-header has display:flex;align-items:center;gap:12px
# The logo-title-sm and tagline are in a flex-column div, icons on the right
# Need to make sure the header aligns properly. The menu-btn is position:absolute
# which messes with alignment. Let's make the right-side icons use flexbox properly.
# Change the menu-btn from position:absolute to position:static already done.
# The issue is .menu-btn has position:absolute which is overridden by inline style="position:static"
# So they're already static. The header already has align-items:center.
# The logo-sub-sm adds a bit of height. Let's make sure vertical alignment is perfect.
# Actually, the .dash-header already has align-items:center, so this should be fine.
# Let me just ensure the header has proper line-height.

# 2. Slogan smaller and more subtle
old_logo_sub = '.logo-sub-sm { font-size: 12px; color: var(--text-muted); letter-spacing: 0.3px; margin-top: 1px; font-weight: 400; }'
new_logo_sub = '.logo-sub-sm { font-size: 10px; color: var(--text-muted); letter-spacing: 0.5px; margin-top: 1px; font-weight: 400; opacity: 0.7; }'
html = html.replace(old_logo_sub, new_logo_sub, 1)

# 3. Mode buttons: warm cream/beige instead of white, lower height, subtle shadow
old_mode_btn = '.mode-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 14px 10px; border-radius: 14px; background: var(--bg-card); border: 1.5px solid var(--border-light); cursor: pointer; transition: all 0.3s ease; color: var(--text-secondary); width: 100%; min-height: 64px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }'
new_mode_btn = '.mode-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 10px 10px; border-radius: 14px; background: #faf7f2; border: 1.5px solid var(--border-light); cursor: pointer; transition: all 0.3s ease; color: var(--text-secondary); width: 100%; min-height: 56px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }'
html = html.replace(old_mode_btn, new_mode_btn, 1)

# Mode button hover: warm
old_mode_hover = '.mode-btn:hover { border-color: var(--warm-beige); background: var(--bg-card-hover); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }'
new_mode_hover = '.mode-btn:hover { border-color: var(--warm-beige); background: #f5f0e8; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }'
html = html.replace(old_mode_hover, new_mode_hover, 1)

# Mode active: match warm cream
old_mode_active = '.mode-btn.mode-active { border-color: var(--terracotta); background: var(--terracotta-soft); box-shadow: 0 0 0 1px var(--terracotta), 0 4px 16px rgba(196,98,74,0.15); color: var(--terracotta); transform: translateY(-1px); }'
new_mode_active = '.mode-btn.mode-active { border-color: var(--terracotta); background: var(--terracotta-soft); box-shadow: 0 0 0 1px var(--terracotta), 0 4px 16px rgba(196,98,74,0.15); color: var(--terracotta); transform: translateY(-1px); }'
# (keep as-is, active state is fine)

# 4. Carousel height +10-15% (280px → 320px)
old_card = '.hc-card { flex: 0 0 260px; height: 280px; border-radius: 20px; scroll-snap-align: center; position: relative; overflow: hidden; cursor: default; transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 8px 24px rgba(0,0,0,0.1); background: #1F1E1C; }'
new_card = '.hc-card { flex: 0 0 260px; height: 320px; border-radius: 20px; scroll-snap-align: center; position: relative; overflow: hidden; cursor: default; transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 8px 24px rgba(0,0,0,0.1); background: #1F1E1C; }'
html = html.replace(old_card, new_card, 1)

# 5. Gallery button: same dark premium style as camera CTA, but subtle secondary difference
old_gallery = '.gallery-btn { border: 1px solid rgba(0,0,0,0.06); background: var(--bg-card); color: var(--text-secondary); }'
new_gallery = '.gallery-btn { border: 1px solid rgba(255,255,255,0.08); background: rgba(31,30,28,0.85); color: rgba(255,255,255,0.6); letter-spacing: 0.8px; }'
html = html.replace(old_gallery, new_gallery, 1)

old_gallery_hover = '.gallery-btn:hover { background: #f5f3ef; border-color: rgba(0,0,0,0.1); color: var(--text-primary); }'
new_gallery_hover = '.gallery-btn:hover { background: rgba(45,42,36,0.9); border-color: rgba(255,255,255,0.2); color: rgba(255,255,255,0.9); }'
html = html.replace(old_gallery_hover, new_gallery_hover, 1)

# 6. Adjust dash-header to ensure perfect vertical alignment
old_header = '.dash-header { display: flex; align-items: center; gap: 12px; padding: 6px 0; }'
new_header = '.dash-header { display: flex; align-items: center; gap: 12px; padding: 6px 0; line-height: 1; }'
html = html.replace(old_header, new_header, 1)

# Also ensure the logo-title-sm has proper line-height for alignment
old_logo_title = '.logo-title-sm { font-family: \'Playfair Display\', serif; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; color: var(--text-primary); }'
new_logo_title = '.logo-title-sm { font-family: \'Playfair Display\', serif; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; color: var(--text-primary); line-height: 1.2; }'
html = html.replace(old_logo_title, new_logo_title, 1)

# 7. Make the gap between logo and icons consistent - the menu-btn gap is 2px currently
# The two buttons are in a div with gap:2px. Let's make them gap:6px for better spacing
html = html.replace(
    '<div style="margin-left:auto;display:flex;align-items:center;gap:2px">',
    '<div style="margin-left:auto;display:flex;align-items:center;gap:6px">',
    1
)

# 8. Adjust the dg-1 gap to be tighter
html = html.replace(
    '.dg-1 { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; position: relative; }',
    '.dg-1 { display: flex; flex-direction: column; gap: 4px; flex-shrink: 0; position: relative; }',
    1
)

with open(path, "w") as f:
    f.write(html)

# Verify JS syntax
result = subprocess.run(["node", "-e", "const fs=require('fs'); const s=fs.readFileSync('"+path+"','utf8'); const m=s.match(/<script>([\\s\\S]*?)<\\/script>/); if(!m)process.exit(1); try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('JS_ERROR:',e.message);process.exit(1)}"], capture_output=True, text=True, shell=True)
print(result.stdout.strip())
if result.returncode != 0:
    print("STDERR:", result.stderr.strip())
    exit(1)