# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
# This file is part of osm-fieldwork.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm-fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
ARG PYTHON_IMG_TAG=3.10


FROM docker.io/python:${PYTHON_IMG_TAG}-slim-bookworm as base
ARG COMMIT_REF
ARG PYTHON_IMG_TAG
ARG MAINTAINER=admin@hotosm.org
LABEL org.hotosm.osm-fieldwork.python-img-tag="${PYTHON_IMG_TAG}" \
      org.hotosm.osm-fieldwork.commit-ref="${COMMIT_REF}" \
      org.hotosm.osm-fieldwork.maintainer="${MAINTAINER}"
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends "locales" "ca-certificates" \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates
# Set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8



FROM base as extract-deps
WORKDIR /opt/python
COPY pyproject.toml pdm.lock /opt/python/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir pdm==2.6.1
RUN pdm export --prod > requirements.txt \
    && pdm export -G debug -G test -G docs \
        --no-default > requirements-ci.txt \
    && pdm export -G ui \
        --no-default > requirements-ui.txt



FROM base as build-wheel
WORKDIR /build
COPY pyproject.toml pdm.lock README.md LICENSE.md ./
COPY osm_fieldwork ./osm_fieldwork
RUN pip install pdm==2.6.1 && pdm build



FROM base as build
WORKDIR /opt/python
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "build-essential" \
        "gcc" \
        "libpcre3-dev" \
        "libpq-dev" \
        "libspatialindex-dev" \
        "libproj-dev" \
        "libgeos-dev" \
    && rm -rf /var/lib/apt/lists/*
COPY --from=extract-deps \
    /opt/python/requirements.txt /opt/python/
RUN pip install --user --no-warn-script-location \
    --no-cache-dir -r ./requirements.txt
COPY --from=build-wheel \
    "/build/dist/*-py3-none-any.whl" .
RUN whl_file=$(find . -name '*-py3-none-any.whl' -type f) \
    && pip install --user --no-warn-script-location \
    --no-cache-dir "${whl_file}"



FROM base as runtime
ARG PYTHON_IMG_TAG
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/root/.local/bin:$PATH" \
    PYTHON_LIB="/usr/local/lib/python$PYTHON_IMG_TAG/site-packages" \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "nano" \
        "curl" \
        "libpcre3" \
        "postgresql-client" \
        "libglib2.0-0" \
        "libspatialindex-c6" \
        "libproj25" \
        "libgeos-c1v5" \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build \
    /root/.local \
    /root/.local
WORKDIR /data
COPY entrypoint.sh /container-entrypoint.sh



FROM runtime as ui-base
ARG PYTHON_IMG_TAG
COPY --from=extract-deps \
    /opt/python/requirements-ui.txt /opt/python/
RUN mv /root/.local/bin/* /usr/local/bin/ \
    && mv /root/.local/lib/python${PYTHON_IMG_TAG}/site-packages/* \
    /usr/local/lib/python${PYTHON_IMG_TAG}/site-packages/ \
    && set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "git" \
        "xclip" \
        "libmtdev-dev" \
        "libgl-dev" \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade --no-warn-script-location \
    --no-cache-dir -r \
    /opt/python/requirements-ui.txt \
    # Add flask, required for webdebugger
    && pip install --upgrade --no-warn-script-location \
    --no-cache-dir flask==3.0.0 \
    && rm -r /opt/python
WORKDIR /app
COPY ui/main.py ui/osmfieldwork.kv ui/buildozer.spec ./
# Update the requirements in buildozer.spec
RUN requirements_list=$(grep -v '^#' requirements-ci.txt \
    | tr '\n' ',' | sed 's/^,//; s/,$//') \
    && sed -e "/^requirements =/c\requirements = $requirements_list" \
    buildozer.spec > temp_file.txt \
    && mv temp_file.txt buildozer.spec



FROM ui-base as ui-debug
# Default app storage dir
VOLUME ["/root/.config/osmfieldwork"]
VOLUME ["/tmp/.X11-unix"]
CMD ["python", "main.py", "-m", "webdebugger"]



FROM ui-base as ui-build
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "build-essential" \
        "automake" \
        "ant" \
        "cmake" \
        "zip" \
        "unzip" \
        "openjdk-17-jdk" \
        "autoconf" \
        "libtool" \
        "patch" \
        "pkg-config" \
        "zlib1g-dev" \
        "libncurses5-dev" \
        "libncursesw5-dev" \
        "libtinfo5" \
        "libffi-dev" \
        "libssl-dev" \
        "libltdl-dev" \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --user --no-warn-script-location \
    --no-cache-dir buildozer==1.5.0 \
    Cython==0.29.33 virtualenv==20.24.7
CMD ["buildozer", "android", "release"]



FROM runtime as ci
ARG PYTHON_IMG_TAG
# Add the SSL cert for debug odkcentral
COPY nginx/certs/central-fullchain.crt /usr/local/share/ca-certificates/
COPY --from=extract-deps \
    /opt/python/requirements-ci.txt /opt/python/
# Required for pytest-asyncio config
COPY pyproject.toml /data/
RUN cp -r /root/.local/bin/* /usr/local/bin/ \
    && cp -r /root/.local/lib/python${PYTHON_IMG_TAG}/site-packages/* \
    /usr/local/lib/python${PYTHON_IMG_TAG}/site-packages/ \
    && set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
    -y --no-install-recommends \
        "git" \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade --no-warn-script-location \
    --no-cache-dir -r \
    /opt/python/requirements-ci.txt \
    && rm -r /opt/python && rm -r /root/.local \
    # Update CA Certs
    && update-ca-certificates \
    # Pre-compile packages to .pyc (init speed gains)
    && python -c "import compileall; compileall.compile_path(maxlevels=10, quiet=1)"
# # Squash filesystem (reduce img size) NOTE this breaks PyTest!
# FROM scratch as ci
# COPY --from=ci-prep / /
# Override entrypoint, as not possible in Github action
ENTRYPOINT [""]
CMD [""]



FROM runtime as prod-prep
# Pre-compile packages to .pyc (init speed gains)
RUN python -c "import compileall; compileall.compile_path(maxlevels=10, quiet=1)" \
    && chmod +x /container-entrypoint.sh
# Squash filesystem (reduce img size)
FROM scratch as prod
COPY --from=prod-prep / /
ENTRYPOINT ["/container-entrypoint.sh"]
CMD ["bash"]
