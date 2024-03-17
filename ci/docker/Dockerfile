FROM python:3.11-alpine AS build

ARG MIRRORS_SOURCE="dl-cdn.alpinelinux.org"
ARG PYPI_SOURCE="pypi.org"

RUN sed -i "s/dl-cdn.alpinelinux.org/${MIRRORS_SOURCE}/g" /etc/apk/repositories \
 && apk add --update --no-cache \
      bash \
      binutils \
      gcc \
      g++ \
      git \
      make \
      libffi-dev \
 && pip3 install poetry -i "https://${PYPI_SOURCE}/simple"

WORKDIR /tmp/project

ADD . /tmp/project

RUN make install

RUN make build

FROM alpine:3.18 AS runtime

LABEL maintainers="Leryn <leryn1122@gmail.com>"
LABEL description="yuque-exporter"

ARG MIRRORS_SOURCE="dl-cdn.alpinelinux.org"

RUN sed -i "s/dl-cdn.alpinelinux.org/${MIRRORS_SOURCE}/g" /etc/apk/repositories \
 && apk add --update --no-cache \
      bash \
      git \
      openssh

COPY --from=build /tmp/project/dist/yuque-exporter /usr/local/bin/yuque-exporter

WORKDIR /tmp

ENTRYPOINT [ "/usr/local/bin/yuque-exporter" ]
