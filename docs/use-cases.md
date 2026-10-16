<!--
SPDX-FileCopyrightText: ElaadNL

SPDX-License-Identifier: Apache-2.0
-->

# Key Use Cases

This document outlines the three core residential flexibility use cases of the Residential Flexibility initiative.

Connector implementations are expected to support these use cases.
These use cases are protocol-agnostic and serve to validate real-world applicability of the HEMS-to-device integration.

> For concrete implementation-level use cases against the vendored Matter server (Home Assistant automations driving the EVSE simulator), see [`evse-use-cases.md`](./evse-use-cases.md).
> For an analysis of how Matter 1.4 supports these use cases across different device types (EVSE, heat pumps, batteries, PV), see [`matter-feid-analysis.md`](./matter-feid-analysis.md).

---

## 1. Limiting Peak Grid Demand

**Goal:** Avoid grid congestion by respecting capacity limits provided by the DSO.

**How it works:**

- The DSO sends a capacity profile that defines the household’s allowed import/export limits over time.
- The HEMS receives this profile and ensures total energy usage remains within the allowed envelope.
- Flexible devices (e.g. EV chargers, batteries) are controlled accordingly to reduce peak load.

This use case helps alleviate local grid stress, especially during winter demand peaks.

---

## 2. Dynamic Tariff Optimization

**Goal:** Reduce household energy costs by shifting consumption to low-price periods.

**How it works:**

- The HEMS receives dynamic electricity price data (e.g. hourly spot prices).
- It schedules or shifts device operation to low-tariff periods.
- This can include charging a battery, pre-heating water, or delaying EV charging.

This use case leverages market signals to benefit consumers and reduce load during high-price events.

---

## 3. Maximizing Self-Consumption

**Goal:** Increase the use of self-generated solar energy within the home.

**How it works:**

- The HEMS monitors local PV production and current household load.
- When generation exceeds demand, it redirects surplus energy to flexible devices (e.g. battery or EV).
- This reduces grid feed-in and increases self-sufficiency.

This use case improves local efficiency and avoids overloading the grid during solar peaks.

---

## Implementation Note

These use cases are not tied to specific device types or protocols.
Each connector implementation should demonstrate that its HEMS-device communication supports control actions and telemetry needed to implement the use cases described above.
