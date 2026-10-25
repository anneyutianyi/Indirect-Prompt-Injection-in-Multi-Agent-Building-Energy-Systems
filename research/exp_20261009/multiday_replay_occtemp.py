"""Occupied-hours indoor temperature for the August multi-day replay.

Re-runs the same configurations as multiday_replay.py (no LLM; BESTOpt
simulation only), keeps the 15-min zone temperature and occupancy series,
and reports the mean indoor temperature over occupied steps. Also re-checks
the totals already stored in multiday_replay_31d.json.

    .venv/bin/python research/exp_20261009/multiday_replay_occtemp.py [days]
"""
import contextlib, copy, csv, io, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import multiday_replay as M  # noqa: E402
C = M.C

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 31
CHECK = ['occupied_steps', 'temp_max', 'hvac_kwh', 'cost_cents',
         'occupied_hours_above_26C', 'occupied_hours_above_28C']


def main():
    stored = json.loads((HERE / f'multiday_replay_{DAYS}d.json').read_text())['conditions']
    rows, series = [], {}
    for name, cfg in M.configs().items():
        cfg = copy.deepcopy(cfg)
        cfg['environment']['parameters']['duration'] = DAYS * 86400
        with contextlib.redirect_stdout(io.StringIO()):
            records = C.run_sim(cfg, steps=DAYS * M.STEPS_PER_DAY)
        total = C.evaluate(records)
        occ = [r for r in records if r['occupancy'] > 0]
        total['occupied_hours_above_26C'] = round(sum(C.RESOLUTION_H for r in occ if r['zone_temperature'] > 26.0), 2)
        total['occupied_hours_above_28C'] = round(sum(C.RESOLUTION_H for r in occ if r['zone_temperature'] > 28.0), 2)
        row = {'condition': name,
               'occupied_hours': round(len(occ) * C.RESOLUTION_H, 2),
               'occupied_mean_temp_C': round(sum(r['zone_temperature'] for r in occ) / len(occ), 3),
               'occupied_max_temp_C': round(max(r['zone_temperature'] for r in occ), 3),
               'mean_cooling_setpoint_occupied_C': round(sum(r['cooling_setpoint'] for r in occ) / len(occ), 3),
               'temp_max_C': total['temp_max'],
               'occupied_hours_above_26C': total['occupied_hours_above_26C'],
               'occupied_hours_above_28C': total['occupied_hours_above_28C'],
               'hvac_kwh': total['hvac_kwh'],
               'cost_usd': round(total['cost_cents'] / 100, 2)}
        mism = [k for k in CHECK if abs(float(total[k]) - float(stored[name]['total'][k])) > 1e-3]
        row['matches_stored_31d_json'] = 'yes' if not mism else 'no: ' + ','.join(mism)
        rows.append(row)
        series[name] = [(r['zone_temperature'], r['occupancy'], r['cooling_setpoint']) for r in records]
        print(json.dumps(row), flush=True)
    out = HERE / f'multiday_replay_{DAYS}d_occupied_temp.csv'
    with out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    ts = HERE / f'multiday_replay_{DAYS}d_timeseries.csv'
    names = list(series)
    with ts.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['step', 'occupied'] + [f'{n}_zone_temp_C' for n in names] + [f'{n}_cooling_setpoint_C' for n in names])
        for i in range(len(series[names[0]])):
            w.writerow([i, int(series[names[0]][i][1] > 0)] + [round(series[n][i][0], 3) for n in names]
                       + [series[n][i][2] for n in names])
    print('wrote', out, ts)


if __name__ == '__main__':
    main()
