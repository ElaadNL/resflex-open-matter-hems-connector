<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Matter analysis for residential flexibility FEIDs

The analysis covers:

- EV supply equipment (EVSE), which is the implemented reference path in this
  repository;
- heat pumps and water-heating loads;
- home batteries;
- photovoltaic (PV) inverters or PV generation endpoints.

The message-level mappings below use Matter cluster, attribute, command, and
event names. Device support still needs to be validated per product and firmware
because Matter device type support, optional cluster features, Home Assistant
mapping, and vendor implementation quality can differ.

## Executive summary

Matter 1.4.1 is useful for residential flexibility when a HEMS needs secure
local discovery, commissioning, device identity, live telemetry, subscriptions,
and standardized control of some device classes. EVSE is the strongest fit in
the current repository because Matter defines EVSE-specific clusters such as
`EnergyEvse` and `EnergyEvseMode`, and this project already validates that
surface through `desired.json`.

For non-EVSE FEIDs, Matter is promising but less complete. The generic
energy-management surface is mainly built around `DeviceEnergyManagement`,
`DeviceEnergyManagementMode`, `PowerTopology`, `ElectricalPowerMeasurement`,
`ElectricalEnergyMeasurement`, and device-specific mode/control clusters. These
clusters can express power limits, forecasts, opt-out state, power adjustment
capability, and electrical telemetry. They provide a common foundation for HEMS
control, but they do not yet provide the same device-specific depth for heat
pumps, home batteries, and PV that `EnergyEvse` provides for EV charging.

The recommended roadmap is therefore:

1. Treat EVSE as the reference implementation and conformance baseline.
2. Define a common FEID capability profile based on telemetry, power
   flexibility, forecast, opt-out, and mode support.
3. Add device-specific profiles for heat pump, battery, and PV using Matter
   clusters where they exist and explicit gap notes where they do not.
4. Add `desired-*.json` validation files and device snapshots for each FEID
   class.
5. Keep external grid, tariff, and solar-forecast inputs outside Matter unless a
   device exposes a standardized Matter mechanism for them.

## Scope and assumptions

This is an implementation-facing analysis, not a CSA certification statement. It
is based on:

- the EVSE implementation and validation files already present in this
  repository;
- the generated Matter cluster and device-type metadata included in the
  repository;
- Matter 1.4.x energy-management concepts relevant to residential flexibility.

The HEMS is treated as the Matter controller client or as a client of the Matter
Server. The FEID is treated as a Matter node that exposes server clusters and
accepts commands or writes through the Matter fabric.

## What Matter 1.4.1 can support

Matter can support the following parts of residential flexibility:

| Capability                     | Matter support                                                   | Relevance                                                                                             |
| ------------------------------ | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Secure local control           | Commissioning, fabric credentials, access control, subscriptions | Lets the HEMS control local devices without cloud dependency.                                         |
| Device discovery and structure | `Descriptor`, device types, endpoint lists, server cluster lists | Lets the HEMS discover which FEID capabilities are present.                                           |
| Device identity                | `BasicInformation`                                               | Lets the HEMS track vendor, product, firmware, serial number, and inventory data.                     |
| Live electrical telemetry      | `ElectricalPowerMeasurement`, `ElectricalEnergyMeasurement`      | Supports grid import/export, device consumption, production, and analytics where implemented.         |
| Power topology                 | `PowerTopology`                                                  | Helps relate electrical measurement endpoints to controllable endpoints.                              |
| Generic energy flexibility     | `DeviceEnergyManagement`                                         | Reports power limits, state, forecast, opt-out, and power adjustment capability.                      |
| Mode-based control             | `DeviceEnergyManagementMode`, device-specific mode clusters      | Lets the HEMS request operating modes where the device exposes them.                                  |
| EV charging control            | `EnergyEvse`, `EnergyEvseMode`                                   | Provides device-specific EVSE control, session state, targets, current limits, and EVSE events.       |
| HVAC and water heating control | `Thermostat`, `WaterHeaterManagement`, `WaterHeaterMode`         | Supports temperature setpoints, mode state, water-heater state, and load shifting by thermal storage. |

## What Matter 1.4.1 cannot fully support yet

The main gaps for the residential flexibility use cases are:

- Matter does not define the HEMS optimization algorithm. It provides device
  capabilities and control messages; the HEMS still decides how to optimize
  across assets.
- External inputs such as DSO capacity profiles, OpenADR events, dynamic
  tariffs, weather, and PV forecasts are not automatically Matter inputs in this
  repository.
