<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Open Matter HEMS Connector

`resflex-open-matter-hems-connector` is the ElaadNL HEMS Matter connector, developed within the Residential Flexibility initiative of ElaadNL and FAN, part of the Dutch National Grid Congestion Action Program.

The connector bridges Home Energy Management Systems (HEMS) and flexible energy-intensive devices (FEIDs) over the Matter protocol. It consists of:

- A vendored Matter controller server (Python), forked from `matter-js/python-matter-server`

The controller server originates from an Apache-2.0 upstream and is maintained here as a hard fork; see [`NOTICE`](./NOTICE) for attribution. The EVSE-simulator firmware this connector is tested against lives in a separate repository, [`resflex-open-matter-device-connector`](https://github.com/ElaadNL/resflex-open-matter-device-connector); see [esp-matter integration](./docs/esp-matter-integration.md).

## Disclaimer

This software is an open reference implementation, developed under the
coordination of ElaadNL as part of the
[Residential Flexibility](https://elaad.nl/en/projects/residential-flexibility/) initiative. It is not a finished,
certified, or end-user product. Before publication, the code was reviewed for
security by the European Network for Cyber Security (ENCS); that review is a
snapshot in time, not a guarantee. Anyone who integrates this software into a
product does so at their own risk and is responsible for its secure integration,
ongoing security testing, regulatory compliance, and any certification of that
product. The software is provided "as is", without warranty, under the Apache
License 2.0.

Read the full [disclaimer](DISCLAIMER.md) before using this software.

---

## What it does

At a high level the controller server:

- Runs and owns a Matter fabric/controller context
- Stores commissioned device information and controller state persistently
- Exposes a WebSocket API (`/ws`, port `5580`) for local or trusted-network clients
- Allows multiple clients to interact with the same Matter fabric simultaneously
- Supports commissioning, device control, attribute reads/writes, and event streaming

Instead of embedding the Matter stack directly into a frontend, the server centralizes Matter operations, making it easy to build HEMS integrations, web dashboards, mobile apps, or automated test harnesses against a single fabric.

> [!WARNING]
> **The WebSocket API has no authentication by default.** Any client that can reach the server can issue privileged commands that control commissioned Matter devices (including energy devices). By default the server listens only on `127.0.0.1` (localhost). Prefer setting `--api-token` / `MATTER_API_TOKEN` when exposing the API beyond a single trusted process, confine non-local binds to a trusted management network, and terminate TLS at a reverse proxy for remote access.

The repository includes:

- Implementation code for the Matter controller server (`matter_server/`)
- Project documentation (`docs/`) covering architecture, WebSocket API, EVSE use cases, and integration guides
- Contribution guidelines
- CI workflows for tests, REUSE compliance, and Markdown linting

---

## System architecture

```text
Frontend / App / Automation Platform → WebSocket API → Matter Server → Matter Devices
```

This separates UI from controller logic: the Matter fabric remains online even if frontends disconnect, and frontends can be written in any language that speaks WebSockets.

---

## Getting started

For local development setup (clone, dependency install, running the server, troubleshooting), follow the vendored [`DEVELOPMENT.md`](./DEVELOPMENT.md). It is the authoritative source for development workflow.

For OS and network prerequisites (kernel features, IPv6, mDNS, Thread requirements), see [`docs/os_requirements.md`](./docs/os_requirements.md).

For running the server in a container, see [`docs/docker.md`](./docs/docker.md). A `Dockerfile` is included in the repository so the image can be built locally as `docker build -t resflex-open-matter-hems-connector .` (installs this repository's code, not the upstream PyPI package).

---

## Connecting a frontend

Once the server is running, a WebSocket-capable client on the same host can connect on port `5580`.

**Default connection URL (localhost bind):**

- `ws://127.0.0.1:5580/ws` or `ws://localhost:5580/ws`

To listen on additional addresses (for example a trusted management network), pass `--listen-address` explicitly.

Optional API token, listen address, TLS via reverse proxy, and Chip-Test / test-net PAA behavior are documented in [`security-deployment.md`](./security-deployment.md).

**Basic flow:**

1. Open the WebSocket connection.
2. Parse the initial `ServerInfoMessage` to verify schema compatibility.
3. Send a `start_listening` command to initialize the client state stream.
4. Issue commands (e.g., `get_nodes`, `commission_with_code`, `device_command`).
5. Listen for events (e.g., `node_updated`, `attribute_updated`).

For EVSE-specific clusters (`EnergyEvse`, `DeviceEnergyManagement`, telemetry) and example automations, see [`docs/evse-use-cases.md`](./docs/evse-use-cases.md).

---

## Documentation

- [Matter Adopter Onboarding](./docs/matter-adopter-onboarding.md) — core Matter concepts, commissioning, and general integration guidelines
- [Security and deployment](./docs/security-deployment.md) — localhost bind, optional API token, TLS via proxy, Chip-Test PAA / test mode
- [Matter FEID Analysis & Roadmap](./docs/matter-feid-analysis.md) — evaluation of Matter 1.4 for heat pumps, batteries, PV, and EVSE, plus future project roadmap
- [Matter EVSE Onboarding](./docs/matter-evse-onboarding.md) — architecture and Home Assistant mapping for EV chargers
- [Developer Integration Guide](./docs/project-overview-developer.md) — architecture, message schema, and integration constraints
- [WebSocket API reference](./docs/websockets_api.md) — frequently used commands
- [EVSE Compulsory Cluster Test Guide](./docs/evse-compulsory-cluster-test-guide.md) — test if an EV charger exposes required Matter clusters
- [Use cases](./docs/use-cases.md) — residential flexibility scenarios
- [EVSE use cases](./docs/evse-use-cases.md) — Home Assistant automations against the simulator
- [esp-matter integration](./docs/esp-matter-integration.md) — how the EVSE simulator fits in and where it lives
- [Glossary](./docs/glossary.md), [Style guide](./docs/style-guide.md)

---

## Repository structure

```text
/
├── README.md                       → Project overview and usage
├── CONTRIBUTING.md                 → Contribution process
├── SECURITY.md                     → Vulnerability disclosure
├── SUPPORT.md                      → Support expectations
├── CHANGELOG.md                    → Release notes
├── NOTICE                          → Apache-2.0 §4 attribution
├── REUSE.toml                      → REUSE bulk licensing rules
├── pyproject.toml                  → Build, runtime, and tooling configuration
├── Dockerfile, Dockerfile.dev      → Container images
├── matter_server/                  → Matter controller server (vendored)
├── tests/                          → Pytest suite
├── dashboard/                      → Web dashboard
├── scripts/                        → Operational tooling
├── docs/                           → Architecture, API, use cases, EVSE guides
└── .github/workflows/              → CI: tests, reuse, docs
```

---

## License

All content is licensed under the [Apache 2.0 License](./LICENSE). See [`NOTICE`](./NOTICE) for upstream attribution.

---

## License Compliance (REUSE)

This repository follows the [REUSE Specification](https://reuse.software/) to ensure consistent and machine-readable license and copyright information.

To support this:

- A REUSE configuration (`REUSE.toml`) is included in the repository
- Contributors are expected to use the provided pre-commit hook to validate compliance before committing
- The CI pipeline enforces REUSE compliance on all pull requests and is the authoritative check

Developers are free to integrate the pre-commit hook into their local workflow in the way that suits them best, as long as it is consistently applied.

If you want to run checks locally, the following projects are used:

- REUSE tool: [https://reuse.software/](https://reuse.software/)
- pre-commit framework: [https://pre-commit.com](https://pre-commit.com)

If a pull request fails the REUSE check in CI, it must be fixed before it can be merged.

---

## Questions or suggestions?

Please open an issue or contact the ElaadNL coordination team. This repository is intended to evolve with input from all participants.
