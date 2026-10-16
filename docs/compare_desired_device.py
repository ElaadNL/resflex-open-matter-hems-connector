#!/usr/bin/env python3
"""
Compare Matter device data with desired endpoints/clusters/attributes.

Reads desired.json and device node files (with attributes), then outputs
for each device: what's present and what's missing, with human-readable names.
Also checks ha_mapping.json to show which items have HA entity coverage.

Output formats: txt (readable), json (structured), csv (Cluster Id, Type, Id,
Description, Matter ready, HA ready). Use --format csv or --format both.

Usage:
  python3 compare_desired_device.py --input-dir matter_snapshots
  python3 compare_desired_device.py --input-file matter_snapshots/20260130-041029/node_52.json
  python3 compare_desired_device.py --input-dir . --output-dir comparison_results
  python3 compare_desired_device.py --input-dir . --format csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any


def safe_cli_path(path_like: str | Path) -> Path:
    """Resolve a CLI-provided path, rejecting any '..' traversal segments."""
    candidate = Path(path_like).expanduser()
    if any(part == ".." for part in candidate.parts):
        raise ValueError(f"Path traversal ('..') is not allowed: {path_like}")
    return candidate.resolve(strict=False)


# Common Matter cluster and attribute names for human-readable output
CLUSTER_NAMES: dict[int, str] = {
    29: "Descriptor",
    31: "AccessControl",
    40: "BasicInformation",
    42: "OtaSoftwareUpdateRequestor",
    47: "PowerSource",
    48: "GeneralCommissioning",
    49: "NetworkCommissioning",
    51: "GeneralDiagnostics",
    60: "AdministratorCommissioning",
    62: "OperationalCredentials",
    63: "GroupKeyManagement",
    144: "ElectricalPowerMeasurement",
    152: "DeviceEnergyManagement",
    153: "EnergyEvse",
    159: "DeviceEnergyManagementMode",
    156: "PowerTopology",
    157: "EnergyEvseMode",
}

DESCRIPTOR_ATTR_NAMES: dict[int, str] = {
    0: "deviceTypeList",
    1: "serverList",
    2: "clientList",
    3: "partsList",
}

# Matter standard attribute IDs for cluster metadata
GENERATED_COMMAND_LIST_ATTR = 65528  # 0xFFF8 (lists response/generated command IDs)
ACCEPTED_COMMAND_LIST_ATTR = 65529  # 0xFFF9 (lists command IDs server accepts)
EVENT_LIST_ATTR = 65530  # 0xFFF2 (lists event IDs cluster supports)


def hex_to_int(val: str | int) -> int:
    """Convert hex string or int to int."""
    if isinstance(val, str) and val.lower().startswith("0x"):
        return int(val, 16)
    return int(val)


def to_hex(val: int, width: int = 4) -> str:
    """Format int as hex string (e.g., 29 -> 0x001D)."""
    return f"0x{val:0{width}X}"


def get_cluster_name(cluster_id: int) -> str:
    """Return human-readable cluster name."""
    return CLUSTER_NAMES.get(cluster_id, f"Cluster_0x{cluster_id:04X}")


def get_attribute_name(
    cluster_id: int, attr_id: int, custom_names: dict[str, str] | None
) -> str:
    """Return human-readable attribute name."""
    if custom_names:
        key = f"0x{attr_id:04X}"
        if key in custom_names:
            return custom_names[key]
    if cluster_id == 29:
        return DESCRIPTOR_ATTR_NAMES.get(attr_id, f"Attr_0x{attr_id:04X}")
    return f"Attr_0x{attr_id:04X}"


def is_generated_command_name(command_name: str) -> bool:
    """Return True for generated/response commands exposed via GeneratedCommandList."""
    return command_name.endswith("Response")


def extract_endpoints(attributes: dict[str, Any] | list[Any]) -> list[int]:
    """Extract endpoint IDs from device attributes.

    Supports attributes as dict (path string -> value) or list of path entries.
    Path format: "0/29/0" or "EP2 / PowerSource / Attr".
    """
    eps: set[int] = set()

    def add_ep_from_path(path: Any) -> None:
        if not isinstance(path, str):
            return
        parts = path.split("/")
        if len(parts) >= 1:
            first = parts[0].strip()
            if first.isdigit():
                eps.add(int(first))
            elif first.upper().startswith("EP") and first[2:].strip().isdigit():
                eps.add(int(first[2:].strip()))

    if isinstance(attributes, dict):
        for path in attributes:
            add_ep_from_path(path)
    elif isinstance(attributes, list):
        for entry in attributes:
            if isinstance(entry, dict):
                add_ep_from_path(entry.get("path") or entry.get("attribute_path"))
            elif isinstance(entry, str):
                add_ep_from_path(entry)
    # Also include partsList from endpoint 0 if available (dict format only)
    if isinstance(attributes, dict):
        parts_list = attributes.get("0/29/3")
        if isinstance(parts_list, list) and all(isinstance(x, int) for x in parts_list):
            eps.update(parts_list)
            eps.add(0)
    return sorted(eps)


def load_desired(desired_path: Path) -> dict[str, Any]:
    """Load and parse desired.json."""
    safe_path = safe_cli_path(desired_path)
    data = json.loads(safe_path.read_text(encoding="utf-8"))
    # Normalize cluster IDs and attr IDs to int for comparison
    normalized: dict[int, dict[str, Any]] = {}
    for cluster_hex, spec in data.get("check_on_all_endpoints", {}).items():
        cluster_id = hex_to_int(cluster_hex)
        attrs = spec.get("attributes", [])
        attr_ids = [hex_to_int(a) for a in attrs]
        cmd_ids = [hex_to_int(c) for c in spec.get("commands", [])]
        cmd_names = {
            hex_to_int(k): v for k, v in (spec.get("command_names") or {}).items()
        }
        evt_ids = [hex_to_int(e) for e in spec.get("events", [])]
        evt_names = {
            hex_to_int(k): v for k, v in (spec.get("event_names") or {}).items()
        }
        normalized[cluster_id] = {
            "name": spec.get("name", get_cluster_name(cluster_id)),
            "attribute_ids": attr_ids,
            "attribute_names": {
                hex_to_int(k): v for k, v in (spec.get("attribute_names") or {}).items()
            },
            "command_ids": cmd_ids,
            "command_names": cmd_names,
            "event_ids": evt_ids,
            "event_names": evt_names,
        }
    return {"clusters": normalized, "description": data.get("description", "")}


def load_ha_mapping(mapping_path: Path) -> dict[str, set[tuple[int, int]]]:
    """Load ha_mapping.json into lookup sets for quick membership checks.

    Returns dict with keys 'attrs', 'cmds', 'events'.
    Each value is a set of (cluster_id, item_id) tuples.
    Also stores the raw entries in 'attrs_detail', 'cmds_detail', 'events_detail'
    as dicts mapping (cluster_id, item_id) -> {"platform": ..., "entity": ...}.
    """
    result: dict[str, Any] = {
        "attrs": set(),
        "cmds": set(),
        "events": set(),
        "attrs_detail": {},
        "cmds_detail": {},
        "events_detail": {},
    }
    try:
        safe_path = safe_cli_path(mapping_path)
    except ValueError:
        return result
    if not safe_path.exists():
        return result
    try:
        data = json.loads(safe_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return result
    for entry in data.get("attributes", []):
        cid = hex_to_int(entry["cluster"])
        aid = hex_to_int(entry["id"])
        result["attrs"].add((cid, aid))
        result["attrs_detail"][(cid, aid)] = {
            "platform": entry.get("platform", ""),
            "entity": entry.get("entity", ""),
            "entity_class": entry.get("entity_class", ""),
        }
    for entry in data.get("commands", []):
        cid = hex_to_int(entry["cluster"])
        cmd_id = hex_to_int(entry["id"])
        result["cmds"].add((cid, cmd_id))
        result["cmds_detail"][(cid, cmd_id)] = {
            "platform": entry.get("platform", ""),
            "entity": entry.get("entity", ""),
            "entity_class": entry.get("entity_class", ""),
        }
    for entry in data.get("events", []):
        cid = hex_to_int(entry["cluster"])
        eid = hex_to_int(entry["id"])
        result["events"].add((cid, eid))
        result["events_detail"][(cid, eid)] = {
            "platform": entry.get("platform", ""),
            "entity": entry.get("entity", ""),
            "entity_class": entry.get("entity_class", ""),
        }
    return result


def load_device_file(path: Path) -> dict[str, Any] | None:
    """Load a single device node file. Returns dict with node_id and attributes.

    Supports:
    - matter_snapshots format: { "node_id": N, "attributes": {...} }
    - HA Matter diagnostics: { "data": { "node": { "node_id": N, "attributes": {...} } } }
    """
    try:
        safe_path = safe_cli_path(path)
        data = json.loads(safe_path.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError, OSError):
        return None
    # HA diagnostics format
    if "data" in data and "node" in data["data"]:
        node = data["data"]["node"]
        if "attributes" in node:
            return {
                "node_id": node.get("node_id", "unknown"),
                "attributes": node["attributes"],
                "source": str(safe_path),
            }
    # matter_snapshots / direct node format
    if "attributes" in data:
        return {
            "node_id": data.get("node_id", "unknown"),
            "attributes": data["attributes"],
            "source": str(safe_path),
        }
    return None


def find_device_files(input_path: Path) -> list[Path]:
    """Find all device JSON files (with attributes) under input path."""
    files: list[Path] = []
    if input_path.is_file():
        if load_device_file(input_path):
            return [input_path]
        return []
    # Search for node_*.json or any JSON with node_id + attributes
    files = [p for p in input_path.rglob("*.json") if load_device_file(p)]
    return sorted(set(files))


def fetch_node_files_from_matter_server(
    ws_url: str, out_dir: Path, node_id: int | None = None, timeout_s: float = 15.0
) -> list[Path]:
    """Fetch commissioned nodes from python-matter-server and save to JSON files.

    The saved files contain a MatterNodeData dict with at least 'node_id' and
    'attributes', which can be consumed by load_device_file().
    """
    import asyncio  # noqa: PLC0415

    async def _run() -> list[Path]:
        try:
            import aiohttp  # type: ignore[import-not-found]  # noqa: PLC0415

            from matter_server.client.client import (  # noqa: PLC0415
                MatterClient,  # type: ignore[import-not-found]
            )
            from matter_server.common.models import (  # noqa: PLC0415
                APICommand,  # type: ignore[import-not-found]
            )
        except ImportError as err:  # pragma: no cover
            raise RuntimeError(
                "Cannot import python-matter-server client dependencies. "
                "Install Home Assistant requirements (python-matter-server) first."
            ) from err

        out_dir.mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240

        async with aiohttp.ClientSession() as session:
            async with MatterClient(ws_url, session) as client:
                await asyncio.wait_for(client.connect(), timeout=timeout_s)
                # Prefer lightweight commands over full diagnostics dump to avoid timeouts.
                if node_id is not None:
                    node = await asyncio.wait_for(
                        client.send_command(APICommand.GET_NODE, node_id=node_id),
                        timeout=timeout_s,
                    )
                    nodes = [node]
                else:
                    nodes = await asyncio.wait_for(
                        client.send_command(APICommand.GET_NODES),
                        timeout=timeout_s,
                    )

        written: list[Path] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            nid = node.get("node_id")
            if not isinstance(nid, int):
                continue
            if node_id is not None and nid != node_id:
                continue
            fp = out_dir / f"node_{nid}.json"
            fp.write_text(
                json.dumps(node, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            written.append(fp)
        return written

    return asyncio.run(_run())


def compare_device(
    device: dict[str, Any],
    desired: dict[str, Any],
    ha_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare one device against desired spec. Return present/missing with names.

    An attribute is considered PRESENT if ANY endpoint has it (cluster+attr exists
    somewhere on the device). We do not require every endpoint to have it.
    ha_map is the output of load_ha_mapping(); when provided, each entry gets
    an 'ha_mapped' flag and optional 'ha_platform'/'ha_entity' detail.
    """
    if ha_map is None:
        ha_map = {
            "attrs": set(),
            "cmds": set(),
            "events": set(),
            "attrs_detail": {},
            "cmds_detail": {},
            "events_detail": {},
        }

    attributes = device.get("attributes", {})
    endpoints = extract_endpoints(attributes)
    clusters_spec = desired.get("clusters", {})

    present: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for cluster_id, spec in clusters_spec.items():
        cluster_name = spec.get("name", get_cluster_name(cluster_id))
        attr_names = spec.get("attribute_names", {})

        for attr_id in spec.get("attribute_ids", []):
            attr_name = attr_names.get(attr_id) or get_attribute_name(
                cluster_id, attr_id, None
            )
            if not attr_name and cluster_id == 29:
                attr_name = DESCRIPTOR_ATTR_NAMES.get(attr_id, f"0x{attr_id:04X}")
            if not attr_name:
                attr_name = f"0x{attr_id:04X}"

            endpoints_with_attr: list[int] = []
            for ep_id in endpoints:
                path = f"{ep_id}/{cluster_id}/{attr_id}"
                if path in attributes:
                    endpoints_with_attr.append(ep_id)

            ha_key = (cluster_id, attr_id)
            ha_matched = ha_key in ha_map["attrs"]
            ha_detail = ha_map["attrs_detail"].get(ha_key, {})

            entry: dict[str, Any] = {
                "type": "attr",
                "cluster_id": cluster_id,
                "cluster_id_hex": to_hex(cluster_id),
                "cluster_name": cluster_name,
                "attribute_id": attr_id,
                "attribute_id_hex": to_hex(attr_id),
                "attribute_name": attr_name,
                "endpoints": endpoints_with_attr,
                "endpoints_hex": [to_hex(ep) for ep in endpoints_with_attr],
                "ha_mapped": ha_matched,
            }
            if ha_matched:
                entry["ha_platform"] = ha_detail.get("platform", "")
                entry["ha_entity"] = ha_detail.get("entity", "")
                entry["ha_entity_class"] = ha_detail.get("entity_class", "")

            if endpoints_with_attr:
                present.append(entry)
            else:
                missing.append(entry)

        for cmd_id in spec.get("command_ids", []):
            cmd_name = spec.get("command_names", {}).get(cmd_id, f"Cmd_0x{cmd_id:04X}")
            endpoints_with_cmd: list[int] = []
            command_list_attr = (
                GENERATED_COMMAND_LIST_ATTR
                if is_generated_command_name(cmd_name)
                else ACCEPTED_COMMAND_LIST_ATTR
            )
            for ep_id in endpoints:
                acl_path = f"{ep_id}/{cluster_id}/{command_list_attr}"
                acl_value = attributes.get(acl_path)
                if isinstance(acl_value, list) and cmd_id in acl_value:
                    endpoints_with_cmd.append(ep_id)

            ha_key = (cluster_id, cmd_id)
            ha_matched = ha_key in ha_map["cmds"]
            ha_detail = ha_map["cmds_detail"].get(ha_key, {})

            cmd_entry: dict[str, Any] = {
                "type": "cmd",
                "cluster_id": cluster_id,
                "cluster_id_hex": to_hex(cluster_id),
                "cluster_name": cluster_name,
                "command_id": cmd_id,
                "command_id_hex": to_hex(cmd_id),
                "command_name": cmd_name,
                "endpoints": endpoints_with_cmd,
                "endpoints_hex": [to_hex(ep) for ep in endpoints_with_cmd],
                "ha_mapped": ha_matched,
            }
            if ha_matched:
                cmd_entry["ha_platform"] = ha_detail.get("platform", "")
                cmd_entry["ha_entity"] = ha_detail.get("entity", "")
                cmd_entry["ha_entity_class"] = ha_detail.get("entity_class", "")

            if endpoints_with_cmd:
                present.append(cmd_entry)
            else:
                missing.append(cmd_entry)

        for evt_id in spec.get("event_ids", []):
            evt_name = spec.get("event_names", {}).get(evt_id, f"Event_0x{evt_id:04X}")
            endpoints_with_evt: list[int] = []
            for ep_id in endpoints:
                evt_list_path = f"{ep_id}/{cluster_id}/{EVENT_LIST_ATTR}"
                evt_list_value = attributes.get(evt_list_path)
                if isinstance(evt_list_value, list) and evt_id in evt_list_value:
                    endpoints_with_evt.append(ep_id)

            ha_key = (cluster_id, evt_id)
            ha_matched = ha_key in ha_map["events"]
            ha_detail = ha_map["events_detail"].get(ha_key, {})

            evt_entry: dict[str, Any] = {
                "type": "evt",
                "cluster_id": cluster_id,
                "cluster_id_hex": to_hex(cluster_id),
                "cluster_name": cluster_name,
                "event_id": evt_id,
                "event_id_hex": to_hex(evt_id),
                "event_name": evt_name,
                "endpoints": endpoints_with_evt,
                "endpoints_hex": [to_hex(ep) for ep in endpoints_with_evt],
                "ha_mapped": ha_matched,
            }
            if ha_matched:
                evt_entry["ha_platform"] = ha_detail.get("platform", "")
                evt_entry["ha_entity"] = ha_detail.get("entity", "")
                evt_entry["ha_entity_class"] = ha_detail.get("entity_class", "")

            if endpoints_with_evt:
                present.append(evt_entry)
            else:
                missing.append(evt_entry)

    node_id = device.get("node_id")
    ha_present_count = sum(1 for e in present if e.get("ha_mapped"))
    ha_missing_from_present = sum(1 for e in present if not e.get("ha_mapped"))
    return {
        "node_id": node_id,
        "node_id_hex": to_hex(node_id, width=4)
        if isinstance(node_id, int)
        else f"{node_id}",
        "source": device.get("source", ""),
        "endpoints_found": endpoints,
        "endpoints_found_hex": [to_hex(ep) for ep in endpoints],
        "present": present,
        "missing": missing,
        "summary": {
            "total_desired": len(present) + len(missing),
            "present_count": len(present),
            "missing_count": len(missing),
            "ha_mapped_count": ha_present_count,
            "ha_unmapped_present_count": ha_missing_from_present,
        },
    }


