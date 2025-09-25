# builds the base container
docker buildx build . \
  --platform linux/amd64 \
  --tag internationalbrainlab/alyx_apache_base:latest \
  -f ./Dockerfile_base

# builds the top layer
docker buildx build . \
  --platform linux/amd64 \
  --tag internationalbrainlab/alyx_apache:latest \
  -f ./Dockerfile \
  --build-arg alyx_branch=deploy \
  --no-cache
