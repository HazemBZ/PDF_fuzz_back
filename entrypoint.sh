#!/bin/sh
set -e

echo "((( IS_BACKEND $IS_BACKEND )))"

if [ -n "$IS_BACKEND" ]  &&  [ ! -f "./setup-complete" ]; then
    echo "Running first time setup ..."
    
    sh ./setup.sh

    touch ./setup-complete

fi

# Execute the main container command (Dockerfile "CMD" or docker-compose file "command")
exec "$@"