def _ha_tag(entry: dict[str, Any]) -> str:
    """Return HA mapping tag string for a single entry."""
    if entry.get("ha_mapped"):
        platform = entry.get("ha_platform", "")
        return f"HA:yes ({platform})" if platform else "HA:yes"
    return "HA:no"


def _item_label(entry: dict[str, Any]) -> str:
    """Return '[Type] Cluster (hex) | Name (hex)' label for an entry."""
    cname = entry["cluster_name"]
    chex = entry["cluster_id_hex"]
    if entry.get("type") == "cmd":
        return f"[Cmd]  {cname} ({chex}) | {entry['command_name']} ({entry['command_id_hex']})"
    if entry.get("type") == "evt":
        return (
            f"[Evt]  {cname} ({chex}) | {entry['event_name']} ({entry['event_id_hex']})"
        )
    return f"[Attr] {cname} ({chex}) | {entry['attribute_name']} ({entry['attribute_id_hex']})"


def format_result_text(result: dict[str, Any], desired_desc: str) -> str:
    """Format comparison result as human-readable text (all hex).

    Layout: Matter results on top, HA mapping analysis below.
    """
    summary = result["summary"]

    # --- Part 1: Matter device comparison ---
    lines = [
        "=" * 80,
        "Part 1 — Matter Device Comparison  (device 有/缺)",
        "=" * 80,
        f"Device Node ID : {result.get('node_id_hex', result['node_id'])}",
        f"Source         : {result.get('source', 'N/A')}",
        f"Desired spec   : {desired_desc}",
        f"Endpoints found: {result.get('endpoints_found_hex', result['endpoints_found'])}",
        "",
        f"Matter Summary: {summary['present_count']} present, "
        f"{summary['missing_count']} missing "
        f"(of {summary['total_desired']} desired)",
        "",
        "-" * 80,
        "PRESENT (Matter 有):",
        "-" * 80,
    ]

    for p in result["present"]:
        eps = p.get("endpoints_hex", p.get("endpoints", []))
        label = _item_label(p)
        lines.append(f"  {label} → ep {eps}")

    lines.extend(
        [
            "",
            "-" * 80,
            "MISSING (Matter 缺):",
            "-" * 80,
        ]
    )

    lines.extend(f"  {_item_label(m)}" for m in result["missing"])

    # --- Part 2: HA entity mapping analysis ---
    ha_mapped_count = summary.get("ha_mapped_count", 0)
    ha_unmapped_count = summary.get("ha_unmapped_present_count", 0)

    present_ha_yes = [e for e in result["present"] if e.get("ha_mapped")]
    present_ha_no = [e for e in result["present"] if not e.get("ha_mapped")]
    missing_ha_yes = [e for e in result["missing"] if e.get("ha_mapped")]
    missing_ha_no = [e for e in result["missing"] if not e.get("ha_mapped")]

    lines.extend(
        [
            "",
            "",
            "=" * 80,
            "Part 2 — Home Assistant Entity Mapping  (HA 有/缺)",
            "=" * 80,
            f"HA Summary (of {summary['present_count']} Matter-present items):",
            f"  HA mapped   : {ha_mapped_count}",
            f"  HA unmapped : {ha_unmapped_count}",
            "",
            "-" * 80,
            f"Matter:present + HA:yes  ({len(present_ha_yes)})  — device 有 + HA 有 mapping",
            "-" * 80,
        ]
    )
    for e in present_ha_yes:
        eps = e.get("endpoints_hex", e.get("endpoints", []))
        platform = e.get("ha_platform", "")
        entity = e.get("ha_entity", "")
        label = _item_label(e)
        ha_info = f"[{platform}] {entity}" if platform else ""
        lines.append(f"  {label}  →  {ha_info}")

    lines.extend(
        [
            "",
            "-" * 80,
            f"Matter:present + HA:no   ({len(present_ha_no)})  — device 有, 但 HA 缺 mapping ⚠",
            "-" * 80,
        ]
    )
    for e in present_ha_no:
        eps = e.get("endpoints_hex", e.get("endpoints", []))
        lines.append(f"  {_item_label(e)}  →  ep {eps}")

    lines.extend(
        [
            "",
            "-" * 80,
            f"Matter:missing + HA:yes  ({len(missing_ha_yes)})  — device 缺, 但 HA 有 mapping",
            "-" * 80,
        ]
    )
    if missing_ha_yes:
        for e in missing_ha_yes:
            platform = e.get("ha_platform", "")
            entity = e.get("ha_entity", "")
            ha_info = f"[{platform}] {entity}" if platform else ""
            lines.append(f"  {_item_label(e)}  →  {ha_info}")
    else:
        lines.append("  (none)")

    lines.extend(
        [
            "",
            "-" * 80,
            f"Matter:missing + HA:no   ({len(missing_ha_no)})  — device 缺 + HA 缺 mapping",
            "-" * 80,
        ]
    )
    if missing_ha_no:
        lines.extend(f"  {_item_label(e)}" for e in missing_ha_no)
    else:
        lines.append("  (none)")

    lines.append("")
    return "\n".join(lines)


