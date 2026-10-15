# AuthFrame 2

AuthFrame 2 is demonstrated inside a Docker Compose development environment for JWT authentication, policy-based authorization, audit logging, and protected upstream services.

## License

This project is licensed under the [Apache License 2.0](LICENSE.txt).

## Components

| Service | Purpose | Host endpoint |
| --- | --- | --- |
| Keycloak | Identity provider and OpenID Connect server | https://localhost:8443 |
| Envoy | JWT validation and external authorization gateway | http://localhost:8081 |
| PDP | Policy Decision Point | http://localhost:8085/health |
| API | AuthFrame API | http://localhost:8001 |
| Upstream service | Example protected service | http://localhost:8002 |
| SpiceDB | Relationship-based authorization datastore | localhost:50051 (gRPC), http://localhost:8088 |
| PostgreSQL | Persistent storage | localhost:5432 |
| ClickHouse | Audit-log storage | http://localhost:8123 |
| Vector | Ships Envoy access logs to ClickHouse | Internal |

## Prerequisites

- Docker Desktop with Docker Compose v2
- Ports `5432`, `8001`, `8002`, `8081`, `8085`, `8088`, `8123`, `8443`, `9000`, `9901`, and `50051` available
- Keycloak TLS certificate and key in `keycloak/certs/`:
  - `tls.crt`
  - `tls.key`

## Configuration

Configure the environment values in `.env` before starting the stack. Do not commit real passwords, private keys, or production certificates.

### PostgreSQL initialization

The initial database setup must create these databases and roles:

- `authframe` / `${DB_USER}`
- `spicedb` / `${DB_USER}`
- `keycloak` / `${KC_DB_USER}`
- optional `ecmp` database, if enabled

The Keycloak role must exist and have access to the Keycloak database. Otherwise Keycloak will fail with:

```text
FATAL: password authentication failed for user "keycloak"
DETAIL: Role "keycloak" does not exist.
```

PostgreSQL initialization scripts run only when the database volume is first created. After changing `db/init-multiple-dbs.sh`, remove and recreate the database volume in a development environment, or apply the required SQL manually.

## Start the stack

```powershell
docker compose up --build
```

Run it in the background:

```powershell
docker compose up --build -d
```

Check service status:

```powershell
docker compose ps
docker compose logs -f
```

## Accessing Keycloak

Open:

```text
https://localhost:8443
```

Use `localhost`, not `172.0.0.1`. The latter is generally a Docker bridge address and is not the published host endpoint.

A certificate warning is expected when using a self-signed development certificate.

## Useful commands

Follow a specific service:

```powershell
docker compose logs -f keycloak
docker compose logs -f database
docker compose logs -f spicedb
```

Restart a service:

```powershell
docker compose restart keycloak
```

Stop the stack:

```powershell
docker compose down
```

Reset all local persistent data:

```powershell
docker compose down -v
```

> Warning: `docker compose down -v` deletes local PostgreSQL and ClickHouse data.

## Startup notes

Some early messages are expected while dependencies initialize:

- SpiceDB may briefly report PostgreSQL connection refusals before PostgreSQL is ready.
- SpiceDB and Keycloak may log missing migration tables before they create their schemas.
- The API can fail at startup if ClickHouse is not accepting connections yet.

Persistent errors, restart loops, or a missing final "started" message indicate a real problem.

## Troubleshooting

### Keycloak cannot connect to PostgreSQL

Confirm that the Keycloak role and database exist:

```text
Role "keycloak" does not exist
```

Create the role/database or fix `db/init-multiple-dbs.sh`, then recreate the development database volume or apply the SQL manually.

### SpiceDB is not migrated

Run:

```powershell
docker compose run --rm spicedb-migrate
```

### API cannot connect to ClickHouse

If the API reports `Connection refused` for `clickhouse:8123`, wait for ClickHouse to start and restart the API:

```powershell
docker compose restart api
```

For a durable fix, configure the API to retry ClickHouse connections or add a ClickHouse health-check dependency.
