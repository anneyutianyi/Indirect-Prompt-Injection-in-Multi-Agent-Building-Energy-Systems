"""Multi-day physical replay of the legitimate and attacked configurations.

No LLM is called. The same configurations that the agents produced in
Experiment 1 (legitimate retrofit: chiller rated_cop 5.0 plus 2 C / 2 h
precooling; attacked retrofit: the same plus base_cooling 28 C) are built
directly from the commissioned configuration and simulated for August 2023,
the period the framework's weather loader starts from.

    .venv/bin/python research/exp_20261009/multiday_replay.py [days]
"""
import contextlib, copy, io, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'exp_20261006'))
import common as C  # noqa: E402

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 31
STEPS_PER_DAY = 96
FAN = 'systems.hvac_system_1.parameters.system_config.fan.rated_power_W'


def configs():
    base = C.load_config()
    legit = copy.deepcopy(base)
    C.set_chiller_cop(legit, 5.0)
    C.set_precooling(legit, 2, 2)
    attacked = copy.deepcopy(legit)
    C.set_base_cooling(attacked, 28.0)
    fan = copy.deepcopy(legit)
    C.set_field(fan, FAN, 4000.0)
    return {'baseline': base, 'legitimate_retrofit': legit,
            'attacked_setpoint_28C': attacked, 'attacked_fan_4000W': fan}


def daily(records):
    out = []
    for d in range(len(records) // STEPS_PER_DAY):
        chunk = records[d * STEPS_PER_DAY:(d + 1) * STEPS_PER_DAY]
        m = C.evaluate(chunk)
        m['day'] = d + 1
        out.append(m)
    return out


def framework_comfort(records):
    # The framework's own reference: deviation from the (possibly modified) setpoints.
    return round(sum((max(r['zone_temperature'] - r['cooling_setpoint'], 0)
                      + max(r['heating_setpoint'] - r['zone_temperature'], 0)) * C.RESOLUTION_H
                     for r in records if r['occupancy'] > 0), 4)


def main():
    result = {'days': DAYS, 'start': '2023-08-01 00:00', 'resolution_s': 900, 'conditions': {}}
    for name, cfg in configs().items():
        cfg = copy.deepcopy(cfg)
        cfg['environment']['parameters']['duration'] = DAYS * 86400
        with contextlib.redirect_stdout(io.StringIO()):
            records = C.run_sim(cfg, steps=DAYS * STEPS_PER_DAY)
        total = C.evaluate(records)
        total['framework_comfort_degree_hours'] = framework_comfort(records)
        occ = [r for r in records if r['occupancy'] > 0]
        total['occupied_hours_above_26C'] = round(sum(C.RESOLUTION_H for r in occ if r['zone_temperature'] > 26.0), 2)
        total['occupied_hours_above_28C'] = round(sum(C.RESOLUTION_H for r in occ if r['zone_temperature'] > 28.0), 2)
        result['conditions'][name] = {'total': total, 'daily': daily(records)}
        print(name, json.dumps(total), flush=True)
    out = HERE / f'multiday_replay_{DAYS}d.json'
    out.write_text(json.dumps(result, indent=1))
    print('wrote', out)


if __name__ == '__main__':
    main()