def _entry_to_csv_row(entry: dict[str, Any], matter_ready: bool) -> dict[str, str]:
    """Convert one compare result entry to CSV row dict."""
    cluster_id_hex = entry.get("cluster_id_hex", to_hex(entry.get("cluster_id", 0)))
    t = entry.get("type", "attr")
    if t == "cmd":
        type_label = "Cmd"
        item_id_hex = entry.get("command_id_hex", to_hex(entry.get("command_id", 0)))
        description = entry.get("command_name", "")
    elif t == "evt":
        type_label = "Evt"
        item_id_hex = entry.get("event_id_hex", to_hex(entry.get("event_id", 0)))
        description = entry.get("event_name", "")
    else:
        type_label = "Attr"
        item_id_hex = entry.get(
            "attribute_id_hex", to_hex(entry.get("attribute_id", 0))
        )
        description = entry.get("attribute_name", "")
    ha_ready = entry.get("ha_mapped", False)
    entity_class = entry.get("ha_entity_class", "") if ha_ready else ""
    # Supported = True when HA has implementation (even if device doesn't have it yet)
    supported = ha_ready
    return {
        "Cluster Id": cluster_id_hex,
        "Type": type_label,
        "Id": item_id_hex,
        "Description": description,
        "Matter ready": str(matter_ready),
        "HA ready": str(ha_ready),
        "Supported": str(supported),
        "Entity class": entity_class,
    }


