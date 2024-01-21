FROM ubuntu:bionic as base

# Tweak shell.
SHELL ["/bin/bash", "-c"]

# Installation helper.
RUN printf '#!/bin/sh\n\
export DEBIAN_FRONTEND=noninteractive; \
set -x; \
apt-get update -qq && \
if [ "x$1" = "x--repo" ]; \
then \
  "$0" software-properties-common && \
  apt-add-repository -y "$2" && \
  apt-get -qq update && \
  apt-get -qq remove --auto-remove software-properties-common && \
  shift 2; \
fi && \
if [ -z "$1" ]; \
then \
  apt-get -qq dist-upgrade --no-install-recommends --verbose-versions; \
else \
  apt-get -qq install --no-install-recommends --verbose-versions "$@"; \
fi; \
code=$?; \
apt-get -qq clean; \
exit $code\n\
' >install.sh && chmod +x install.sh

# Update.
RUN ./install.sh

# Install some essentials...
RUN ./install.sh \
      apt-utils \
      make \
      patch \
      wget \
      xz-utils \
      ;

# Install a more recent toolchain.
ARG GCC_VERSION_MAJOR="9"
RUN ./install.sh --repo ppa:ubuntu-toolchain-r/test {gcc,g++}-$GCC_VERSION_MAJOR
RUN for tool in g++ gcc gcov-dump gcov-tool gcov; \
    do \
      ln -s "../../bin/$tool-$GCC_VERSION_MAJOR" "/usr/local/bin/$tool"; \
      $tool --version; \
    done

# Install OpenSSL dependencies.
RUN ./install.sh \
      libkrb5-3 \
      libsctp1 \
      zlib1g \
      ;

# Install Python dependencies.
RUN ./install.sh \
      libbz2-1.0 \
      libdb5.3 \
      libffi6 \
      libgdbm5 \
      libgssapi-krb5-2 \
      liblzma5 \
      libncurses5 \
      libreadline7 \
      libsqlite3-0 \
      libuuid1 \
      zlib1g \
      ;

ARG JOBS=4

FROM base AS python_install

# Install OpenSSL build dependencies.
RUN ./install.sh \
      perl \
      libkrb5-dev \
      libsctp-dev \
      zlib1g-dev \
      ;

# Install a more recent version of OpenSSL.
ARG OPENSSL_VERSION="1.1.1k"
RUN wget --quiet "https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz"
RUN tar xaf "openssl-$OPENSSL_VERSION.tar.gz"
WORKDIR "openssl-$OPENSSL_VERSION"
RUN ./Configure \
      --openssldir=/etc/ssl \
      shared no-ssl3-method enable-ec_nistp_64_gcc_128 linux-x86_64 \
      "-Wa,--noexecstack -Wall" \
      && perl configdata.pm -d
RUN make -j"$JOBS"
ARG RUN_OPENSSL_TESTS="no"
RUN if [ "x$RUN_OPENSSL_TESTS" = 'xyes' ]; then make test; fi
RUN make install_sw
RUN find /usr/local/lib -name '*.a' -o -name '*.so' -print0 | xargs -0 strip
RUN strip /usr/local/bin/openssl
WORKDIR ..
RUN rm -rf "openssl-$OPENSSL_VERSION"*
RUN ldconfig
# Work around the braindead SSL detection code in Python...
RUN mkdir /usr/local/ssl && \
      ln -s ../include /usr/local/ssl/include && \
      ln -s ../lib64 /usr/local/ssl/lib

# Install Python from Github Actions @setup-python.
ARG GITHUB_ACTIONS_PYTHON="3.9.7-116077/python-3.9.7-linux-18.04-x64.tar.gz"
RUN wget --quiet "https://github.com/actions/python-versions/releases/download/$GITHUB_ACTIONS_PYTHON"
RUN tar xaf "${GITHUB_ACTIONS_PYTHON##*/}" -C /usr/local
RUN rm "${GITHUB_ACTIONS_PYTHON##*/}"
RUN rm /usr/local/Python-*.tgz
RUN ln -s python3 /usr/local/bin/python
RUN ln -s pip3 /usr/local/bin/pip
run strip /usr/local/lib/libpython*.so
run find /usr/local/lib/python3* -name '*.so' -print0 | xargs -0 strip
RUN ldconfig
# But does it work?
ARG RUN_PYTHON_TESTS="no"
RUN if [ "x$RUN_PYTHON_TESTS" = 'xyes' ]; then \
      python -m test \
      --multiprocess "$JOBS" \
      -uall,-audio,-cpu,-gui,-largefile,-network,-urlfetch \
      -x test_tk \
      -x test_gdb \
      -x test_clinic \
      ; fi

FROM base
COPY --from=python_install /usr/local /usr/local/
RUN ldconfig

# Install AppImage tools dependencies.
RUN ./install.sh \
      file \
      libp11-kit0 \
      ;

# Install log_dbus dependencies.
# Note: we install the `libdbus-1-dev` because the `libdbus-1.so`
# symlink is not part of the base `libdbus-1-3` package…
RUN ./install.sh \
      libdbus-1-dev \
      ;

# Install PyQt5 (minimal) dependencies.
RUN ./install.sh \
      libasound2 \
      libegl1-mesa \
      libfontconfig1 \
      libfreetype6 \
      libgl1-mesa-glx \
      libnss3 \
      libxcomposite1 \
      libxcursor1 \
      libxi6 \
      libxrandr2 \
      libxtst6 \
      ;

# vim: sw=2
