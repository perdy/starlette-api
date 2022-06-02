#!/usr/bin/env bash

NO_FORMAT="\033[0m"
C_RED1="\033[38;5;196m"

build_pkg()
{
  echo "🔥 Build package:"
  local arg="$1"
  if [ -z "$arg" ]; then
    poetry build
  elif [[ "$arg" == "-c" || "$arg" == "--clean" ]]; then
    sh "${PWD}/scripts/clean.sh"
    poetry build
  else
    printf "%b" "🚨 ${C_RED1}Unknown argument:${NO_FORMAT} ${arg}\n"
  fi
}

build_pkg "${@:2}"