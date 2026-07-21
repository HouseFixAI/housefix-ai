#!/usr/bin/env python3
"""Add scroll listener to carousel to update selectedCarouselIntent on swipe."""
import subprocess

p = "/home/team/shared/backend/templates/index.html"
with open(p, "r", encoding="utf-8") as f:
    s = f.read()

old = """      scroll.innerHTML = html;
    }"""

new = """      scroll.innerHTML = html;
      scroll.onscroll = function() {
        if (!list || !list.length || !clickable) return;
        var cards = scroll.querySelectorAll('.hc-card');
        if (!cards.length) return;
        var scrollRect = scroll.getBoundingClientRect();
        var center = scrollRect.left + scrollRect.width / 2;
        var bestIdx = 0, bestDist = Infinity;
        for (var i = 0; i < cards.length; i++) {
          var cr = cards[i].getBoundingClientRect();
          var cardCenter = cr.left + cr.width / 2;
          var dist = Math.abs(cardCenter - center);
          if (dist < bestDist) { bestDist = dist; bestIdx = i; }
        }
        var item = list[bestIdx];
        if (item && item.a) {
          var m = item.a.match(/'([^']+)'/);
          if (m) selectedCarouselIntent = m[1];
        }
      };
    }"""

if old in s:
    s = s.replace(old, new)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)
    print("Scroll listener added to carousel")
else:
    print("ERROR: pattern not found")

r = subprocess.run(["node", "-e", "const fs=require('fs');const s=fs.readFileSync('/home/team/shared/backend/templates/index.html','utf8');const m=s.match(/<script>([\\s\\S]*?)<\\/script>/);try{new Function(m[1]);console.log('JS_OK')}catch(e){console.log('Error: '+e.message)}"], capture_output=True, text=True, cwd="/home/team/shared")
print("JS:", r.stdout.strip())