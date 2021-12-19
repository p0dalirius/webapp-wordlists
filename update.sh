#!/usr/bin/env bash

while read script; do
  pushd "$(dirname "$script")"
  ./$(basename "$script")
  popd
done <<< $(find ./ -name "gen_*.py" | grep -v 'drupal' | grep -v 'wordpress')