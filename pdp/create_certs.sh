
#!/bin/bash
mkdir -p ./certs

# cleanup certs foder
rm ./certs/*

# Root CA
openssl req -x509 -newkey rsa:4096 -days 365 -nodes \
  -keyout ./certs/ca.key -out ./certs/ca.crt -subj "/CN=ENPOWER CA"

cat > ./certs/pdp.cnf <<'CFG'
[ req ]
distinguished_name = dn
req_extensions = v3_req
prompt = no
[ dn ]
CN = pdp
[ v3_req ]
subjectAltName = @alt_names
[ alt_names ]
DNS.1 = pdp
CFG

cat > ./certs/envoy.cnf <<'CFG'
[ req ]
distinguished_name = dn
req_extensions = v3_req
prompt = no
[ dn ]
CN = envoy
[ v3_req ]
subjectAltName = @alt_names
[ alt_names ]
DNS.1 = envoy
CFG


# PDP server cert
openssl req -newkey rsa:2048 -nodes -keyout ./certs/pdp.key -out ./certs/pdp.csr -config ./certs/pdp.cnf 
openssl x509 -req -in ./certs/pdp.csr -CA ./certs/ca.crt -CAkey ./certs/ca.key -CAcreateserial \
  -out ./certs/pdp.crt -days 365 -sha256 -extensions v3_req -extfile ./certs/pdp.cnf

# Envoy client cert
openssl req -newkey rsa:2048 -nodes -keyout ./certs/envoy.key -out ./certs/envoy.csr -subj "/CN=envoy"
openssl x509 -req -in ./certs/envoy.csr -CA ./certs/ca.crt -CAkey ./certs/ca.key -CAcreateserial \
  -out ./certs/envoy.crt -days 365 -sha256 -extensions v3_req -extfile ./certs/envoy.cnf

# set folder and file permissions
chmod -R 755 ./certs
