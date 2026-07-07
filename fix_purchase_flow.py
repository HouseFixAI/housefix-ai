#!/usr/bin/env python3
"""Fix all 3 Purchase-flow defects: tab filtering, AI params, catalog image_urls."""

# ========== FIX 1 & 3: main.py ==========
with open('/home/team/shared/backend/main.py', 'r') as f:
    c = f.read()

# Fix 3: Add image_url to _seed_catalog
old_seed = """                pid = 'prod_' + re.sub(r'[^a-z0-9]', '_', store.lower().strip()) + '_' + str(idx)
                cur.execute("""
new_seed = """                pid = 'prod_' + re.sub(r'[^a-z0-9]', '_', store.lower().strip()) + '_' + str(idx)
                # Generate placeholder image URL from color palette
                pal_list = visual.get('color_palette', ['e8ddd0', 'd4c5b5'])
                img_color = pal_list[0].lstrip('#') if pal_list else 'e8ddd0'
                img_label = name[:20].replace(' ', '%20')
                img_url = f'https://placehold.co/400x400/{img_color}/ffffff?text={img_label}'
                cur.execute("""

old_seed_cols = """                    (id, name, store, category, price_cents, currency, price_segment,
                     color_palette, mood, style_tag, featured, available, last_updated)"""
new_seed_cols = """                    (id, name, store, category, price_cents, currency, price_segment,
                     color_palette, mood, style_tag, featured, available, image_url, last_updated)"""

old_seed_vals = """                    (pid, name, store, cat, price_cents, 'EUR', seg_name,
                      pal, mood, style_tag, featured,
                      datetime.datetime.now().isoformat()))"""
new_seed_vals = """                    (pid, name, store, cat, price_cents, 'EUR', seg_name,
                      pal, mood, style_tag, featured, img_url,
                      datetime.datetime.now().isoformat()))"""

assert old_seed in c, "old_seed not found!"
assert old_seed_cols in c, "old_seed_cols not found!"
assert old_seed_vals in c, "old_seed_vals not found!"

c = c.replace(old_seed, new_seed, 1)
c = c.replace(old_seed_cols, new_seed_cols, 1)
c = c.replace(old_seed_vals, new_seed_vals, 1)

# Fix 2: Move user_answers context to VERY TOP of purchase prompt
# Find the purchase advise prompt assembly
old_prompt = """            full_prompt = base_prompt + (
                f\"\\n\\nCONTEXT VAN EERDERE STAP:\\n{user_context}\\n\\n\"
                f\"{system_message}\"
            )"""
new_prompt = """            # Prepend user_answers as HARD CONSTRAINTS before the rest of the prompt
            purchase_context = user_context if user_intent == "purchase" else ""
            full_prompt = (
                f\"\\n\\n[[HARD CONSTRAINTS]]\\n{purchase_context}\\n[[END HARD CONSTRAINTS]]\\n\\n\"
                f\"{base_prompt}\\n\\n{system_message}\"
            )"""

assert old_prompt in c, "old_prompt not found!"
c = c.replace(old_prompt, new_prompt, 1)

with open('/home/team/shared/backend/main.py', 'w') as f:
    f.write(c)

print("main.py: Fixed seed_catalog + prompt ordering")

# ========== FIX 1 & Carousel: index.html ==========
with open('/home/team/shared/backend/templates/index.html', 'r') as f:
    html = f.read()

# Add CSS rule for segment-content (ensures display works)
old_css = '              .pv-board-del:hover { color: var(--terracotta); }'
new_css = old_css + '''

              /* Ensure tab filtering works (overrides any CSS cascade) */
              .segment-content { display: none !important; }
              .segment-content.seg-active { display: block !important; }'''

html = html.replace(old_css, new_css, 1)

# Make tab switching more robust — use seg-active class instead of inline style
old_tab = """      // Product cards per segment with ID attrs for async upgrade
      for(const seg of["budget","middenklasse","premium"]){
        const v=seg===bestSeg?"block":"none";
        html+='<div class="segment-content" id="seg-'+seg+'" style="display:'+v+'">';"""
new_tab = """      // Product cards per segment with ID attrs for async upgrade
      for(const seg of["budget","middenklasse","premium"]){
        html+='<div class="segment-content" id="seg-'+seg+'"'+(seg===bestSeg?' class="segment-content seg-active"':'')+'>';"""

