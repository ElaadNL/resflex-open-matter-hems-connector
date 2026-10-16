<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Matter adopter onboarding

This guide is for teams that want to adopt the Open Matter HEMS Connector but are new to Matter. It explains the practical Matter concepts you need before you commission devices, build a HEMS integration, or validate a Matter EV charger.

The goal is not to replace the Matter specification. The goal is to give adopters enough context to make good early decisions and avoid the most common integration mistakes.

## Who should read this

Read this guide if you are:

- evaluating whether Matter is suitable for a HEMS-to-device integration;
- onboarding a Matter EV charger, simulator, or test device;
- building a frontend, dashboard, mobile app, or test harness against this connector;
- comparing Matter with S2, EEBUS, OCPP, or Modbus in the ElaadNL interoperability work;
- debugging first-run problems around commissioning, networking, or missing device capabilities.

If you already understand Matter and only need the backend API, continue with [`project-overview-developer.md`](project-overview-developer.md) and [`websockets_api.md`](websockets_api.md).

## The short version

Matter is a local-network application protocol for securely controlling devices. In this repository, the Matter Server is the controller backend. It owns the Matter fabric, commissions devices, keeps device state, and exposes a WebSocket API for HEMS applications and other clients.

The main integration chain is:

```text
HEMS / frontend / test tool -> WebSocket API -> Matter Server -> Matter fabric -> Matter device
```

For EV charging use cases, the Matter device is usually an EVSE node. The HEMS does not send a proprietary EVSE command directly to the charger. It sends a request to the Matter Server, and the server performs the relevant Matter read, write, command, or subscription operation.

## Core Matter concepts

| Concept | What it means for adopters |
| --- | --- |
| Controller | Software that can commission and control Matter devices. In this repository, the Matter Server fills this role. |
| Fabric | The trusted Matter security domain shared by a controller and commissioned devices. A device can belong to multiple fabrics through multi-admin. |
| Commissioning | The process of adding a device to a fabric. This establishes trust and gives the controller operational credentials. |
| Node | One commissioned Matter device. An EV charger normally appears as one node. |
| Endpoint | A functional part of a node. A single node can expose several endpoints for different functions. |
| Device type | The declared role of an endpoint, such as an EVSE-related device type. Device types define which clusters are expected. |
| Cluster | A group of related capabilities, such as `EnergyEvse`, `DeviceEnergyManagement`, or `ElectricalEnergyMeasurement`. |
| Attribute | A readable or writable value inside a cluster, such as a charging current limit or supply state. |
| Command | An action sent to a cluster, such as enabling or disabling charging. |
| Event | A device-originated notification, such as a charging state transition. |
| Subscription | A long-lived request that lets the controller receive updates when selected attributes or events change. |

The most important habit is to think in paths:

```text
node -> endpoint -> cluster -> attribute / command / event
```

When an integration "cannot find" a feature, first check which endpoint exposes it and which cluster owns it.

## What this connector provides

This repository provides a Matter controller server and project documentation for HEMS interoperability work. The server:

- maintains the Matter fabric and controller state;
- stores commissioned node data persistently;
- exposes the `/ws` WebSocket endpoint on port `5580`;
- supports commissioning, node inspection, attribute reads and writes, commands, and event streaming;
- lets multiple clients consume the same Matter backend instead of embedding a Matter stack in every frontend.

This means an adopter can build a HEMS connector, dashboard, mobile app, or QA tool as a normal WebSocket client while the Matter-specific controller work stays on the server.

## Adoption path

Use this path when you are starting from zero.

1. Confirm the runtime environment

   Matter depends on local network behavior, especially IPv6, mDNS, link-local multicast, and Thread routing when Thread devices are involved. Read [`os_requirements.md`](os_requirements.md) before choosing the host. For container deployment, read [`docker.md`](docker.md) and note that the documented setup uses host networking.

2. Decide how devices will be commissioned

   A Wi-Fi or Thread device may require Bluetooth during commissioning. The machine running the Matter Server needs the commissioning capability, not just the phone, frontend, or HEMS client. If Bluetooth is unavailable, network-only commissioning may still work for devices that are already reachable on the network.

3. Start the Matter Server and keep its storage

   Treat the server storage as controller identity and fabric state. If you delete it, the controller may lose its commissioned fabric context and devices may need to be commissioned again.

4. Commission one device first

   Start with one EVSE simulator or one known-good Matter device. Use a QR code or manual pairing code through `commission_with_code`. Set Wi-Fi credentials or a Thread dataset first when the device needs them.

5. Inspect the node structure

   Use `get_nodes`, `get_node`, Home Assistant diagnostics, or the dashboard to confirm the node, endpoints, clusters, and attributes that the device actually exposes.

6. Validate EVSE capabilities

   For EV charger work, compare the device against the expected EVSE cluster surface before writing automations. Use [`evse-compulsory-cluster-test-guide.md`](evse-compulsory-cluster-test-guide.md) and the local [`desired.json`](desired.json) example.

7. Build against stable Matter behavior

   Prefer the connector API and Matter data model over UI-specific assumptions. Home Assistant entity names are useful for demo automation, but the protocol-level contract is the Matter cluster, attribute, command, and event surface exposed by the device.

## Commissioning expectations

Commissioning is often the first place where new Matter adopters lose time. Keep these points in mind:

- Commissioning creates trust. It is not only device discovery.
- The Matter Server host performs controller-side commissioning work.
- For Wi-Fi devices, call `set_wifi_credentials` before `commission_with_code` when the device needs Wi-Fi credentials.
- For Thread devices, call `set_thread_dataset` before `commission_with_code` when the device needs Thread credentials.
- Bluetooth-based commissioning requires Bluetooth access on the server host. In Docker, this may require host D-Bus access as shown in [`docker.md`](docker.md).
- Network-only commissioning is useful for devices that are already on the IP network, but it is not a universal replacement for BLE commissioning.
- If you replace the server storage, you replace the controller identity from the device's perspective.