- EVSE has a comparatively rich device-specific cluster model, but heat pump,
  battery, and PV support is less complete.
- In the local generated metadata, Heat Pump, Solar Power, and Battery Storage
  device types are identifiable device types, but they do not by themselves
  expose a full flexibility-control surface. They need additional clusters such
  as telemetry, thermostat, water heater, or generic device energy management.
- Generic energy-management commands are not universally present in current FEID
  products. In practice, each device should be validated for accepted command
  list, optional feature map, and effective runtime behavior.
- Home batteries need state-of-charge, capacity, import/export limits,
  charge/discharge commands, reserve policy, and cycle constraints. These are
  only partially represented by generic energy-management and
  electrical-measurement clusters unless a device implements a richer profile or
  vendor extension.
- PV needs generation telemetry, inverter state, curtailment/export limit
  control, and production forecasts. Matter can represent some of this through
  electrical measurement and generic energy management, but PV-specific
  curtailment semantics remain a gap.
- Heat pumps need thermal comfort constraints, buffer or domestic-hot-water
  state, compressor limitations, and defrost or lockout behavior. Matter can
  express thermostat and water-heater state, but a full flexibility contract
  still needs profiling.
- Event coverage outside EVSE is limited in the current repository. Most
  non-EVSE workflows should expect attribute updates and command responses
  rather than rich domain events.

## Common Matter FEID capability model

For all FEIDs, the HEMS should first build a common capability model before
applying device-specific logic.

| HEMS question                            | Matter message to inspect                                                                                                                                                                            | Device-side meaning                                                             |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| What device is this?                     | Read `Descriptor.DeviceTypeList`, `Descriptor.ServerList`, `BasicInformation.*`                                                                                                                      | The device declares its type, endpoints, clusters, and identity.                |
| Which endpoint is controllable?          | Read `Descriptor.PartsList`, `Descriptor.ServerList`, `PowerTopology.AvailableEndpoints`                                                                                                             | The device exposes functional and electrical endpoint topology.                 |
| What is the live power?                  | Subscribe to `ElectricalPowerMeasurement.ActivePower`, `Voltage`, `ActiveCurrent`, `Frequency`                                                                                                       | The device reports live electrical behavior.                                    |
| How much energy has moved?               | Subscribe to `ElectricalEnergyMeasurement.CumulativeEnergyImported`, `CumulativeEnergyExported`, `PeriodicEnergyImported`, `PeriodicEnergyExported`                                                  | The device reports imported/exported energy counters where available.           |
| Can the device change power?             | Read `DeviceEnergyManagement.AbsMinPower`, `AbsMaxPower`, `PowerAdjustmentCapability`                                                                                                                | The device declares its minimum, maximum, and adjustable power envelope.        |
| Can the device generate?                 | Read `DeviceEnergyManagement.ESACanGenerate`                                                                                                                                                         | The device declares whether it can export or generate energy.                   |
| What is the planned behavior?            | Read `DeviceEnergyManagement.Forecast`                                                                                                                                                               | The device provides a forecast or planned operating sequence.                   |
| Can the user override flexibility?       | Read `DeviceEnergyManagement.OptOutState`                                                                                                                                                            | The device reports whether local user preference blocks or limits HEMS control. |
| Which mode is active?                    | Read `DeviceEnergyManagementMode.SupportedModes`, `CurrentMode`                                                                                                                                      | The device declares and reports energy-management modes.                        |
| How should the HEMS request flexibility? | Send supported `DeviceEnergyManagement` commands such as `PowerAdjustRequest`, `StartTimeAdjustRequest`, `ModifyForecastRequest`, `RequestConstraintBasedForecast`, or send device-specific commands | The device accepts or rejects a power, schedule, or constraint request.         |

The HEMS should subscribe to attributes used for control decisions. A
polling-only implementation will miss fast changes in opt-out state, live power,
fault state, or active operating mode.

## FEID readiness by device class

| FEID class   | Current Matter fit  | Practical interpretation                                                                                                                                                    |
| ------------ | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| EVSE         | Strong              | Use `EnergyEvse`, `EnergyEvseMode`, `DeviceEnergyManagement`, and electrical measurement clusters. This is the current repository reference.                                |
| Heat pump    | Partial             | Use thermostat and water-heater semantics where available. Add `DeviceEnergyManagement` for explicit flexibility. A heat-pump device type alone is not enough.              |
| Home battery | Partial to immature | Use electrical telemetry and generic energy management. Battery-specific state-of-charge and reserve semantics need a profile, vendor extension, or future Matter support.  |
| PV           | Partial to immature | Use electrical telemetry for generation/export and generic energy management for curtailment if supported. PV-specific inverter and forecast semantics need more profiling. |