html = html.replace(old_tab, new_tab, 1)

# Update tab switch handler to use class-based approach
old_switch = """setTimeout(()=>{
        document.querySelectorAll(".segment-tab").forEach(t=>t.addEventListener("click",function(){
          document.querySelectorAll(".segment-tab").forEach(x=>x.classList.remove("segment-active"));
          this.classList.add("segment-active");
          document.querySelectorAll(".segment-content").forEach(c=>c.style.display="none");
          const e=document.getElementById("seg-"+this.dataset.seg);if(e)e.style.display="block";
        }));
      },0);"""
new_switch = """setTimeout(()=>{
        document.querySelectorAll(".segment-tab").forEach(t=>t.addEventListener("click",function(){
          document.querySelectorAll(".segment-tab").forEach(x=>x.classList.remove("segment-active"));
          this.classList.add("segment-active");
          document.querySelectorAll(".segment-content").forEach(function(x){x.classList.remove("seg-active");});
          const e=document.getElementById("seg-"+this.dataset.seg);if(e)e.classList.add("seg-active");
        }));
      },0);"""

html = html.replace(old_switch, new_switch, 1)

# Make carousel fallback better — show gradient from color_palette instead of blank
old_carousel = """      prods.forEach(function(p){
        const u=p.image_url||"";
        const pal=p.color_palette||["#e8ddd0","#d4c5b5"];
        const fb=Array.isArray(pal)?pal[0]:"#e8ddd0";
        h+='<div class="pv-carousel-card"><div class="pv-carousel-img-wrap">';
        if(u)h+='<img src="'+u+'" alt="'+escHtml(p.name)+'" class="pv-carousel-img" loading="lazy" onerror="this.style.display=\\'none\\';this.parentNode.querySelector(\\'.pv-carousel-fallback\\').style.display=\\'block\\'" />';
        h+='<div class="pv-carousel-fallback" style="background:'+fb+'"></div></div>';
        h+='<div class="pv-carousel-price">'+(p.price||"")+'</div></div>';
      });"""
new_carousel = """      prods.forEach(function(p){
        const u=p.image_url||"";
        const pal=p.color_palette||["#e8ddd0","#d4c5b5"];
        const fb=Array.isArray(pal)?pal[0]:"#e8ddd0";
        const fb2=Array.isArray(pal)&&pal.length>1?pal[1]:"#d4c5b5";
        h+='<div class="pv-carousel-card"><div class="pv-carousel-img-wrap">';
        if(u&&u.startsWith("http"))h+='<img src="'+u+'" alt="'+escHtml(p.name)+'" class="pv-carousel-img" loading="lazy" onerror="this.style.display=\\'none\\';this.parentNode.querySelector(\\'.pv-carousel-fallback\\').style.display=\\'flex\\'" />';
        h+='<div class="pv-carousel-fallback" style="background:linear-gradient(135deg,'+fb+','+fb2+');display:'+(u&&u.startsWith("http")?'none':'flex')+'"><span class="pv-carousel-icon">\\uD83D\\uDD2E</span></div></div>';
        h+='<div class="pv-carousel-price">'+(p.price||"")+'</div></div>';
      });"""

html = html.replace(old_carousel, new_carousel, 1)

with open('templates/index.html', 'w') as f:
    f.write(html)

print("index.html: Fixed tab filtering + carousel fallback")

# ========== Re-seed database ==========
# Delete old DB so it gets re-seeded on next import
import os
db_path = '/home/team/shared/backend/product_catalog.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted old DB: {db_path}")

# Verify
import subprocess
result = subprocess.run(['python3', '-c', 'import main; print("Backend: OK"); c=main.search_catalog(limit=999); print(f"Products: {len(c)}"); imgs=[p.get(\'image_url\',\'\') for p in c if p.get(\'image_url\')]; print(f"With image_url: {len(imgs)}"); print(f"Sample: {imgs[0][:60] if imgs else \'NONE\'}")'], 
    capture_output=True, text=True, cwd='/home/team/shared/backend')
print(result.stdout.strip())
if result.stderr:
    print("STDERR:", result.stderr[:200])

print("\nAll fixes applied. Run node check next.")