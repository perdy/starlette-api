#!/usr/bin/env bash

run_version()
{
  echo "⬆️ Upgrade version:"
  poetry version "$@"
}

run_version "${@:2}"