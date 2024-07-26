# This script assumes that the env files of each container are set for local testing.

cd social-media-db-manager
# Looks like docker uses stdout, delegating stderr for the container contents
docker compose up --build > build-logs.log 2> container-logs.log &

cd ..

cd postgres-db

docker compose up --build > build-logs.log 2> container-logs.log &

echo "Build Started"