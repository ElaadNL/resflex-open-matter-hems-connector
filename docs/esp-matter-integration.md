<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# esp-matter Integration

The EVSE simulator that this connector commissions and controls is a separate
firmware project, maintained in its own repository.

## Location

The EVSE-simulator firmware lives in
[`ElaadNL/resflex-open-matter-device-connector`](https://github.com/ElaadNL/resflex-open-matter-device-connector),
built on `esp-matter`.

- **Device connector repo:** [`ElaadNL/resflex-open-matter-device-connector`](https://github.com/ElaadNL/resflex-open-matter-device-connector)
- **Original upstream:** [`espressif/esp-matter`](https://github.com/espressif/esp-matter) (`release/v1.4`)
- **License:** Apache-2.0

## What it provides

An ESP32-based EVSE simulator that:

- Implements the Matter `EnergyEvse` (`0x0099`), `DeviceEnergyManagement` (`0x0098`), and telemetry clusters that the controller exercises
- Acts as a commissioning target so the controller's flow can be tested end-to-end without real hardware
- Exposes the same cluster surface a production EVSE would, enabling automation tests against this connector

## Building and flashing

Building the firmware is out of scope for this repository. Clone the
device-connector repository and follow its guide:

- [`resflex-open-matter-device-connector` README](https://github.com/ElaadNL/resflex-open-matter-device-connector) for prerequisites, build, flash, and commissioning
- Its `examples/energy_evse/` firmware is the EVSE simulator this connector is tested against

## How the connector uses it

Once flashed and powered on, the simulator is commissioned via the controller's WebSocket API:

1. Issue a `commission_with_code` command with the simulator's Matter pairing code.
2. The controller adds the simulator to its fabric and persists the node.
3. Subsequent `read_attribute` / `write_attribute` / `device_command` calls drive the EVSE behavior.

For the WebSocket commands, see [`websockets_api.md`](./websockets_api.md).
For end-to-end automation examples (price-based charging, solar-surplus following) against the simulator, see [`evse-use-cases.md`](./evse-use-cases.md).
