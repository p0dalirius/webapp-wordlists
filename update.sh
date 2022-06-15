#!/usr/bin/env bash

log()  { echo -e "\\x1b[1m[\\x1b[93mLOG\\x1b[0m\\x1b[1m]\\x1b[0m ${@}";  }
info() { echo -e "\\x1b[1m[\\x1b[92mINFO\\x1b[0m\\x1b[1m]\\x1b[0m ${@}"; }
warn() { echo -e "\\x1b[1m[\\x1b[91mWARN\\x1b[0m\\x1b[1m]\\x1b[0m ${@}"; }


github_api_wait() {
  rate_limit_data=$(curl -s https://api.github.com/rate_limit)
  n_used=$(echo "${rate_limit_data}" | jq .resources.core.used)
  n_limit=$(echo "${rate_limit_data}" | jq .resources.core.limit)
  reset_timestamp=$(echo "${rate_limit_data}" | jq .resources.core.reset)
  echo "[+] Github API status | used: ${n_used}/${n_limit} (reset: ${reset_timestamp})"
  if [ $((${n_limit} - ${n_used})) -le 5 ]; then
    echo "[+] Possible API rate limit on next script, waiting for counter reset at ${reset_timestamp}"
    while [[ $(date +%s) -le ${reset_timestamp} ]]; do sleep 1; done
    sleep 2
  fi
}

generate=1

if [ ${generate} -eq 1 ]; then
  log "Updating wordlists ..."
  while read script; do
    pushd "$(dirname "${script}")" > /dev/null
    ./$(basename "${script}")
    popd > /dev/null
    github_api_wait
  done <<< $(find ./ -name "gen_*.py")
fi


log "Updating README.md ..."
NUMWORDLISTS=$(find ./ -name "*.txt" | wc -l)
sed -i 's/This repository contains \*\*.*\*\* wordlists!/This repository contains \*\*'${NUMWORDLISTS}'\*\* wordlists!/g' ./README.md
sed -i 's!https://img.shields.io/badge/wordlists-.*-brightgreen!https://img.shields.io/badge/wordlists-'${NUMWORDLISTS}'-brightgreen!g' ./README.md

git add README.md
git commit -m "Updated README.md"

log "Pushing to remote repository ..."
git push
