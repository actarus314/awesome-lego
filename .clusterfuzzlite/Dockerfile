# Image of the build of the fuzz targets (ClusterFuzzLite, workflow Fuzzing): OSS-Fuzz's Python builder, which brings
# Python, Atheris and PyInstaller; the scripts use the standard library only, so nothing else is installed.
# Pinned by digest; the image is rebuilt upstream every day, and Renovate renews the digest once a month (renovate.json).
FROM gcr.io/oss-fuzz-base/base-builder-python:v1@sha256:6ccbb6b02fcbb8e07d15680e933a6d835cdb579636032cec7d256d0f25d483e4
COPY . $SRC/awesome-lego
WORKDIR $SRC/awesome-lego
COPY .clusterfuzzlite/build.sh $SRC/
