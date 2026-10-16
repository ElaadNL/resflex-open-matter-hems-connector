<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Glossary

This glossary maps common terms across the open protocols used for residential flexibility.
It helps ensure consistency across protocols and documentation.

| **Term**           | **S2**                      | **EEBus / SPINE**                                | **Matter 1.4**                             | **Usage / Notes** |
|--------------------|-----------------------------|--------------------------------------------------|--------------------------------------------|------------------|
| **HEMS**           | CEM (Customer Energy Manager) | CEM (Central Energy Manager)                    | Controller (multi-admin Node)              | Central orchestrator that receives grid signals, processes them, and controls devices. |
| **Device / Asset** | RM (Resource Manager)        | SPINE Actor (e.g. EVSE, PV, Battery)            | Node (with Endpoints)                      | A flexible, controllable device. |
| **Function**       | Control Type (e.g. PEBC)      | Use Case + Data Point via SPINE Features        | Endpoint (Device Type + Clusters)          | The logical capability being controlled (e.g. charge EV, curtail PV). |
| **Constraint**     | PowerConstraints / EnergyConstraints | LoadControlLimitListData, LoadControlEventListData | DeviceEnergyManagementMode cluster         | Defines operational or grid-imposed limits. |
| **Instruction**    | PEBC.Instruction              | LoadControlEventListData / ScheduleListData     | Energy Management Schedule cluster         | Setpoint or plan sent from HEMS to device. |
| **Status**         | InstructionStatusUpdate       | LoadControlStateListData, Result objects        | Attributes and telemetry                   | Status, measurement, or feedback confirming control. |
| **Measurement**    | PowerMeasurement / Forecast   | MeasurementListData                             | ElectricalMeasurement cluster              | Real-time or forecasted power data. |
| **Device Type**    | SystemDescription             | SPINE Actor Type                                | Device Type Library                        | Used for declaring capabilities and role binding. |
| **Topology**       | CEM ↔ RM over s2-ws-json      | SHIP + SPINE                                    | Fabric with Nodes, Admins, Clusters        | Communication structure between controller and devices. |
| **Transport**      | s2-ws-json (WebSocket/JSON)   | SHIP over TLS WebSocket                         | Matter IP stack (Thread/Wi-Fi/Ethernet)    | Underlying communication stack. |
| **Security Domain**| Session with authentication   | SHIP pairing and lifecycle management           | Fabric with ACLs and certificates          | Defines control authority and trust boundary. |
| **Use Case**       | ControlType + Forecast        | SPINE Use Case Model                            | Cluster interaction                        | E.g. grid capacity management, dynamic pricing, PV self-use. |
| **Interop Layer**  | S2 semantic model             | SPINE data model                                | Matter data model (Clusters)               | Standardized structure of control and feedback messages. |

---

## Notes

- This glossary is protocol-neutral. Each implementation should map to these concepts consistently.
- For detailed definitions, refer to the individual protocol specifications.
- Feel free to extend this glossary with additional domain-specific terms as needed during implementation.
