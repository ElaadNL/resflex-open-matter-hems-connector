<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.0] – 2026-10-19

Initial public release, developed under the ElaadNL
[Residential Flexibility](https://elaad.nl/en/projects/residential-flexibility/)
initiative.

### Added

- Matter controller server for the HEMS side, vendored as a hard fork of
  python-matter-server; provenance and attribution in `NOTICE`
- WebSocket API for commissioning, device control, attribute reads and writes,
  and event streaming, with optional API token authentication
- Docker setup and deployment security guidance
- Documentation of the EVSE use cases and the WebSocket API
