#!/bin/bash
set -e -x

ENV="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../" && pwd )"

$ENV/compose.sh

cd $ROOT
docker-compose build --no-cache