The first successful commissioning run should be treated as an infrastructure validation: it proves the host, network, credentials, and pairing flow are good enough for the next integration step.

## Reading device capabilities

After commissioning, avoid assuming that a device supports a feature because it is marketed as an EV charger or because a UI exposes a friendly entity. Confirm the Matter data model.

For each device, capture:

- node ID;
- endpoints and device types;
- server clusters per endpoint;
- supported attributes for each relevant cluster;
- accepted commands;
- emitted events, where observable;
- Home Assistant entity mappings, if Home Assistant is part of the adopter workflow.

For EVSE and other flexible devices, the most relevant cluster areas include energy management, operational modes, and electrical telemetry. For a detailed breakdown of which clusters to read for EVSEs, heat pumps, batteries, and solar inverters, refer to the [Matter FEID Analysis](matter-feid-analysis.md).

The compulsory-cluster guide explains how to compare this surface against the current EVSE project expectation.

## Choosing an integration style

Adopters usually choose one of these integration styles:

| Integration style | When to use it |
| --- | --- |
| Home Assistant | Best when the HEMS logic is expressed as Home Assistant entities and automations. |
| Custom WebSocket client | Best for a HEMS backend, dashboard, QA tool, or non-Home Assistant automation service. |
| Python client library | Best when the adopter service is Python and benefits from the existing typed client models. |
| Dashboard or diagnostic UI | Best for commissioning support, node inspection, and engineering troubleshooting. |

The connector does not require the frontend to be the Matter controller. The frontend can stay small and stateless while the Matter Server owns the fabric and streams updates.

## Security and deployment boundaries

Matter secures device communication within the fabric, but adopters still need to secure their own deployment around the Matter Server.

Important boundaries:

- Full deployment guidance: [`security-deployment.md`](./security-deployment.md).
- By default the WebSocket API has no token and listens on localhost (`127.0.0.1`) only.
- Set `--api-token` or `MATTER_API_TOKEN` to require a shared secret (`Authorization: Bearer` or `?token=`).
- Do not expose the WebSocket API directly to the internet or an untrusted LAN.
- Confine any non-local bind (`--listen-address`) to a trusted management network.
- Terminate TLS at a reverse proxy (`wss://`) when remote access is needed; the server does not terminate TLS itself.
- Production mode does not trust Chip-Test development PAA roots. Use `--enable-test-net-dcl` only for development / simulator commissioning.
- Protect the server storage because it contains controller state.
- Limit who can commission devices or open commissioning windows.
- Keep test fabrics separate from production fabrics when evaluating devices or firmware.

For browser-based frontends, use `wss://` behind a trusted reverse proxy in production. A page served over HTTPS may reject plain `ws://` connections because of browser mixed-content rules.

## Readiness checklist

Before calling an integration "ready", confirm the following:

- The Matter Server host satisfies the OS and network requirements.
- IPv6, mDNS, multicast, and Thread border router routing are correct for the target devices.
- Server storage is persistent and backed up according to the deployment policy.
- Commissioning succeeds from the chosen host and commissioning method.
- The device exposes the expected endpoints, clusters, attributes, commands, and events.
- EVSE devices pass the project compulsory-cluster comparison for the target scope.
- The HEMS or frontend handles initial state, updates, reconnects, and command failures.
- Access to the WebSocket API is restricted to trusted clients.
- The adopter has a repeatable way to capture diagnostics when a device or firmware version changes.

## Common first-run problems

| Symptom | Likely area to check |
| --- | --- |
| Device is not discovered | IPv6, mDNS, multicast filtering, LAN or VLAN topology, Thread routing. |
| Commissioning fails for Wi-Fi or Thread device | Missing Wi-Fi credentials, missing Thread dataset, unavailable Bluetooth, expired pairing window. |
| Frontend connects but no devices appear | Wrong WebSocket endpoint, incompatible message flow, `start_listening` not sent, empty server storage. |
| Device appears but EVSE controls are missing | Wrong endpoint, missing EVSE clusters, incomplete firmware support, Home Assistant mapping gap. |
| Attribute reads work but events are unclear | Diagnostics snapshot may not include enough event evidence; inspect Matter Server logs or live event stream. |
| Device worked before but is now unknown | Server storage was replaced, fabric membership changed, or the device was removed from the fabric. |

When debugging, separate the layers: first prove the server can see the node, then prove the node exposes the capability, then prove the HEMS or frontend maps it correctly.

## Where to go next

- [`matter-feid-analysis.md`](matter-feid-analysis.md) explains how Matter 1.4 supports non-EVSE flexible loads (heat pumps, batteries, PV) and the project roadmap.
- [`matter-evse-onboarding.md`](matter-evse-onboarding.md) explains the EVSE-specific Home Assistant path and entity mapping.
- [`evse-compulsory-cluster-test-guide.md`](evse-compulsory-cluster-test-guide.md) explains how to validate a Matter EV charger against the project scope.
- [`project-overview-developer.md`](project-overview-developer.md) explains the backend architecture and integration constraints.
- [`security-deployment.md`](security-deployment.md) covers API token, listen address, TLS via proxy, and Chip-Test / test-net PAA mode.
- [`websockets_api.md`](websockets_api.md) shows the commonly used WebSocket commands.
- [`evse-use-cases.md`](evse-use-cases.md) shows EVSE automation examples.
- [`glossary.md`](glossary.md) aligns Matter terms with S2, EEBUS, and general HEMS terminology.
