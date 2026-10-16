# EVSE Charging Use Cases

This document summarizes the three EV charging use cases currently represented in Home Assistant for the Matter EVSE.

If you are new to Matter, read [`matter-evse-onboarding.md`](matter-evse-onboarding.md) first. The use cases below assume that the EV charger has already been commissioned into Matter and that Home Assistant exposes its EVSE capabilities as entities.

How to read the mapping tables:

- `Source / Matter mapping` describes where the value or action comes from. It may be an external input such as ENTSO-E, IAMMETER, or OpenADR, or a Matter EVSE attribute/command.
- `Home Assistant entity` is the entity used by the automation.
- The main Matter control pattern in all three use cases is `switch.matter_evse_enable_charging`, which maps to `EnergyEvse.EnableCharging` (`0x02`) / `EnergyEvse.Disable` (`0x01`) and reads `EnergyEvse.SupplyState` (`0x0001`).

## Use Case 1: Price-Based Charging

Goal:
Charge when electricity is relatively cheap, and stop when electricity becomes expensive.

How it works:

- `sensor.price_level` is derived from `sensor.current_electricity_market_price` and `sensor.average_electricity_price`.
- When the price level becomes `VERY_CHEAP`, `CHEAP`, or `NORMAL`, Home Assistant turns on every charger whose entity ID matches `switch.*_enable_charging`.
- When the price level becomes `EXPENSIVE`, `VERY_EXPENSIVE`, or `EXTREMELY_EXPENSIVE`, Home Assistant turns those chargers off.

Main entity mapping:

| Role | Source / Matter mapping | Home Assistant entity |
| --- | --- | --- |
| Current electricity price input | ENTSO-E custom integration market price sensor | `sensor.current_electricity_market_price` |
| Average electricity price input | ENTSO-E custom integration average price sensor | `sensor.average_electricity_price` |
| Derived tariff level | Home Assistant template sensor derived from the two ENTSO-E price sensors above | `sensor.price_level` |
| Enable or disable EV charging | `EnergyEvse.EnableCharging` (`0x02`) / `EnergyEvse.Disable` (`0x01`); reads `EnergyEvse.SupplyState` (`0x0001`) | `switch.matter_evse_enable_charging` |

Configured automations:

- `price_based_charging_start`
- `price_based_charging_stop`

Behavior summary:

- Simple tariff-based control
- Good for scheduled low-cost charging
- Does not consider solar surplus or house load

## Use Case 2: Solar Surplus Charging

Goal:
Only charge when there is exported solar power available, and increase charging current according to the available surplus.

How it works:

- Home Assistant reads IAMMETER simulator data from `http://127.0.0.1:8080/monitorjson` using Basic Auth.
- The simulator provides three measured channels:
  - `A(Solar)` -> solar generation
  - `B(Grid)` -> grid import/export
  - `C(Load)` -> local load
- Template sensors expose these values as Home Assistant entities.
- `sensor.iammeter_solar_surplus_power` treats negative grid power as exported power and converts it to usable solar surplus.
- `sensor.evse_target_current_from_surplus` converts surplus power into a target charging current using a single-phase 230 V assumption.
- If the target current is greater than zero, Home Assistant:
  - updates `number.matter_evse_user_max_charge_current`
  - turns on `switch.matter_evse_enable_charging`
- If the target current is zero, Home Assistant turns charging off.

Main entity mapping:

