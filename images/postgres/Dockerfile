ARG PG_VERSION
ARG PG_MAJOR
ARG PG_BIGM_VERSION

FROM postgres:${PG_VERSION}

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  postgresql-server-dev-${PG_MAJOR} \
  libicu-dev \
  wget \
  && wget -O /tmp/pg_bigm.tar.gz \
  "https://github.com/pgbigm/pg_bigm/archive/refs/tags/${PG_BIGM_VERSION}.tar.gz" \
  && tar -xzf /tmp/pg_bigm.tar.gz \
  -C /tmp \
  && cd "/tmp/pg_bigm-${PG_BIGM_VERSION}" \
  && make USE_PGXS=1 \
  && make USE_PGXS=1 install \
  && cd / \
  && rm -rf \
  "/tmp/pg_bigm-${PG_BIGM_VERSION}" \
  /tmp/pg_bigm.tar.gz \
  && apt-get purge -y --auto-remove \
  build-essential \
  wget \
  && rm -rf /var/lib/apt/lists/*

RUN echo "shared_preload_libraries='pg_bigm'" \
  >> /usr/share/postgresql/postgresql.conf.sample