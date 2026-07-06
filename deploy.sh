#!/bin/sh
cd /home/team/shared/backend
git add templates/index.html
git commit -m "fix: body overflow scroll, snapshot max-height 50vh, history dashboard niet tonen"
git push origin main
echo "PUSH_DONE"