| Role | Source / Matter mapping | Home Assistant entity |
| --- | --- | --- |
| IAMMETER simulator payload | IAMMETER simulator REST endpoint `http://127.0.0.1:8080/monitorjson` | `sensor.iammeter_simulator_api` |
| Solar generation measurement | Home Assistant template sensor derived from IAMMETER channel `A(Solar)` | `sensor.iammeter_solar_power` |
| Grid import/export measurement | Home Assistant template sensor derived from IAMMETER channel `B(Grid)` | `sensor.iammeter_grid_power` |
| Local load measurement | Home Assistant template sensor derived from IAMMETER channel `C(Load)` | `sensor.iammeter_load_power` |
| Calculated available surplus | Home Assistant template sensor derived from `sensor.iammeter_grid_power` export value | `sensor.iammeter_solar_surplus_power` |
| Calculated EVSE target current | Home Assistant template sensor derived from solar surplus and 230 V current conversion | `sensor.evse_target_current_from_surplus` |
| EVSE minimum charge current | `EnergyEvse.MinimumChargeCurrent` (`0x0006`) | `sensor.matter_evse_min_charge_current` |
| EVSE maximum charge current | `EnergyEvse.MaximumChargeCurrent` (`0x0007`) | `sensor.matter_evse_max_charge_current` |
| Set user charging limit | `EnergyEvse.UserMaximumChargeCurrent` (`0x0009`); best-effort write to `EnergyEvse.MaximumChargeCurrent` (`0x0007`) | `number.matter_evse_user_max_charge_current` |
| Enable or disable EV charging | `EnergyEvse.EnableCharging` (`0x02`) / `EnergyEvse.Disable` (`0x01`); reads `EnergyEvse.SupplyState` (`0x0001`) | `switch.matter_evse_enable_charging` |

Configured automation:

- `solar_surplus_evse_control`

Behavior summary:

- Dynamic solar-following control
- Attempts to match EV charging current to real-time surplus power
- Stops charging when available surplus is below minimum charging current

## Use Case 3: Limiting Peak Grid Demand

Goal:
Limit household grid import during DSO capacity-constrained periods, especially when forecasted grid demand is high.

How it works:

- An OpenADR VEN bridge receives capacity limit events from the VTN/DSO side and publishes them to Home Assistant over MQTT.
- `sensor.openadr_current_limit` exposes the received `IMPORT_CAPACITY_LIMIT` value in kW.
- Home Assistant compares the measured grid draw with the OpenADR limit.
- If grid draw is above the limit, Home Assistant turns off chargers whose entity ID matches `switch.*_enable_charging`.

Main entity mapping:

| Role | Source / Matter mapping | Home Assistant entity |
| --- | --- | --- |
| DSO/VTN capacity limit | OpenADR VEN bridge MQTT payload from VTN `IMPORT_CAPACITY_LIMIT` event | `sensor.openadr_current_limit` |
| Active interval capacity limit | OpenADR VEN bridge MQTT payload for the currently active event interval | `sensor.openadr_ven_openadr_active_limit` |
| Grid import/export measurement | Home Assistant template sensor derived from IAMMETER channel `B(Grid)` | `sensor.iammeter_grid_power` |
| Enable or disable EV charging | `EnergyEvse.EnableCharging` (`0x02`) / `EnergyEvse.Disable` (`0x01`); reads `EnergyEvse.SupplyState` (`0x0001`) | `switch.matter_evse_enable_charging` |

Configured automation:

- `openadr_limit_stop_charging`

Behavior summary:

- Basic OpenADR capacity-limit response
- Reduces EV charging load when grid import exceeds the received limit
- Currently acts as a charger shutoff rule, not a full HEMS import/export optimizer
- Does not yet coordinate other flexible assets such as batteries, heat buffers, or household loads

## Notes

- The current solar surplus calculation assumes `sensor.iammeter_grid_power < 0` means power is being exported to the grid.
- The current-to-power conversion assumes single-phase 230 V charging.
- If the installation is three-phase, the target current formula should be updated.
- The price-based, solar-surplus, and OpenADR limit automations can conflict because they all control `switch.matter_evse_enable_charging`.
- The OpenADR peak-demand rule is a partial implementation of DSO capacity-profile handling. It currently turns charging off when the limit is exceeded rather than dynamically reducing charging current or coordinating all local flexibility.

Recommended operating mode:

- Enable only one strategy at a time unless a higher-level coordination rule is added.
