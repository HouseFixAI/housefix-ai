#!/bin/bash
cd /home/team/shared/backend
git add templates/index.html
git commit -m "fix: foto max-height 250px, snapshot max-height, history accordion overflow fix"
git push origin main
echo "GIT_DONE:$?" > /home/team/shared/git_status.txt