#!/usr/bin/env bash

while read script; do
  pushd "$(dirname "$script")"
  python3 $(basename "$script")
  popd
done <<< $(find ./ -name "gen_*.py")