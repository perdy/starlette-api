#!/usr/bin/env bash

NO_FORMAT="\033[0m"
C_RED1="\033[38;5;196m"

publish_pkg()
{
    username=$PYPI_USERNAME
    password=$PYPI_PASSWORD

    if [[ (-z "$PYPI_USERNAME") || (-z "$PYPI_PASSWORD") ]] ; then
      printf "%b" "🆘 Error: Environment variables ${C_RED1}PYPI_USERNAME${NO_FORMAT} or ${C_RED1}PYPI_PASSWORD${NO_FORMAT} (or both) not found\n"
      return;
    else
        poetry config http-basic.pypi "$username" "$password"
    fi

    local arg="$1"
    if [ "$arg" == "--build" ]; then
      build_pkg --clean
    fi

    poetry publish
}

publish_pkg "${@:2}"