def result_to_csv(result: dict[str, Any], out_path: Path) -> None:
    """Write comparison result to CSV.

    Columns: Cluster Id (hex), Type (Attr/Evt/Cmd), Id (hex), Description,
    Matter ready (bool), HA ready (bool), Supported (HA ready implies True),
    Entity class.
    """
    fieldnames = [
        "Cluster Id",
        "Type",
        "Id",
        "Description",
        "Matter ready",
        "HA ready",
        "Supported",
        "Entity class",
    ]
    rows: list[dict[str, str]] = [
        _entry_to_csv_row(p, matter_ready=True) for p in result["present"]
    ]
    rows.extend(_entry_to_csv_row(m, matter_ready=False) for m in result["missing"])
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def result_to_hex_only(result: dict[str, Any]) -> dict[str, Any]:
    """Convert result to hex-only format for JSON output."""

    def entry_hex(e: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {
            "type": e.get("type", "attr"),
            "cluster_id": e["cluster_id_hex"],
            "cluster_name": e["cluster_name"],
        }
        if e.get("type") == "cmd":
            out["command_id"] = e["command_id_hex"]
            out["command_name"] = e["command_name"]
        elif e.get("type") == "evt":
            out["event_id"] = e["event_id_hex"]
            out["event_name"] = e["event_name"]
        else:
            out["attribute_id"] = e["attribute_id_hex"]
            out["attribute_name"] = e["attribute_name"]
        if "endpoints_hex" in e:
            out["endpoints"] = e["endpoints_hex"]
        out["ha_mapped"] = e.get("ha_mapped", False)
        if e.get("ha_mapped"):
            out["ha_platform"] = e.get("ha_platform", "")
            out["ha_entity"] = e.get("ha_entity", "")
        return out

    return {
        "node_id": result.get("node_id_hex", result["node_id"]),
        "source": result.get("source", ""),
        "endpoints_found": result.get("endpoints_found_hex", result["endpoints_found"]),
        "present": [entry_hex(p) for p in result["present"]],
        "missing": [entry_hex(m) for m in result["missing"]],
        "summary": result["summary"],
    }


def main() -> None:
    """Run CLI: compare device JSON files against desired.json and write reports."""
    parser = argparse.ArgumentParser(
        description="Compare Matter devices with desired structure (endpoints/clusters/attributes)."
    )
    parser.add_argument(
        "--desired",
        default="desired.json",
        type=Path,
        help="Path to desired.json (default: desired.json)",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory to search for device node JSON files",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        help="Single device node JSON file (with attributes)",
    )
    parser.add_argument(
        "--output-dir",
        default="comparison_results",
        type=Path,
        help="Output directory for result files (default: comparison_results)",
    )
    parser.add_argument(
        "--ha-mapping",
        default="ha_mapping.json",
        type=Path,
        help="Path to ha_mapping.json (default: ha_mapping.json)",
    )
    parser.add_argument(
        "--format",
        choices=["both", "txt", "json", "csv"],
        default="both",
        help="Output format: txt (readable), json (structured), csv, or both (txt+json) (default)",
    )
    parser.add_argument(
        "--fetch-matter-server",
        action="store_true",
        help="Fetch all commissioned nodes from a running python-matter-server (instead of scanning JSON files).",
    )
    parser.add_argument(
        "--matter-server-url",
        default=os.environ.get("MATTER_SERVER_WS_URL", "ws://127.0.0.1:5580/ws"),
        help="python-matter-server websocket URL (default: ws://127.0.0.1:5580/ws). "
        "You can also set MATTER_SERVER_WS_URL.",
    )
    parser.add_argument(
        "--node-id",
        type=int,
        default=None,
        help="Only process this Matter node id (works with scanning and with --fetch-matter-server).",
    )
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="With --fetch-matter-server: only fetch and write node JSON files, then exit.",
    )
    parser.add_argument(
        "--matter-timeout",
        type=float,
        default=float(os.environ.get("MATTER_SERVER_TIMEOUT", "15")),
        help="Timeout (seconds) for matter-server connection/requests (default: 15). "
        "You can also set MATTER_SERVER_TIMEOUT.",
    )
    args = parser.parse_args()

    try:
        args.desired = safe_cli_path(args.desired)
        args.ha_mapping = safe_cli_path(args.ha_mapping)
        args.output_dir = safe_cli_path(args.output_dir)
        if args.input_dir is not None:
            args.input_dir = safe_cli_path(args.input_dir)
        if args.input_file is not None:
            args.input_file = safe_cli_path(args.input_file)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    if not args.desired.exists():
        print(f"Error: desired file not found: {args.desired}")
        return 1

    desired = load_desired(args.desired)
    desired_desc = desired.get("description", "N/A")

    ha_map = load_ha_mapping(args.ha_mapping)
    if args.ha_mapping.exists():
        attr_count = len(ha_map["attrs"])
        cmd_count = len(ha_map["cmds"])
        evt_count = len(ha_map["events"])
        print(
            f"Loaded HA mapping: {attr_count} attrs, {cmd_count} cmds, {evt_count} events"
        )
    else:
        print(
            f"Warning: HA mapping file not found: {args.ha_mapping} (HA column will show 'no' for all)"
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Find device files
    if args.fetch_matter_server:
        fetched_dir = args.output_dir / "matter_server_nodes"
        device_files = fetch_node_files_from_matter_server(
            args.matter_server_url,
            fetched_dir,
            node_id=args.node_id,
            timeout_s=args.matter_timeout,
        )
        if args.fetch_only:
            print(f"Fetched {len(device_files)} node(s) into {fetched_dir}")
            return 0
    elif args.input_file:
        device_files = [args.input_file] if args.input_file.exists() else []
    elif args.input_dir and args.input_dir.exists():
        device_files = find_device_files(args.input_dir)
    else:
        # Default: search matter_snapshots
        snapshots = Path("matter_snapshots")
        if snapshots.exists():
            device_files = find_device_files(snapshots)
        else:
            device_files = find_device_files(Path())

    if not device_files:
        print(
            "No device files found. Use --input-dir or --input-file to specify device data."
        )
        print("Device files must be JSON with 'node_id' and 'attributes' keys.")
        return 1

    for fp in device_files:
        device = load_device_file(fp)
        if not device:
            continue
        if args.node_id is not None and device.get("node_id") != args.node_id:
            continue
        result = compare_device(device, desired, ha_map)
        node_id = result["node_id"]

        if args.format in ("txt", "both"):
            txt_path = args.output_dir / f"device_{node_id}_result.txt"
            txt_path.write_text(
                format_result_text(result, desired_desc), encoding="utf-8"
            )
            print(f"Wrote {txt_path}")

        if args.format in ("json", "both"):
            json_path = args.output_dir / f"device_{node_id}_result.json"
            out = result_to_hex_only(result)
            json_path.write_text(
                json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"Wrote {json_path}")

        if args.format in ("csv", "both"):
            csv_path = args.output_dir / f"device_{node_id}_result.csv"
            result_to_csv(result, csv_path)
            print(f"Wrote {csv_path}")

    print(
        f"\nDone. Processed {len(device_files)} device(s), results in {args.output_dir}/"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
