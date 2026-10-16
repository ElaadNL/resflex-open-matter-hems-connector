<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Contributing Guide

Thank you for your interest in contributing to this project.

This repository contains the Open Matter HEMS Connector: a Matter controller
server with a WebSocket API for integrating energy devices into a HEMS,
developed as part of the ElaadNL
[Residential Flexibility](https://elaad.nl/en/projects/residential-flexibility/)
initiative.

---

## Scope of Contributions

You can contribute by:

- Reporting bugs or interoperability issues with Matter devices
- Improving the controller server, its WebSocket API, or the dashboard
- Adding or improving tests
- Improving documentation, including the EVSE use cases and integration guides

---

## Implementation Contributions

The controller server is vendored from an Apache-2.0 upstream and maintained
here as a hard fork; see [`NOTICE`](./NOTICE) for attribution. The EVSE-simulator
firmware it is tested against is maintained separately in
[`resflex-open-matter-device-connector`](https://github.com/ElaadNL/resflex-open-matter-device-connector).

Implementation pull requests should:

- Include unit tests where reasonable
- Carry REUSE-compliant license and copyright information (per-file SPDX headers,
  sidecar `.license` files, or matching rules in `REUSE.toml`)
- Add a `CHANGELOG.md` entry under an `Unreleased` heading
- Use one of the branch prefixes listed below
- Pass all required CI checks (REUSE, markdownlint, tests)

---

## How to Contribute

1. Fork the repository
2. Create a focused branch for your change:

   ```bash
   git checkout -b fix/my-change
   ```

3. Make a small, reviewable change and add or update tests where reasonable
4. Open a pull request against the `main` branch with a clear description of
   what changed, why, and how you validated it

---

## Review and Merge Process

All changes are reviewed by ElaadNL maintainers. Pull requests are reviewed for:

- Correct behaviour against the Matter data and interaction model
- Security of the control API, commissioning, and certificate handling
- Adequate tests and documentation

---

## Branch Naming Convention

- `feat/<area>` – new features
- `fix/<description>` – bug fixes
- `test/<description>` – test-only changes
- `docs/<topic>` – documentation changes
- `chore/<area>` – maintenance and dependency updates

---

## License and Copyright

By contributing, you agree that your contribution is licensed under the
[Apache License 2.0](LICENSE). No Contributor License Agreement (CLA) is
required.

---

## Code of Conduct

Please keep all contributions respectful and constructive.

---

## Security

Do not report security issues in public issues. Follow the process in
[SECURITY.md](SECURITY.md).

---

## Questions?

See [SUPPORT.md](SUPPORT.md), or open an issue if you are unsure whether
something belongs in this repository.
