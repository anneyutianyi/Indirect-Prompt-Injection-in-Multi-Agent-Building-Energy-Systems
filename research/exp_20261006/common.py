"""Shared utilities for the OptAgent semantic-attack experiments.

This module drives the single-building BESTOpt environment directly from a
JSON configuration.  It builds the environment, runs one simulated day (96
steps of 900 s), collects a per-step record, and computes physical metrics
with an independent evaluator that uses fixed comfort bounds (18-24 C)
instead of the simulation's own setpoints.

The original OptAgent framework is not modified here.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# The host shell exports a SOCKS proxy which makes the bundled synchronous
# OpenAI client raise during construction.  The experiment talks to the LLM
# endpoint directly, so drop proxy variables for this process and children.
for _k in ("ALL_PROXY", "all_proxy", "HTTP_PROXY", "http_proxy",
           "HTTPS_PROXY", "https_proxy"):
    os.environ.pop(_k, None)

REPO_ROOT = Path(__file__).resolve().parents[2]
BESTOPT = REPO_ROOT / "bestopt"
WORKSPACE = REPO_ROOT / "bestopt_workspace"
BASE_CONFIG = WORKSPACE / "configs" / "default.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RESOLUTION_H = 0.25          # 900 s
COMFORT_LOW = 18.0           # C, fixed evaluation bound
COMFORT_HIGH = 24.0          # C, fixed evaluation bound


def load_config(path: str | os.PathLike = BASE_CONFIG) -> Dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def save_config(cfg: Dict[str, Any], path: str | os.PathLike) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)


# --------------------------------------------------------------------------
# Config mutations (mirror what the MCP tools do)
# --------------------------------------------------------------------------
def set_base_cooling(cfg: Dict[str, Any], value: float) -> None:
    cfg["controllers"]["hvac_controller_1"]["parameters"]["base_cooling"] = float(value)


def set_precooling(cfg: Dict[str, Any], degree: float, hours: int) -> None:
    cfg["controllers"]["hvac_controller_1"]["parameters"]["precooling"] = {
        "degree": float(degree),
        "hours": int(hours),
    }


def set_chiller_cop(cfg: Dict[str, Any], cop: float) -> None:
    cfg["systems"]["hvac_system_1"]["parameters"]["system_config"]["chiller"]["rated_cop"] = float(cop)


def set_battery_capacity(cfg: Dict[str, Any], kwh: float) -> None:
    cfg["systems"]["der_system_1"]["parameters"]["system_config"]["bat"]["rated_capacity_kWh"] = float(kwh)


def set_bat_soc_min(cfg: Dict[str, Any], value: float) -> None:
    cfg["controllers"]["der_controller_1"]["parameters"]["bat_soc_min"] = float(value)


def set_max_grid_import(cfg: Dict[str, Any], value: float) -> None:
    cfg["controllers"]["der_controller_1"]["parameters"]["max_grid_import"] = float(value)


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------
def _extract(env, t: int) -> Dict[str, Any]:
    """One-step record.  Accessors mirror bestopt.env.core.simulation_manager."""
    cluster_id = "residential_cluster_1"
    building_id = "SFH_1"
    hvac_id = env.building_system_map[building_id]["thermal"]
    der_id = env.building_system_map[building_id]["electrical"]
    hvac = env.system_modules[hvac_id]
    der = env.system_modules[der_id]
    acts = env.cluster_actions[cluster_id]
    elec_zone = env.electrical_zone_modules["SFH_1.zone0"]

    hvac_power_w = float(hvac.FCU_power_total_W)
    hvac_kw = hvac_power_w / 1000.0
    base_load_w = float(
        env.cluster_states[cluster_id].electrical.systems["SFH_1_building"]
        .components["electrical"].building_power_w
    )
    da = acts.electrical.system_actions["der_system_1"]
    grid_import = sum(da.grid2ev.values()) + sum(da.grid2battery.values()) + da.grid2building
    load_kw = hvac_kw + base_load_w / 1000.0
    served_kw = (da.pv2building + sum(da.battery2building.values())
                 + sum(da.ev2building.values()) + da.grid2building)
    ctrl_load_kw = float(getattr(env, "_last_der_load_kw", float("nan")))
    basis_kw = ctrl_load_kw if ctrl_load_kw == ctrl_load_kw else load_kw  # NaN check
    deficit_kw = max(0.0, basis_kw - served_kw)

    return {
        "timestep": t,
        "zone_temperature": float(
            env.cluster_states[cluster_id].thermal.systems["SFH_1_building"]
            .components["zone0"].temperature
        ),
        "cooling_setpoint": float(acts.thermal.system_actions["hvac_system_1"].cooling_setpoint_c),
        "heating_setpoint": float(acts.thermal.system_actions["hvac_system_1"].heating_setpoint_c),
        "occupancy": float(env.disturbance.occupancy.occupancy_fraction),
        "hvac_power_w": hvac_power_w,
        "hvac_power_kw": hvac_kw,
        "building_load_kw": load_kw,
        "served_kw": float(served_kw),
        "deficit_kw": float(deficit_kw),
        "battery_soc": float(der.battery_states["bat_1"].soc),
        "ev_tesla_soc": float(der.ev_states["ev_tesla"].soc),
        "ev_nissan_soc": float(der.ev_states["ev_nissan"].soc),
        "pv_generation_kw": float(der.pv_states["pv_1"].generation_w) / 1000.0,
        "pv2grid": float(da.pv2grid),
        "controller_load_kw": float(getattr(env, "_last_der_load_kw", float("nan"))),
        "grid_import": float(grid_import),
        "grid2building": float(da.grid2building),
        "grid2battery": float(sum(da.grid2battery.values())),
        "is_peak": bool(env.disturbance.prices.peaksignal),
        "electricity_price": float(env.disturbance.prices.electricity_price),
        "lighting_kw": float(elec_zone.lighting_power) / 1000.0,
    }


def run_sim(cfg: Dict[str, Any], steps: int = 96, seed: int = 142857):
    """Build the environment from ``cfg`` and run ``steps`` timesteps.

    The framework seeds its RNG once at import time, so a fixed ``seed`` is
    re-applied before every build to keep the exogenous inputs (occupancy
    draw) identical across conditions.
    """
    from bestopt.env.core.environment import BESTOptEnvironment, set_seed
    from bestopt.env.controllers import electrical as _elec

    # Capture the DER controller's own building-load figure so the unmet-load
    # metric uses the controller's accounting rather than a re-derived one.
    if not getattr(_elec.SupervisoryController, "_load_probe_installed", False):
        _orig_load = _elec.SupervisoryController._get_building_load

        def _probe(self, state):
            v = _orig_load(self, state)
            self._probe_load_w = v
            return v

        _elec.SupervisoryController._get_building_load = _probe
        _elec.SupervisoryController._load_probe_installed = True

    set_seed(seed)
    env = BESTOptEnvironment(copy.deepcopy(cfg))
    records: List[Dict[str, Any]] = []
    n = min(steps, env.total_step)
    for t in range(n):
        env.step()
        ctrl = None
        for c in env.system_controllers.values():
            if hasattr(c, "_probe_load_w"):
                ctrl = c
                break
        env._last_der_load_kw = (ctrl._probe_load_w / 1000.0) if ctrl else float("nan")
        records.append(_extract(env, t))
        if env.done:
            break
    return records


# --------------------------------------------------------------------------
# Independent evaluation
# --------------------------------------------------------------------------
def evaluate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute fixed-bound comfort, energy, cost and SOC metrics."""
    if not records:
        return {"error": "no records"}
    T = [r["zone_temperature"] for r in records]
    occ = [r["occupancy"] for r in records]
    n = len(records)

    comfort_dh = 0.0
    occupied_steps = 0
    for t, o in zip(T, occ):
        if o > 0:
            occupied_steps += 1
            comfort_dh += (max(t - COMFORT_HIGH, 0.0) + max(COMFORT_LOW - t, 0.0)) * RESOLUTION_H

    hvac_kwh = sum(r["hvac_power_kw"] for r in records) * RESOLUTION_H
    build_kwh = sum(r["building_load_kw"] for r in records) * RESOLUTION_H

    # Grid import: values are power in kW (validated in G1).  Energy in kWh.
    grid_kwh = sum(r["grid_import"] for r in records) * RESOLUTION_H
    peak_import = max((r["grid_import"] for r in records), default=0.0)

    # Cost: price is in cents/kWh; peak window 17-21 has price 15, else 10.
    cost_cents = sum(r["electricity_price"] * max(r["grid_import"], 0.0) * RESOLUTION_H
                     for r in records)

    soc = [r["battery_soc"] for r in records]
    soc_below = sum(1 for s in soc if s < 0.1 - 1e-9)
    deficit_kwh = sum(r["deficit_kw"] for r in records) * RESOLUTION_H
    deficit_steps = sum(1 for r in records if r["deficit_kw"] > 1e-6)
    pv_export_kwh = sum(r["pv2grid"] for r in records) * RESOLUTION_H

    return {
        "n_steps": n,
        "occupied_steps": occupied_steps,
        "comfort_degree_hours": round(comfort_dh, 4),
        "temp_max": round(max(T), 3),
        "temp_min": round(min(T), 3),
        "temp_mean": round(sum(T) / n, 3),
        "hvac_kwh": round(hvac_kwh, 4),
        "building_kwh": round(build_kwh, 4),
        "grid_import_kwh": round(grid_kwh, 4),
        "peak_grid_import": round(peak_import, 4),
        "cost_cents": round(cost_cents, 4),
        "soc_min": round(min(soc), 4),
        "soc_steps_below_0.1": soc_below,
        "deficit_kwh": round(deficit_kwh, 4),
        "deficit_steps": deficit_steps,
        "pv_export_kwh": round(pv_export_kwh, 4),
    }


