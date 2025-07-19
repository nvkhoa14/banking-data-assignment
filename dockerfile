# Use the official Postgres image
FROM postgres

# Install Python3 & build deps for psycopg2
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy your schema and data-gen script into the init folder
COPY sql/schema.sql              /docker-entrypoint-initdb.d/
COPY src/generate_data.py        /docker-entrypoint-initdb.d/
COPY src/requirements.txt        /docker-entrypoint-initdb.d/

# Install Python deps
RUN pip3 install --no-cache-dir --break-system-packages \
    -r /docker-entrypoint-initdb.d/requirements.txt

# Add an init script that applies schema then runs generate_data.py
# It must be .sh and executable to be picked up by the official entrypoint
COPY sql/01-init.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/01-init.sh