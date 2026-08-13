ARG PG_VERSION=18.4

FROM postgres:${PG_VERSION}

ARG PG_VERSION
ARG PG_BIGM_VERSION

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  ca-certificates \
  build-essential \
  postgresql-server-dev-${PG_MAJOR} \
  libicu-dev \
  wget \
  && update-ca-certificates \
  && wget \
  -O /tmp/pg_bigm.tar.gz \
  "https://github.com/pgbigm/pg_bigm/archive/refs/tags/${PG_BIGM_VERSION}.tar.gz" \
  && tar -xzf /tmp/pg_bigm.tar.gz -C /tmp \
  && cd "/tmp/pg_bigm-${PG_BIGM_VERSION#v}" \
  && make USE_PGXS=1 \
  && make USE_PGXS=1 install \
  && cd / \
  && rm -rf \
  "/tmp/pg_bigm-${PG_BIGM_VERSION#v}" \
  /tmp/pg_bigm.tar.gz \
  && apt-get purge -y --auto-remove \
  build-essential \
  wget \
  && rm -rf /var/lib/apt/lists/*

RUN echo "shared_preload_libraries='pg_bigm'" \
  >> /usr/share/postgresql/postgresql.conf.sample