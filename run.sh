docker run --rm --network host\
  --name banking-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=banking \
  -v "$(pwd)/sql/schema.sql":/docker-entrypoint-initdb.d/schema.sql:ro \
  -v "$(pwd)/src/generate_data.py":/docker-entrypoint-initdb.d/generate_data.py:ro \
  banking-postgres