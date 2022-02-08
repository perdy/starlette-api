#!/usr/bin/env bash

NO_FORMAT="\033[0m"
C_YELLOW1="\033[38;5;226m"
C_SPRINGGREEN2="\033[38;5;47m"
FOLDERS="dist flama.egg-info pip-wheel-metadata site test-results .coverage .pytest_cache"

function clean()
{
  for folder in $FOLDERS; do
    if [[ ! -d $folder ]]
    then
      printf "%b" "${C_YELLOW1}- Folder not found${NO_FORMAT}: $folder\n"
    else
      printf "%b" "🧹 ${C_SPRINGGREEN2}Deleting folder${NO_FORMAT}: $folder\n"
      rm -r "$folder" 2> /dev/null
    fi
  done
}

function main()
{
  echo "🔥 Cleaning directory..."
  clean
}

main