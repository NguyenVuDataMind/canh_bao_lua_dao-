# build.ps1 - Docker Compose Build với BuildKit
# Usage: .\build.ps1 [docker-compose build arguments]

$env:DOCKER_BUILDKIT=1
docker-compose build $args