## FEID-specific analysis

### EVSE

EVSE is the current reference FEID for this repository.

| Message type          | Matter messages                                                                                                                                      |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity and topology | `Descriptor.*`, `BasicInformation.*`, `PowerSource.*`, `PowerTopology.*`                                                                             |
| Live telemetry        | `ElectricalPowerMeasurement.ActivePower`, `Voltage`, `ActiveCurrent`, `Frequency`; `ElectricalEnergyMeasurement.*Imported`, `*Exported`              |
| Energy management     | `DeviceEnergyManagement.ESAType`, `ESACanGenerate`, `ESAState`, `AbsMinPower`, `AbsMaxPower`, `PowerAdjustmentCapability`, `Forecast`, `OptOutState` |
| EVSE state            | `EnergyEvse.State`, `SupplyState`, `FaultState`, `CircuitCapacity`, `MinimumChargeCurrent`, `MaximumChargeCurrent`, `UserMaximumChargeCurrent`       |
| EVSE targets          | `EnergyEvse.NextChargeStartTime`, `NextChargeTargetTime`, `NextChargeRequiredEnergy`, `NextChargeTargetSoC`                                          |
| EVSE commands         | `EnergyEvse.Disable`, `EnableCharging`, `SetTargets`, `GetTargets`, `ClearTargets`, `EnergyEvseMode.ChangeToMode`                                    |
| EVSE events           | `EVConnected`, `EVNotDetected`, `EnergyTransferStarted`, `EnergyTransferStopped`, `Fault`, `RFID`                                                    |

**Assessment:** suitable for all three use cases with the current project scope.
The main remaining work is better cross-device coordination so price,
solar-surplus, and grid-limit automations do not conflict.

### Heat pumps and water heating

Matter has thermostat and water-heater capabilities that can be used for thermal
flexibility. The local generated metadata also contains a Heat Pump device type,
but that type alone only identifies the device; it does not provide the full
flexibility surface.

| Message type          | Matter messages                                                                                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Identity and topology | `Descriptor.*`, `BasicInformation.*`                                                                                                                                           |
| Thermal state         | `Thermostat.LocalTemperature`, `OutdoorTemperature`, `PIHeatingDemand`, `ThermostatRunningState`                                                                               |
| Comfort limits        | `Thermostat.MinHeatSetpointLimit`, `MaxHeatSetpointLimit`, `MinCoolSetpointLimit`, `MaxCoolSetpointLimit`                                                                      |
| Control state         | `Thermostat.SystemMode`, `ControlSequenceOfOperation`, `OccupiedHeatingSetpoint`, `OccupiedCoolingSetpoint`, schedule and hold attributes where supported                      |
| Water-heater state    | `WaterHeaterManagement.HeatDemand`, `TankVolume`, `EstimatedHeatRequired`, `TankPercentage`, `BoostState`                                                                      |
| Water-heater mode     | `WaterHeaterMode.SupportedModes`, `CurrentMode`, `StartUpMode`, `OnMode`                                                                                                       |
| Generic flexibility   | `DeviceEnergyManagement.*`, `DeviceEnergyManagementMode.*` when exposed                                                                                                        |
| Commands and writes   | Write thermostat setpoints and modes; use thermostat setpoint commands where supported; use `WaterHeaterMode.ChangeToMode`; use `DeviceEnergyManagement` commands when exposed |

**Assessment:** suitable for tariff shifting and self-consumption through
preheating or delayed operation, but peak-demand reduction must respect comfort
constraints. A WP2 roadmap should define a heat-pump flexibility profile that
combines thermostat comfort data with generic energy-management power limits and
forecasts.

### Home batteries

Matter includes a Battery Storage device type in the local metadata, but the
type alone does not define a complete home-battery control model. Batteries need
more than generic telemetry: the HEMS needs state of charge, capacity,
charge/discharge limits, reserve requirements, export constraints, and user
preferences.

