FROM envoyproxy/envoy:v1.35-latest

USER root

RUN apt-get update && \
    apt-get install -y ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log/envoy \
 && chown -R envoy:envoy /var/log/envoy
USER envoy

COPY envoy.yaml /etc/envoy/envoy.yaml
CMD ["/usr/local/bin/envoy", "-c", "/etc/envoy/envoy.yaml", "--service-cluster", "enpower-gateway"]
