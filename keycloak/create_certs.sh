
#!/bin/bash
mkdir -p certs

# cleanup certs foder
rm certs/*


# Create a cert authority
openssl genrsa -out certs/ca.key 4096
openssl req -x509 -new -nodes -key certs/ca.key -sha256 -days 3650 -out certs/ca.crt -subj "/CN=ENPOWER Dev CA"
#"/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=cs_demo_ca"

# Create a key + CSR for keycloak.local
openssl genrsa -out certs/keycloak.local.key 2048
cat > certs/san.cnf <<'CFG'
[ req ]
distinguished_name = dn
req_extensions = req_ext
prompt = no
[ dn ]
CN = keycloak.local
[ req_ext ]
subjectAltName = @alt_names
[ alt_names ]
DNS.1 = keycloak.local
CFG

openssl req -new -sha256 \
    -key certs/keycloak.local.key \
    -out certs/keycloak.local.csr \
    -config certs/san.cnf

# Sign with CA
openssl x509 -req \
        -in certs/keycloak.local.csr \
        -CA certs/ca.crt \
        -CAkey certs/ca.key \
        -CAcreateserial \
        -out certs/keycloak.local.crt \
        -days 365 \
        -extfile certs/san.cnf \
        -extensions req_ext \
        -sha256

# rename some files
mv certs/keycloak.local.crt certs/tls.crt
mv certs/keycloak.local.key certs/tls.key

# generate PEM files
# openssl x509 -in certs/client.crt -out certs/client_cert.pem -outform PEM
# openssl x509 -in certs/server.crt -out certs/server_cert.pem -outform PEM
# openssl x509 -in certs/ca.crt -out certs/cacert.pem -outform PEM
# cp certs/client.key certs/client_key.pem
# cp certs/server.key certs/server_key.pem

# set folder and file permissions
chmod -R 755 ./certs