| Message type          | Matter messages                                                                                                                                      |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity and topology | `Descriptor.*`, `BasicInformation.*`, `PowerTopology.*`                                                                                              |
| Live power            | `ElectricalPowerMeasurement.ActivePower`, `Voltage`, `ActiveCurrent`, `Frequency`                                                                    |
| Energy counters       | `ElectricalEnergyMeasurement.CumulativeEnergyImported`, `CumulativeEnergyExported`, `PeriodicEnergyImported`, `PeriodicEnergyExported`               |
| Generic flexibility   | `DeviceEnergyManagement.ESAType`, `ESACanGenerate`, `ESAState`, `AbsMinPower`, `AbsMaxPower`, `PowerAdjustmentCapability`, `Forecast`, `OptOutState` |
| Modes                 | `DeviceEnergyManagementMode.SupportedModes`, `CurrentMode`, `ChangeToMode`                                                                           |
| Candidate controls    | `PowerAdjustRequest`, `StartTimeAdjustRequest`, `RequestConstraintBasedForecast`, `ModifyForecastRequest`, mode changes where supported              |

**Assessment:** useful for telemetry and generic power dispatch if the device
implements the energy-management cluster fully. Not yet sufficient as a complete
standard battery interface unless the project defines required attributes, sign
conventions, reserve behavior, and validation tests.

### PV and inverters

Matter includes a Solar Power device type in the local metadata, but the type
alone does not define a full PV inverter or curtailment profile. PV is often a
measurement-first integration unless the inverter exposes controllable power
adjustment.

| Message type                   | Matter messages                                                                                                               |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Identity and topology          | `Descriptor.*`, `BasicInformation.*`, `PowerTopology.*`                                                                       |
| Live generation/export         | `ElectricalPowerMeasurement.ActivePower`, `Voltage`, `ActiveCurrent`, `Frequency`, `PowerFactor`                              |
| Energy counters                | `ElectricalEnergyMeasurement.CumulativeEnergyExported`, `PeriodicEnergyExported`, imported counters where relevant            |
| Generic generation flexibility | `DeviceEnergyManagement.ESACanGenerate`, `AbsMinPower`, `AbsMaxPower`, `PowerAdjustmentCapability`, `Forecast`, `OptOutState` |
| Candidate controls             | `PowerAdjustRequest`, `RequestConstraintBasedForecast`, or mode changes for curtailment/export limiting where supported       |

**Assessment:** suitable for observing generation and export, and potentially
for curtailment if generic energy management is implemented. It is not yet a
complete PV inverter profile for production forecasting, MPPT/inverter state,
grid-code behavior, or standardized export-limit contracts.

## Roadmap beyond EVSE

### Phase 1: define a common FEID profile

Create a repository-level FEID profile that every device class can be tested
against:

- identity: `Descriptor`, `BasicInformation`;
- topology: `PowerTopology` where applicable;
- telemetry: `ElectricalPowerMeasurement`, `ElectricalEnergyMeasurement`;
- flexibility: `DeviceEnergyManagement`, `DeviceEnergyManagementMode`;
- user override: `OptOutState`;
- validation artifacts: `desired-common-feid.json`, example snapshots, and
  output examples.

### Phase 2: harden the EVSE reference

Extend the EVSE validation and examples:

- keep `desired.json` as the EVSE baseline or rename it to `desired-evse.json`;
- add expected telemetry and event examples for each use case;
- document sign conventions and unit conversions;
- add conflict-resolution guidance for simultaneous tariff, solar, and
  grid-limit strategies.

### Phase 3: add heat pump and water-heater profile

Define a heat-pump profile that combines thermal control and energy flexibility:

- thermostat state and setpoint requirements;
- water-heater state and mode requirements where domestic hot water is part of
  the device;
- comfort-bound constraints for peak-demand and tariff optimization;
- optional `DeviceEnergyManagement` requirements for explicit power flexibility.

### Phase 4: add battery profile

Define a battery profile that resolves the current generic-control gaps:

- sign convention for charge and discharge power;
- state-of-charge and usable-capacity representation;
- reserve and backup constraints;
- allowed import/export envelope;
- mode mapping for charge, discharge, idle, reserve, and automatic operation.

### Phase 5: add PV profile

Define a PV profile focused on telemetry first and control second:

- generation and export telemetry requirements;
- inverter identity and topology;
- optional curtailment/export-limit control through generic energy management;
- production forecast handling where available.

### Phase 6: add HEMS-side orchestration tests

Add integration tests or scenario documentation that verifies:

- peak-demand response across more than one FEID;
- tariff optimization with scheduled and interruptible devices;
- self-consumption using PV, battery, EVSE, and heat pump together;
- user opt-out precedence;
- reconnect and stale-state handling;
- conflict resolution when multiple strategies request incompatible actions.
