ARG PG_VERSION=18.4
FROM postgres:${PG_VERSION}

ARG PG_BIGM_VERSION=1.2-20250903
ENV PG_BIGM_VERSION=${PG_BIGM_VERSION}

RUN apt-get update && apt-get install -y \
  build-essential \
  postgresql-server-dev-$PG_MAJOR \
  libicu-dev \
  wget \
  && wget https://github.com/pgbigm/pg_bigm/archive/refs/tags/v${PG_BIGM_VERSION}.tar.gz \
  && tar zxf v${PG_BIGM_VERSION}.tar.gz \
  && cd pg_bigm-${PG_BIGM_VERSION} \
  && make USE_PGXS=1 \
  && make USE_PGXS=1 install \
  && cd .. \
  && rm -rf pg_bigm-${PG_BIGM_VERSION} v${PG_BIGM_VERSION}.tar.gz \
  && apt-get purge -y --auto-remove build-essential wget \
  && rm -rf /var/lib/apt/lists/*

RUN echo "shared_preload_libraries='pg_bigm'" >> /usr/share/postgresql/postgresql.conf.sample