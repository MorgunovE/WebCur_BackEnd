FROM ubuntu:latest
LABEL authors="Evgenii Morgunov"

ENTRYPOINT ["top", "-b"]