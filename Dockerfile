FROM rust:slim-bullseye as builder

LABEL maintainer="Antony <dentad@users.noreply.github.com>"
ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update; \
apt-get -y install --no-install-recommends python-is-python3 python3-minimal python3-venv python3-distutils python3-pip python3-wheel; \
apt-get -y install --no-install-recommends libxml2 libxslt1.1 zlib1g; \
apt-get -y install --no-install-recommends python-dev-is-python3 python3-dev python-pip-whl binutils binfmt-support make gcc g++ libxml2-dev libxslt1-dev zlib1g-dev patch

RUN pip install --user maturin
ENV PATH="/root/.local/bin:$PATH"

RUN mkdir -p /working
COPY ./ /working/
WORKDIR /working
RUN maturin build --bindings pyo3 --compatibility linux --release --jobs 4

RUN mkdir -p /opt/statisticalme
RUN mkdir -p /opt/statisticalme/venvsme
RUN python3 -m venv /opt/statisticalme/venvsme
ENV PATH="/opt/statisticalme/venvsme/bin:$PATH"
ENV VIRTUAL_ENV="/opt/statisticalme/venvsme"
RUN pip install --requirement /working/requirements.txt
RUN pip install /working/target/wheels/statisticalme-*.whl
RUN rm -rf "/opt/statisticalme/venvsme/share/python-wheels"

FROM debian:bullseye-slim

LABEL maintainer="Antony <dentad@users.noreply.github.com>"
ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update; \
apt-get -y full-upgrade --no-install-recommends; \
apt-get -y install --no-install-recommends python-is-python3 python3-minimal python3-venv python3-distutils; \
apt-get -y autoremove; \
apt-get clean; \
find /var/lib/apt/lists -type f -not -empty -delete

RUN mkdir -p /opt/statisticalme
WORKDIR /opt/statisticalme

RUN mkdir -p /opt/statisticalme/venvsme
COPY --from=builder /opt/statisticalme/venvsme /opt/statisticalme/venvsme
ENV PATH="/opt/statisticalme/venvsme/bin:$PATH"
ENV VIRTUAL_ENV="/opt/statisticalme/venvsme"

RUN mkdir -p /opt/statisticalme/var

ENTRYPOINT ["python3", "-m", "statisticalme"]
