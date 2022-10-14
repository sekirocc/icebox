#!/bin/bash
set -e -x

ENV="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../" && pwd )"

echo $ROOT/env.local
if [ -f $ROOT/env.local ]; then
    ENV_FILE=$ROOT/env.local
else
    ENV_FILE=$ENV/env.sample
fi

set -o allexport
source $ENV_FILE
set +o allexport
 
envsubst < $ENV_FILE > $ROOT/.env
envsubst < $ENV/standalone.yml > $ROOT/docker-compose.yml
