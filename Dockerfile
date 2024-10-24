FROM debian:bookworm-slim

RUN apt update && apt install linux-perf -y

COPY wrapper /srv/

CMD ["/srv/wrapper", "/srv/p1", "/srv/p2"]
