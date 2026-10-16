# Developer Integration Guide

## Start Here

If you are new to Matter, start with [`matter-evse-onboarding.md`](matter-evse-onboarding.md). It explains the basic Matter vocabulary and the relationship between Home Assistant entities, Matter attributes, Matter commands, and the EV charger.

Read this developer guide after that onboarding page if you need to understand the backend architecture. In this repository, `python-matter-server` is the Matter controller backend. Home Assistant is a client/consumer of that backend and exposes selected Matter device capabilities as Home Assistant entities.

## 1. Project Origin

This project is developed based on the Open Home Foundation `python-matter-server` project and extends it for this repository's needs.

Base project:

- [matter-js/python-matter-server](https://github.com/matter-js/python-matter-server)

The upstream project provides a Matter Controller Server built on top of the official Matter/CHIP SDK and exposes a WebSocket-based API so that different clients can interact with the same Matter fabric. This repository should be understood as a downstream development effort built on that foundation.

## 2. What This Project Does

At a high level, this project acts as a Matter controller server that:

- runs and owns a Matter fabric/controller context;
- stores commissioned device information and controller state persistently;
- exposes a WebSocket API for external consumers;
- allows multiple clients to interact with the same fabric;
- supports commissioning, device control, attribute reads/writes, and event streaming.

In practical terms, this server separates the Matter controller logic from the frontend or consumer application. Instead of embedding Matter stack behavior directly into each frontend, the server centralizes Matter operations and publishes them through a network-facing API.

## 3. Main Use Cases

This project is useful when a developer wants a single Matter backend that can be consumed by different user interfaces or applications.

Typical use cases include:

- Home Assistant integration, where Home Assistant acts as one consumer of the Matter server.
- A custom web frontend that connects over WebSocket and visualizes nodes, attributes, and events.
- A custom mobile application, such as a Flutter or Android app, that communicates with the server remotely.
- A desktop or internal operations tool for debugging, diagnostics, node inspection, or commissioning support.
- A multi-client architecture where more than one consumer needs access to the same Matter fabric and current device state.

## 4. Why This Architecture Is Useful

This architecture has several benefits for developers:

- The Matter fabric can keep running even if one frontend goes down.
- Multiple clients can connect to the same controller.
- Commissioning, subscriptions, and device interviews stay on the server side.
- Frontends do not need to embed the full Matter stack.
- Different UI technologies can reuse the same backend interface.

This is especially useful when you want to support more than one frontend channel, for example:

- Home Assistant for end users;
- a custom admin dashboard for diagnostics;
- a mobile app for device onboarding or control;
- a testing tool for engineering teams.

## 5. System Architecture

The integration model is:

`Frontend / App / Automation Platform -> WebSocket API -> Matter Server -> Matter Devices`

The important boundary is that the frontend is usually not the Matter controller. The server is the controller. The frontend is a consumer of the server API.

The server is responsible for:

- maintaining controller state;
- persisting storage;
- handling Matter SDK interactions;
- managing interviews and subscriptions;
- performing commissioning workflows;
- streaming server and node events back to connected clients.

## 6. Supported Frontend Integration Methods

Developers can connect to this server from different kinds of frontends.

### 6.1 Home Assistant

Home Assistant is the most well-known consumer of the upstream project. In this model:

- Home Assistant connects to the Matter Server as a client.
- The Matter Server remains the controller backend.
- Home Assistant uses the server for node data, events, commissioning, and control operations.

This is the reference use case, but it is not the only one.

### 6.2 Custom Web Frontend

A browser-based frontend can connect to the server WebSocket endpoint and exchange JSON messages.

This is appropriate for:

- dashboards;
- debug tools;
- device management panels;
- internal engineering UIs.

Important considerations:

- the browser must be able to reach the server network address and port;
- if the page is served over HTTPS, a plain `ws://` backend may be blocked by browser mixed-content rules;
- for production browser access, a reverse proxy with TLS termination is strongly recommended so the frontend can use `wss://`;
- this server does not provide built-in authentication or TLS configuration in its default documented setup, so direct internet exposure is not recommended.

### 6.3 Custom Mobile App

A mobile app can connect using a normal WebSocket client library.

This is appropriate for:

- Flutter applications;
- Android or iOS native apps;
- cross-platform mobile control apps.

This matches your successful experiment with a custom app approach: if the app can reach the server and speak the expected WebSocket protocol, it can act as a valid consumer.

### 6.4 Desktop or Internal Tooling

Desktop apps, CLI tools, QA tools, and automated test harnesses can connect in the same way.

This is appropriate for:

- automated integration tests;
- engineering diagnostics;
- node inspection tools;
- commissioning assistants.

### 6.5 Python Client Library

The upstream project also ships a Python client library in the same repository. This is the most convenient option when the consumer is another Python-based service.

This is useful when:

- you want typed models instead of hand-written JSON;
- you are building a backend-for-frontend service;
- you want a reference client implementation to copy from.

## 7. When a Frontend Can Successfully Connect

Any frontend can connect if all of the following are true:

1. The frontend can reach the server IP/hostname and TCP port.
2. The frontend uses the correct WebSocket endpoint: `/ws`.
3. The client and server schema versions are compatible.
4. The host machine running the server satisfies Matter networking requirements.
5. The device commissioning method being used matches the host capabilities.
6. The frontend sends commands in the message format expected by the server.

In other words, the UI technology is usually not the hard part. The real constraints are:

- network reachability;
- Matter/Thread host environment correctness;
- WebSocket protocol compatibility;
- commissioning prerequisites;
- deployment security choices.

## 8. Prerequisites, Conditions, and Constraints

This section is critical for developers. Most real integration failures come from these conditions, not from the frontend framework itself.

### 8.1 OS Requirements

According to the upstream project documentation:

- development or runtime is supported on recent 64-bit Linux;
- development is also supported on recent 64-bit macOS;
- non-64-bit environments are not supported;
- Windows and WSL are not supported for this Matter server runtime model.

For serious containerized runtime deployments, Linux is the safer target because Matter and Thread behavior depends heavily on host networking and IPv6 behavior.

### 8.2 Network Requirements

Matter relies heavily on local-network behavior, especially:

- IPv6;
- link-local multicast;
- mDNS/zeroconf;
- proper LAN or VLAN topology;
- Thread border router reachability when Thread devices are involved.

Important network conditions:

- The Matter server host should be on the same LAN or VLAN as the Matter devices and border routers whenever possible.
- Multicast filtering or aggressive "optimization" features on network gear can break Matter.
- mDNS forwarders may interfere with Matter traffic.
- Thread communication depends on correct IPv6 route advertisement handling.

If the network is segmented incorrectly, the frontend may still connect to the server, but the server may fail to discover, commission, or maintain communication with actual Matter devices.

### 8.3 Docker Networking Constraint

The documented Docker deployment uses host networking:

- `--network=host` for `docker run`
- `network_mode: host` for Docker Compose

This is not optional in the documented reference setup because Matter depends on local network behavior that is hard to preserve through normal container NAT.

As a result:

- Docker deployment is best treated as a Linux-hosted runtime pattern;
- deploying on environments with restricted host networking can cause discovery and communication issues;
- Bluetooth-based commissioning needs additional host access through D-Bus.

### 8.4 Bluetooth and Commissioning Constraint

For local commissioning of WiFi or Thread devices:

- the server host, not the frontend, needs the required commissioning capability;
- Bluetooth support must exist on the machine running the server if commissioning depends on BLE;
- in Docker, the D-Bus socket must be mounted for Bluetooth-related workflows in the documented setup.

If the host does not support Bluetooth:

- network-only commissioning may still work in some cases;
- already-networked devices may still be controllable;
- wireless onboarding flows may fail.

### 8.5 WiFi and Thread Credential Constraint

Before commissioning a new WiFi or Thread device, the server needs the correct network credentials.

Specifically:

- use `set_wifi_credentials` before commissioning WiFi devices;
- use `set_thread_dataset` before commissioning Thread devices;
- if those credentials are not set first, commissioning can fail.

### 8.6 Schema Compatibility Constraint

When a client connects, the server sends initial server information that includes:

- `schema_version`
- `min_supported_schema_version`
- `sdk_version`
- fabric information

Clients must verify schema compatibility. A frontend that copies an old command format or an outdated client implementation may connect successfully at the socket layer but still be logically incompatible.

### 8.7 Security Constraint

The default documented setup is intended for trusted-network or development usage. See [`security-deployment.md`](./security-deployment.md) for the full deployment model.

Developers should assume:

- API token authentication is optional and **off by default** (legacy local behavior);
- no built-in production TLS termination is provided (use a reverse proxy for `wss://`);
- the server defaults to listening on localhost (`127.0.0.1`);
- direct public internet exposure is unsafe;
- Chip-Test development PAA roots are loaded only with `--enable-test-net-dcl`.

## 9. How to Start This Docker Project

This section summarizes the documented Docker startup path for developers.

### 9.1 Minimal Docker Run

Use this when you want to start the server with persistent storage and host networking:

```sh
mkdir -p data

docker run -d \
  --name matter-server \
  --restart=unless-stopped \
  --security-opt apparmor=unconfined \
  -v "$(pwd)/data:/data" \
  --network=host \
  ghcr.io/matter-js/python-matter-server:stable
```

What this does:

- stores persistent Matter data in `./data`;
- binds the container to the host network stack;
- starts the `matter-server` entrypoint;
- uses the default command:
  `--storage-path /data --paa-root-cert-dir /data/credentials`

### 9.2 Docker Run with Bluetooth Commissioning Support

Use this when you need local commissioning support through Bluetooth:

```sh
mkdir -p data

docker run -d \
  --name matter-server \
  --restart=unless-stopped \
  --security-opt apparmor=unconfined \
  -v "$(pwd)/data:/data" \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/matter-js/python-matter-server:stable \
  --storage-path /data \
  --paa-root-cert-dir /data/credentials \
  --bluetooth-adapter 0
```

Use this mode when:

- the host has Bluetooth hardware;
- you want the server host to perform BLE-based commissioning;
- you need the documented D-Bus integration path.

### 9.3 Docker Compose Reference

```yaml
services:
  matter-server:
    image: ghcr.io/matter-js/python-matter-server:stable
    container_name: matter-server
    restart: unless-stopped
    network_mode: host
    security_opt:
      - apparmor:unconfined
    volumes:
      - ${USERDIR:-$HOME}/docker/matter-server/data:/data/
      - /run/dbus:/run/dbus:ro
    # If you override the command, keep the default arguments too:
    # command: --storage-path /data --paa-root-cert-dir /data/credentials --bluetooth-adapter 0
```

### 9.4 Important Startup Notes

- If you override the command, keep the default arguments for storage and PAA certificates.
- The default WebSocket server port is `5580`.
- The default WebSocket endpoint is `/ws`.
- The containerized server depends on host OS network correctness, not just container health.

### 9.5 Connection URL Examples

Typical URLs are:

- local server: `ws://localhost:5580/ws`
- LAN server: `ws://<server-hostname-or-ip>:5580/ws`
- Home Assistant add-on exposed on network: `ws://homeassistant.local:5580/ws`

If you put the server behind TLS termination:

- `wss://<your-domain-or-host>/ws`

## 10. Recommended Frontend Connection Flow

Any frontend should follow a consistent connection pattern.

### 10.1 Step 1: Open WebSocket Connection

Connect to:

```text
ws://<host>:5580/ws
```

or:

```text
wss://<host>/ws
```

depending on deployment.

### 10.2 Step 2: Read Initial Server Info

The server sends an initial `ServerInfoMessage` immediately after connection. The frontend should inspect:

- `schema_version`
- `min_supported_schema_version`
- `sdk_version`
- `fabric_id`
- `compressed_fabric_id`
- `wifi_credentials_set`
- `thread_credentials_set`
- `bluetooth_enabled`

This message lets the frontend decide:

- whether the protocol is compatible;
- whether commissioning prerequisites are already prepared;
- whether Bluetooth-based flows are available.

### 10.3 Step 3: Start Listening

Send:

```json
{
  "message_id": "init-1",
  "command": "start_listening"
}
```

This initializes the client-side state stream and causes the server to dump existing node information, after which further events can continue streaming.

### 10.4 Step 4: Perform Commands

After the listening phase, the frontend can issue commands such as:

- `get_nodes`
- `get_node`
- `set_wifi_credentials`
- `set_thread_dataset`
- `commission_with_code`
- `open_commissioning_window`
- `read_attribute`
- `write_attribute`
- `device_command`
- `diagnostics`

### 10.5 Step 5: Track Events

Frontends should handle server-pushed events such as:

- `node_added`
- `node_updated`
- `node_removed`
- `node_event`
- `attribute_updated`
- `server_shutdown`
- `server_info_updated`

This is how a frontend stays in sync instead of polling everything continuously.

## 11. Core API Patterns Developers Should Know

The WebSocket API uses JSON messages with a request/response plus event-stream model.

### 11.1 Command Message Shape

```json
{
  "message_id": "1",
  "command": "get_nodes"
}
```

With arguments:

```json
{
  "message_id": "2",
  "command": "read_attribute",
  "args": {
    "node_id": 1,
    "attribute_path": "1/6/0"
  }
}
```

### 11.2 Frequently Used Commands

| Command | Purpose |
| --- | --- |
| `start_listening` | Initialize node/event streaming for the client |
| `get_nodes` | Return all known commissioned nodes |
| `get_node` | Return one node by ID |
| `set_wifi_credentials` | Prepare WiFi credentials for commissioning |
| `set_thread_dataset` | Prepare Thread dataset for commissioning |
| `commission_with_code` | Commission a device using QR code or pairing code |
| `commission_on_network` | Advanced on-network commissioning flow |
| `discover` | Discover commissionable nodes |
| `open_commissioning_window` | Open pairing window for an already-controlled device |
| `read_attribute` | Read a Matter attribute |
| `write_attribute` | Write a Matter attribute |
| `device_command` | Send a cluster command |
| `diagnostics` | Retrieve server diagnostics |
| `remove_node` | Remove a node from the fabric |

### 11.3 Example Commissioning Flow

For a WiFi device:

1. Connect to `/ws`.
2. Read initial server info.
3. Send `set_wifi_credentials`.
4. Send `commission_with_code`.
5. Start or continue listening for node updates and interview completion.

For a Thread device:

1. Connect to `/ws`.
2. Read initial server info.
3. Send `set_thread_dataset`.
4. Send `commission_with_code`.
5. Monitor resulting node state and events.

### 11.4 EV Charger Domain Model

For EV charger integrations, a frontend should not treat the device as a single-cluster integration. In practice, a usable EV charger experience usually spans multiple Matter clusters that together describe identity, endpoint topology, charger state, power limits, energy telemetry, and energy-management behavior.

> Note: For non-EVSE devices (such as heat pumps, batteries, and PV inverters), the relevant clusters differ. See the [Matter FEID Analysis](matter-feid-analysis.md) for the capability models of other device types.

For this project, the desired EV charger integration coverage includes the following clusters across relevant endpoints:

- `Descriptor` (`0x001D`)
- `BasicInformation` (`0x0028`)
- `EnergyEvse` (`0x0099`)
- `EnergyEvseMode` (`0x009D`)
- `PowerSource` (`0x002F`)
- `DeviceEnergyManagement` (`0x0098`)
- `PowerTopology` (`0x009C`)
- `ElectricalPowerMeasurement` (`0x0091`)
- `ElectricalEnergyMeasurement` (`0x0090`)
- `DeviceEnergyManagementMode` (`0x009F`)

Taken together, these clusters form the practical domain model that a frontend can use to render charger identity, live charging state, session state, mode state, telemetry, and energy-management controls.

In this model:

- `Descriptor` helps identify which endpoints expose the charger-related server clusters and how the device is structured.
- `BasicInformation` provides the stable identity and firmware details needed for device-information screens.
- `EnergyEvse` acts as the primary operational cluster for charging state and charging control.
- `EnergyEvseMode` describes charger mode capabilities and the currently active EVSE mode.
- `PowerSource` describes wired supply characteristics and endpoint mapping.
- `DeviceEnergyManagement` represents higher-level energy-management capability and state.
- `PowerTopology` provides an endpoint-oriented view of the available power topology.
- `ElectricalPowerMeasurement` and `ElectricalEnergyMeasurement` provide cumulative and live electrical measurements for dashboards and analytics.
- `DeviceEnergyManagementMode` exposes mode-oriented controls for device energy management.

### 11.5 EV Charger Data That Frontends Should Read

For an EV charger frontend, the most useful starting point is to organize data into user-facing groups rather than only by cluster identifier.

The minimum identity dataset typically includes:

- `BasicInformation.VendorID` (`0x0000`)
- `BasicInformation.VendorName` (`0x0001`)
- `BasicInformation.ProductName` (`0x0002`)
- `BasicInformation.ProductID` (`0x0004`)
- `BasicInformation.HardwareVersion` (`0x0007`)
- `BasicInformation.HardwareVersionString` (`0x0008`)
- `BasicInformation.SoftwareVersion` (`0x0009`)
- `BasicInformation.SoftwareVersionString` (`0x000A`)
- `BasicInformation.ManufacturingDate` (`0x000B`)
- `BasicInformation.SerialNumber` (`0x000F`)

The minimum charger-state dataset typically includes:

- `EnergyEvse.State` (`0x0000`)
- `EnergyEvse.SupplyState` (`0x0001`)
- `EnergyEvse.FaultState` (`0x0002`)
- `EnergyEvse.ChargingEnabledUntil` (`0x0003`)
- `EnergyEvse.CircuitCapacity` (`0x0005`)
- `EnergyEvse.MinimumChargeCurrent` (`0x0006`)
- `EnergyEvse.MaximumChargeCurrent` (`0x0007`)
- `EnergyEvse.UserMaximumChargeCurrent` (`0x0009`)
- `EnergyEvse.NextChargeStartTime` (`0x0023`)
- `EnergyEvse.NextChargeTargetTime` (`0x0024`)
- `EnergyEvse.NextChargeRequiredEnergy` (`0x0025`)
- `EnergyEvse.NextChargeTargetSoC` (`0x0026`)
- `EnergyEvse.SessionID` (`0x0040`)
- `EnergyEvse.SessionDuration` (`0x0041`)
- `EnergyEvse.SessionEnergyCharged` (`0x0042`)

The minimum mode and energy-management dataset typically includes:

- `EnergyEvseMode.SupportedModes` (`0x0000`)
- `EnergyEvseMode.CurrentMode` (`0x0001`)
- `DeviceEnergyManagement.ESAType` (`0x0000`)
- `DeviceEnergyManagement.ESACanGenerate` (`0x0001`)
- `DeviceEnergyManagement.ESAState` (`0x0002`)
- `DeviceEnergyManagement.AbsMinPower` (`0x0003`)
- `DeviceEnergyManagement.AbsMaxPower` (`0x0004`)
- `DeviceEnergyManagement.PowerAdjustmentCapability` (`0x0005`)
- `DeviceEnergyManagement.Forecast` (`0x0006`)
- `DeviceEnergyManagement.OptOutState` (`0x0007`)
- `DeviceEnergyManagementMode.SupportedModes` (`0x0000`)
- `DeviceEnergyManagementMode.CurrentMode` (`0x0001`)

The minimum power and telemetry dataset typically includes:

- `PowerSource.Status` (`0x0000`)
- `PowerSource.Description` (`0x0002`)
- `PowerSource.WiredCurrentType` (`0x0005`)
- `PowerSource.WiredNominalVoltage` (`0x0007`)
- `PowerSource.WiredMaximumCurrent` (`0x0008`)
- `PowerSource.EndpointList` (`0x001F`)
- `ElectricalPowerMeasurement.Accuracy` (`0x0000`)
- `ElectricalPowerMeasurement.CumulativeEnergyImported` (`0x0001`)
- `ElectricalPowerMeasurement.CumulativeEnergyReset` (`0x0005`)
- `ElectricalEnergyMeasurement.PowerMode` (`0x0000`)
- `ElectricalEnergyMeasurement.Accuracy` (`0x0002`)
- `ElectricalEnergyMeasurement.Voltage` (`0x0004`)
- `ElectricalEnergyMeasurement.ActiveCurrent` (`0x0005`)
- `ElectricalEnergyMeasurement.ActivePower` (`0x0008`)
- `ElectricalEnergyMeasurement.Frequency` (`0x000E`)

This grouping is useful because frontend developers usually build screens such as device overview, live session state, charging control, schedule/targets, diagnostics, and energy dashboards. Organizing the document by these data groups makes it easier to map the Matter model to actual UI requirements.

### 11.6 EV Charger Commands and Events

For EV charger user interfaces, not all interactions are simple generic Matter reads and writes. The `EnergyEvse` and mode clusters define the business-level controls that a frontend may expose.

The primary EV charger commands include:

- `EnergyEvse.Disable` (`0x01`)
- `EnergyEvse.EnableCharging` (`0x02`)
- `EnergyEvse.SetTargets` (`0x05`)
- `EnergyEvse.GetTargets` (`0x06`)
- `EnergyEvse.ClearTargets` (`0x07`)
- `EnergyEvseMode.ChangeToMode` (`0x00`)
- `DeviceEnergyManagementMode.ChangeToMode` (`0x00`)

These commands typically back frontend features such as:

- enabling or disabling charging;
- setting charging windows or charging targets;
- reading existing targets before editing them;
- clearing previously configured targets;
- switching EVSE operating mode;
- switching device energy-management mode.

The primary EV charger domain events include:

- `EnergyEvse.EVConnected` (`0x00`)
- `EnergyEvse.EVNotDetected` (`0x01`)
- `EnergyEvse.EnergyTransferStarted` (`0x02`)
- `EnergyEvse.EnergyTransferStopped` (`0x03`)
- `EnergyEvse.Fault` (`0x04`)
- `EnergyEvse.RFID` (`0x05`)

These events are important because they represent charger business events, not just low-level state updates. In other words:

- generic Matter server events such as `attribute_updated` tell the client that a value changed;
- EVSE-specific events tell the client what operational event happened in charger terms.

This distinction is useful for frontend design. A session timeline, notification system, or audit log will usually care about `EVConnected`, `EnergyTransferStarted`, `Fault`, and similar domain events, while a data panel may care more about the resulting attribute values.

### 11.7 Recommended EV Charger Frontend Flow

For EV charger applications, the recommended frontend integration flow is more specific than the generic connection flow described earlier.

A typical EV charger frontend should:

1. Connect to the Matter server over `/ws`.
2. Read the initial `ServerInfoMessage` and validate schema compatibility.
3. Send `start_listening` to initialize node state and event streaming.
4. Identify charger-capable endpoints using `Descriptor`, especially `ServerList` and related endpoint structure data.
5. Read `BasicInformation` to populate device identity, firmware, and inventory views.
6. Read `EnergyEvse`, `EnergyEvseMode`, `PowerSource`, `DeviceEnergyManagement`, `DeviceEnergyManagementMode`, `ElectricalPowerMeasurement`, and `ElectricalEnergyMeasurement` to build the charger state model in the frontend.
7. React to both generic update events and EVSE-specific domain events to keep UI state and operator-visible timelines in sync.
8. Expose control actions only when charger state, mode state, and backend capability indicate that the command is valid.

This flow gives developers a better foundation for implementing screens such as:

- charger overview;
- session status and energy transfer state;
- live electrical telemetry;
- charging schedule and targets;
- charger mode control;
- diagnostics and fault handling;
- energy-management views.

### 11.8 Notes on IDs and Validation Scope

The EV charger reference data used for this guide is intentionally written in terms of Matter cluster IDs, attribute IDs, command IDs, and event IDs. In the desired reference file, these identifiers are written in hexadecimal form, which aligns well with Matter specifications and cluster documentation.

Frontend developers should keep in mind:

- the reference list is best treated as a desired EV charger integration coverage matrix, not as a guarantee that every field is already surfaced by every downstream implementation;
- hexadecimal identifiers in design documents may need to be translated into the numeric forms expected by the client library or WebSocket request format being used;
- `attribute_names`, `command_names`, and `event_names` may describe additional known fields beyond the minimum selected validation set, which is useful for future expansion and optional support.

For example, a document may refer to `EnergyEvse` as `0x0099`, while a concrete request path or implementation helper may expect the equivalent numeric cluster identifier in another form. Developers should therefore separate the specification-facing representation from the transport-facing representation used by their code.

## 12. Example: JavaScript Frontend Integration

This is a minimal browser or web-app example of direct WebSocket integration:

```js
const ws = new WebSocket("ws://localhost:5580/ws");

ws.onopen = () => {
  console.log("Connected");
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Received:", message);

  if (message.sdk_version) {
    ws.send(
      JSON.stringify({
        message_id: "start-1",
        command: "start_listening",
      }),
    );
  }
};

function getNodes() {
  ws.send(
    JSON.stringify({
      message_id: "nodes-1",
      command: "get_nodes",
    }),
  );
}

function turnOn(nodeId, endpointId = 1) {
  ws.send(
    JSON.stringify({
      message_id: "cmd-1",
      command: "device_command",
      args: {
        node_id: nodeId,
        endpoint_id: endpointId,
        cluster_id: 6,
        command_name: "On",
        payload: {},
      },
    }),
  );
}
```

Notes for browser-based frontends:

- For development on the same LAN, `ws://` is usually fine.
- For production web apps served over HTTPS, use `wss://` through a reverse proxy.
- Do not expose the raw server directly to the public internet.

## 13. Example: Why "Any Frontend" Is Feasible

From a developer integration perspective, "any frontend" is feasible because the frontend only needs to do three things well:

1. open a WebSocket connection;
2. send JSON commands in the expected shape;
3. process result and event messages.

That means the integration model can work with:

- Home Assistant;
- React, Vue, Angular, or plain browser apps;
- Flutter mobile apps;
- Android or iOS native apps;
- Electron or desktop tools;
- backend services acting as a bridge for UI clients.

The frontend technology is replaceable. The Matter server contract is the stable integration point.

## 14. When Direct Frontend-to-Server Access Is Good or Bad

### 14.1 Good Fit for Direct Access

Direct frontend access is reasonable when:

- the frontend runs on a trusted LAN;
- the deployment is internal or for development;
- you control both the frontend and the network;
- security requirements are light and well understood.

### 14.2 Better Fit for a Backend-for-Frontend Layer

A backend adapter is often better when:

- you need authentication and authorization;
- you need audit logging;
- you want API normalization for multiple UI clients;
- you want to hide raw Matter command details from frontend code;
- you want to isolate the Matter server inside a trusted network;
- you need to expose a secure internet-facing API to browsers or mobile apps.

In many production systems, the recommended pattern is:

`Frontend -> Your app backend / BFF -> Matter Server -> Matter devices`

This is usually more secure and easier to maintain than exposing the Matter server directly.

## 15. Common Integration Constraints by Method

### 15.1 Home Assistant

- Best-supported reference consumer.
- Requires the Matter Server to be reachable and correctly configured.
- If using the add-on, the WebSocket port may need to be explicitly exposed to the network.

### 15.2 Browser Frontend

- Requires reachable WebSocket URL.
- Mixed-content rules matter if the page is HTTPS.
- Authentication and TLS should usually be handled outside the Matter server.

### 15.3 Mobile App

- Requires LAN or routed access to the server.
- Works well if the app can persist session/state and handle reconnection.
- Commissioning support still depends on server-host capabilities, not phone capabilities, in this architecture.

### 15.4 Python Service

- Best option for server-to-server integration.
- Can use the upstream Python client implementation as a typed reference layer.

## 16. Existing Documentation in This Project

This repository already contains important upstream documentation that developers should read alongside this guide:

- `README.md`: project overview and positioning.
- `README.md` (`Development` section): local development environment and server/client development notes.
- `docs/docker.md`: Docker runtime instructions.
- `docs/os_requirements.md`: host OS, IPv6, multicast, and Thread-related requirements.
- `docs/security-deployment.md`: listen address, optional API token, TLS via proxy, and Chip-Test PAA mode.
- `docs/websockets_api.md`: commonly used WebSocket commands and example payloads.
- `dashboard/README.md`: dashboard usage and example WebSocket URLs.

This document intentionally consolidates those sources into one developer-facing integration guide.

## 17. Recommended Developer Checklist

Before saying "the frontend cannot connect," verify the following:

1. The server is running and listening on port `5580`.
2. The frontend is connecting to the correct `/ws` endpoint.
3. The frontend can reach the host over the network.
4. The client can parse the initial `ServerInfoMessage`.
5. Schema compatibility is valid.
6. If commissioning WiFi devices, WiFi credentials were set first.
7. If commissioning Thread devices, the Thread dataset was set first.
8. If using BLE commissioning, the server host has Bluetooth support and the required runtime access.
9. The host network supports IPv6, multicast, and Matter discovery correctly.
10. The server is not being exposed in an insecure way for a browser-based production deployment.

## 18. Contribution Guidelines for Developers

When extending this repository for additional frontend integration work:

- keep the Matter server as the source of truth for device/fabric state;
- avoid frontend-specific protocol forks if a shared WebSocket contract can be reused;
- document new commands, flows, or deployment assumptions in `docs/`;
- preserve compatibility expectations between frontend clients and server schema versions;
- clearly separate developer-only deployment instructions from end-user instructions;
- add security notes whenever exposing the server beyond a trusted local network.

If this repository introduces downstream-specific behavior beyond upstream `python-matter-server`, that behavior should be documented explicitly so future developers know what differs from upstream.

## 19. Summary

This project should be understood as a developer-facing Matter backend built on top of the upstream `python-matter-server` model. Its main purpose is to centralize Matter controller functionality and make it reusable from multiple frontend or client implementations through a WebSocket API.

The most important operational truth is this:

- frontend choice is flexible;
- Matter host networking conditions are not;
- Docker startup is straightforward;
- reliable commissioning and device communication still depend on the host OS, IPv6, multicast, Thread, and Bluetooth conditions.

As long as those prerequisites are satisfied, developers can build Home Assistant integrations, custom browser UIs, Flutter apps, native mobile apps, or backend adapters on top of the same server.

## 20. Document Changelog

### 2026-04-10

- Created an English developer-facing overview and integration guide for this repository.
- Added project purpose, use cases, Docker startup guidance, frontend integration methods, prerequisites, constraints, security notes, and source-document mapping.
- Explicitly documented that this repository is based on the upstream `matter-js/python-matter-server` project.