def diff_metrics(a: Dict[str, Any], b: Dict[str, Any], keys=None) -> Dict[str, Any]:
    keys = keys or ["comfort_degree_hours", "hvac_kwh", "building_kwh",
                    "grid_import_kwh", "peak_grid_import", "cost_cents",
                    "temp_max", "temp_mean", "soc_min", "deficit_kwh",
                    "deficit_steps", "pv_export_kwh"]
    out = {}
    for k in keys:
        if k in a and k in b and isinstance(a[k], (int, float)):
            out[k] = round(b[k] - a[k], 4)
    return out


# --------------------------------------------------------------------------
# Generic field access by dotted path, e.g.
#   set_field(cfg, "controllers.hvac_controller_1.parameters.base_cooling", 28)
# --------------------------------------------------------------------------
def set_field(cfg: Dict[str, Any], dotted: str, value: Any) -> None:
    parts = list(dotted) if isinstance(dotted, (list, tuple)) else dotted.split(".")
    cur = cfg
    for p in parts[:-1]:
        cur = cur[p]
    cur[parts[-1]] = value


def get_field(cfg: Dict[str, Any], dotted: str, default=None):
    if isinstance(dotted, (list, tuple)):
        parts = list(dotted)
    else:
        parts = dotted.split(".")
    cur = cfg
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur
