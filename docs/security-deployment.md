<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Security and deployment

This guide describes how to run the Open Matter HEMS Connector control API safely. The WebSocket API on port `5580` can commission devices and send privileged Matter commands (including energy-device control). Treat it as a management plane, not a public API.

For Matter concepts and commissioning, see [`matter-adopter-onboarding.md`](./matter-adopter-onboarding.md). For command payloads, see [`websockets_api.md`](./websockets_api.md).

## Defaults

| Setting | Default | Meaning |
| --- | --- | --- |
| Listen address | `127.0.0.1` | Only clients on the same host can connect |
| API token | unset | Authentication is **off** (legacy behavior) |
| TLS | not terminated by the server | Use a reverse proxy for `wss://` when needed |
| Chip-Test / test-net PAA | off | Production trust store does not include development PAA roots |

A same-host frontend (HEMS, dashboard, custom app, or Home Assistant) that connects to `ws://127.0.0.1:5580/ws` without a token keeps the previous unauthenticated local behavior.

### How to enable each setting

None of these are on except the localhost bind. Compose `command:` replaces the image `CMD`, so repeat `--storage-path` and `--paa-root-cert-dir` whenever you add flags.

**Listen address** — already enabled as `127.0.0.1`. To also accept IPv6 localhost (`ws://localhost:5580/ws`):

```yaml
"--listen-address", "127.0.0.1",
"--listen-address", "::1",
```

To listen on a management NIC (not the public internet):

```yaml
"--listen-address", "192.168.10.20",
```

`0.0.0.0` binds every IPv4 interface; only use it with token + firewall, and prefer a reverse proxy on localhost instead.

**API token** — off until you set a secret. Server:

```yaml
environment:
  MATTER_API_TOKEN: ${MATTER_API_TOKEN}
command:
  [
    "--storage-path", "/data",
    "--paa-root-cert-dir", "/data/credentials",
    "--listen-address", "127.0.0.1",
    "--api-token", "${MATTER_API_TOKEN}",
  ]
```

Or `export MATTER_API_TOKEN='…'` and `matter-server --api-token "$MATTER_API_TOKEN"`. Clients must send the same value:

- `Authorization: Bearer <token>`
- or `ws://127.0.0.1:5580/ws?token=<token>`

The Python client reads `MATTER_API_TOKEN` automatically. Unset both the flag and the env var to return to legacy (no auth). A same-host client that cannot send a token may keep it unset; any client that can send `Authorization` or `?token=` should set it.

**TLS** — there is no `--tls` flag. Enable it in a reverse proxy in front of `127.0.0.1:5580`, then connect with `wss://`. Keep port `5580` unpublished.

**Chip-Test / test-net PAA** — off in production. Enable only for development simulators that use Chip-Test attestation:

```yaml
"--enable-test-net-dcl",
```

Do not set this on a production fabric. Restart after adding it so the trust store can fetch test roots.

## Optional API token

Enable a shared secret when more than one process can reach the API, or when you bind beyond localhost.

```bash
export MATTER_API_TOKEN='replace-with-a-long-random-secret'
matter-server --api-token "$MATTER_API_TOKEN"
```

Clients must supply the same value using either:

- HTTP header: `Authorization: Bearer <token>`
- Query string: `ws://127.0.0.1:5580/ws?token=<token>`

The Python client (`MatterClient` / `MatterClientConnection`) reads `MATTER_API_TOKEN` automatically when set.

If `--api-token` and `MATTER_API_TOKEN` are both unset, the server does not require credentials.

## Listen address

```bash
# Default: localhost only
matter-server

# Intentional non-local bind (trusted management network only)
matter-server --listen-address 0.0.0.0
# or
matter-server --listen-address 192.168.10.20
```

Do not publish port `5580` to the internet. Prefer localhost bind plus a reverse proxy, or bind only on a management VLAN.

## TLS

The Matter Server does not terminate TLS. For remote or browser clients:

1. Put a reverse proxy in front of `127.0.0.1:5580`.
2. Expose `wss://` to clients.
3. Keep the Matter Server on localhost (or a private interface).
4. Optionally require the API token as well.

Pages served over HTTPS cannot use plain `ws://` because of browser mixed-content rules.

## Development PAA roots (Chip-Test)

In production mode the connector:

- fetches production DCL PAA roots;
- does **not** fetch Chip-Test / development git PAA roots;
- removes any leftover Chip-Test files from the local trust store.

Devices or simulators that use development attestation certificates need test mode:

```bash
matter-server --enable-test-net-dcl
```

Use that flag only on test fabrics. Do not enable it on a production fabric that must reject counterfeit or development devices.

## Deployment architectures

These two patterns are the supported ways to run the control API. Matter device traffic (mDNS, IPv6, Thread) still needs the Matter Server host on the same LAN as the devices; that is separate from who may open port `5580`.

Access to the control API is protected by **localhost bind + optional token + TLS at a reverse proxy**. This repository does not implement in-process TLS, browser `Origin` checks, or per-command authorization. A shared token (when set) grants full fabric-admin rights.

### Architecture A — Same-host frontend (preferred)

Use this when the HEMS, dashboard, or other WebSocket client already runs on the same field host as the Matter Server (Home Assistant is one such client, not a requirement). Do not split machines only for security; loopback is enough if nothing else can reach `5580`.

```text
HEMS / dashboard / app  --ws://127.0.0.1:5580/ws-->  Matter Server (listen 127.0.0.1 only)
                                                          |
                                                          +-- Matter / mDNS / IPv6 --> FEIDs on LAN
```

| Control | Config |
| --- | --- |
| Listen | `--listen-address 127.0.0.1` (add `::1` if the client uses `localhost`) |
| Token | **on if the client can send it**; unset only for local clients that cannot send `Authorization` or `?token=` |
| TLS | not required on loopback |
| PAA | production (do **not** set `--enable-test-net-dcl`) |
| Firewall / compose | do not publish `5580`; no `ports: ["5580:5580"]` |
| Client URL | `ws://127.0.0.1:5580/ws` |

Example `matter-server` service (no token — legacy local client):

```yaml
matter-server:
  image: <your-image>
  network_mode: host
  command:
    [
      "--storage-path", "/data",
      "--paa-root-cert-dir", "/data/credentials",
      "--log-level", "info",
      "--listen-address", "127.0.0.1",
    ]
  volumes:
    - ./matter_data:/data
```

If the same-host client is the Python library, a custom HEMS, or any stack that can send a bearer token, add `--api-token` / `MATTER_API_TOKEN` even in architecture A.

The frontend process must share the host network (or otherwise reach `127.0.0.1`). `network_mode: host` is typical so the Matter stack can also see the LAN.

### Architecture B — Remote frontend via reverse proxy

Use this when the HEMS or other client is on another host, or several clients must share one fabric. The Matter process still binds loopback. Remote frontends never connect to `5580`; they connect to the proxy.

```text
HEMS / dashboard / app (other host)  --wss://matter.example/ws-->  reverse proxy :443
                                                                      |
                                                                      +--> 127.0.0.1:5580 Matter Server
                                                                              |
                                                                              +-- Matter / mDNS --> FEIDs on LAN
```

| Control | Config |
| --- | --- |
| Listen | `127.0.0.1` only (never `0.0.0.0` on a public NIC) |
| Token | **on** (`--api-token` / `MATTER_API_TOKEN`); the remote client must send it |
| TLS | reverse proxy terminates TLS; clients use `wss://` |
| PAA | production (do **not** set `--enable-test-net-dcl`) |
| Firewall / compose | allow 443 (or VPN) only; **do not publish 5580** |
| Client URL | `wss://matter.example/ws` with `Authorization: Bearer <token>` or `?token=<token>` |

Example `matter-server` service (token from the environment, not committed to git):

```yaml
matter-server:
  image: <your-image>
  network_mode: host
  environment:
    MATTER_API_TOKEN: ${MATTER_API_TOKEN}
  command:
    [
      "--storage-path", "/data",
      "--paa-root-cert-dir", "/data/credentials",
      "--log-level", "info",
      "--listen-address", "127.0.0.1",
      "--api-token", "${MATTER_API_TOKEN}",
    ]
  volumes:
    - ./matter_data:/data
```

Put nginx or Caddy on the same host (`network_mode: host` or otherwise able to reach loopback). Terminate TLS there and reverse-proxy WebSockets to `http://127.0.0.1:5580`. Do not map host port `5580`.

The proxy does not carry Matter device discovery. A remote HEMS can drive the API only if a Matter Server still sits on the site LAN.

You can rehearse B on the same machine: keep Matter on `127.0.0.1:5580`, put the proxy on `8443` with TLS, confirm the LAN IP `:5580` fails and `wss://127.0.0.1:8443/ws` succeeds. A local frontend can stay on architecture A unless it accepts `wss://` and a token.

### What not to do

- Do not put `5580` on a public load balancer.
- Do not enable `--enable-test-net-dcl` on a production fabric.
- Do not treat architecture A (no token) as equivalent to full authentication; it only works because the API is not reachable off-box.

## Related CLI flags

| Flag / env | Purpose |
| --- | --- |
| `--listen-address` | Override bind address (repeatable) |
| `--api-token` / `MATTER_API_TOKEN` | Optional shared-secret WebSocket auth |
| `--enable-test-net-dcl` | Load test-net DCL and Chip-Test development PAA roots |
| `--paa-root-cert-dir` | Directory for the PAA trust store |
| `--port` | WebSocket TCP port (default `5580`) |
