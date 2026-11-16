"""Recompute paper aggregates from the two portable source CSV files.

The input metrics are derived simulation outputs, not executable QUIC-Fire inputs.
The complete, balanced categorical design permits orthogonal Type II sums of
squares. The independent regression check is retained from the verified audit.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from anova import calculate, FACTORS, RESPONSES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/source'
OUTPUT = ROOT / 'outputs/tables'
LAYOUTS = ['Strip_Broken', 'Strip_Dot', 'Flank_Broken', 'Flank_Dot']
META = ['fuel_model', 'curing_state', 'ignition_pattern', 'ignition_family',
        'ignition_structure', 'wind_speed_mph', 'surface_moisture']
METRICS = {'consumption': 'consumption_fraction_surface',
           'active_area': 'active_consumed_area_fraction_1pct',
           'patchiness': 'cell_consumption_cv'}


def save(table, filename, index=False):
    table.to_csv(OUTPUT / filename, index=index)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = SOURCE / 'doe_analysis_ready_response_table.csv'
    series_path = SOURCE / 'paper2_fuel_consumption_active_area_timeseries.csv'
    data = pd.read_csv(source)
    ts = pd.read_csv(series_path)
    assert len(data) == 1600 and data.run_id.is_unique
    assert not data.isna().any().any()
    assert np.isfinite(data[list(METRICS.values())]).all().all()
    assert data.groupby(FACTORS).size().eq(1).all()
    assert data.groupby(FACTORS).ngroups == 1600
    assert (data.ignition_pattern == data.ignition_family+'_'+data.ignition_structure).all()
    assert len(ts) == 97600 and ts.run_id.nunique() == 1600
    assert not ts.duplicated(['run_id', 'time_index']).any()
    assert set(ts.run_id) == set(data.run_id)
    assert not ts.isna().any().any()
    pairs = ts[['run_id'] + META].drop_duplicates().merge(data[['run_id']+META], on='run_id', validate='one_to_one', suffixes=('_series','_primary'))
    for field in META:
        assert pairs[field+'_series'].equals(pairs[field+'_primary'])

    anova, checks = calculate(data, 'Pooled')
    save(anova, 'pooled_anova.csv')
    save(anova.pivot(index='term_clean', columns='metric', values='omega_sq'), 'pooled_omega_squared.csv', index=True)
    save(data[list(METRICS.values())].describe().T, 'final_metric_summary.csv', index=True)
    group_keys = ['fuel_model', 'curing_state']
    group_means = data.groupby(group_keys)[list(METRICS.values())].mean().reset_index()
    group_means['n_runs'] = 64
    assert data.groupby(group_keys).size().eq(64).all()
    save(group_means, 'condition_means.csv')
    heatmap = []
    for symbol, column in zip(['C_T','A_T','P_T'], METRICS.values()):
        for _, row in group_means.iterrows():
            heatmap.append(dict(fuel_model=row.fuel_model, curing_state=row.curing_state,
                                metric=symbol, mean_value=row[column], n_runs=64))
    save(pd.DataFrame(heatmap), 'heatmap_values.csv')
    for name, field in [('wind', 'wind_speed_mph'), ('moisture', 'surface_moisture')]:
        table = data.groupby(['fuel_model', field]).agg(mean_C_T=('consumption_fraction_surface','mean'), n_runs=('run_id','size')).reset_index()
        assert table.n_runs.eq(80).all()
        save(table, name+'_means.csv')

    orientation = data.groupby(group_keys+['ignition_family'])[list(METRICS.values())].mean()
    assert data.groupby(group_keys+['ignition_family']).size().eq(32).all()
    contrasts = []
    for fuel, curing in data.groupby(group_keys).groups:
        row = dict(fuel_model=fuel, curing_state=curing)
        for name, column in METRICS.items():
            strip = float(orientation.loc[(fuel,curing,'Strip'),column])
            flank = float(orientation.loc[(fuel,curing,'Flank'),column])
            row.update({f'mean_{name}_Strip':strip, f'mean_{name}_Flank':flank,
                        f'delta_mean_{name}_strip_minus_flank':strip-flank})
        contrasts.append(row)
    save(pd.DataFrame(contrasts), 'pooled_strip_minus_flank.csv')

    layout = data.groupby(group_keys+['ignition_pattern'])[list(METRICS.values())].mean().reset_index()
    assert data.groupby(group_keys+['ignition_pattern']).size().eq(16).all()
    layout['n_runs'] = 16
    save(layout, 'layout_means.csv')
    winners, margins, rankings = [], [], []
    for (fuel,curing), group in layout.groupby(group_keys):
        winner = dict(fuel_model=fuel,curing_state=curing)
        margin = dict(winner)
        for name,column in METRICS.items():
            objective = 'low_patchiness' if name == 'patchiness' else name
            ranked = group.sort_values([column,'ignition_pattern'],ascending=[name=='patchiness',True])
            first, second = ranked.iloc[0], ranked.iloc[1]
            winner['best_for_'+objective] = first.ignition_pattern
            difference = float(second[column]-first[column]) if name=='patchiness' else float(first[column]-second[column])
            margin.update({f'best_pattern_{objective}':first.ignition_pattern,
                           f'best_value_{objective}':float(first[column]),
                           f'second_pattern_{objective}':second.ignition_pattern,
                           f'second_value_{objective}':float(second[column]),
                           f'margin_{objective}':difference})
            for rank,(_,record) in enumerate(ranked.iterrows(),1):
                rankings.append(dict(fuel_model=fuel,curing_state=curing,objective=objective,
                                     rank=rank,ignition_pattern=record.ignition_pattern,mean_value=record[column]))
        winners.append(winner); margins.append(margin)
    save(pd.DataFrame(winners), 'winners.csv')
    save(pd.DataFrame(margins), 'top_two_margins.csv')
    save(pd.DataFrame(rankings), 'all_layout_rankings.csv')

    # Archived configuration/log audit established a 60 s stored-output interval.
    # Therefore indices 0..60 correspond to 0..60 elapsed minutes.
    records = []
    for run_id, group in ts.groupby('run_id'):
        group = group.sort_values('time_index')
        index = group.time_index.to_numpy(dtype=float)
        assert np.array_equal(index, np.arange(61))
        minutes = index * 60.0 / 60.0
        record = {'run_id': run_id, **{key:group.iloc[0][key] for key in META}}
        for kind,column,thresholds in [('consumption','consumption_fraction_t',[.1,.5,.8]),
                                       ('active_area','active_area_fraction_t',[.1,.5])]:
            values = group[column].to_numpy(dtype=float)
            assert np.isfinite(values).all() and values.min() >= 0 and values.max() <= 1
            assert values[0] == 0
            record['final_'+kind] = float(values[-1])
            for level in thresholds:
                hits = np.flatnonzero(values >= level)
                record[f't{int(level*100)}_{kind}'] = float(minutes[hits[0]]) if len(hits) else np.nan
            record['auc_'+kind] = float(np.sum((values[:-1]+values[1:])/2*np.diff(minutes)))
        records.append(record)
    temporal = pd.DataFrame(records)
    joined = temporal.merge(data,on='run_id',suffixes=('_temporal','_primary'),validate='one_to_one')
    np.testing.assert_allclose(joined.final_consumption,joined.consumption_fraction_surface,rtol=0,atol=1e-11)
    np.testing.assert_allclose(joined.final_active_area,joined.active_consumed_area_fraction_1pct,rtol=0,atol=1e-11)
    save(temporal,'temporal_milestones.csv')
    summary = []
    for pattern,group in temporal.groupby('ignition_pattern'):
        assert len(group)==400
        row = dict(ignition_pattern=pattern,n_runs=len(group))
        for kind,levels in [('consumption',[10,50,80]),('active_area',[10,50])]:
            row['mean_final_'+kind]=float(group['final_'+kind].mean())
            row['median_final_'+kind]=float(group['final_'+kind].median())
            row['mean_auc_'+kind]=float(group['auc_'+kind].mean())
            row['median_auc_'+kind]=float(group['auc_'+kind].median())
            for level in levels:
                key=f't{level}_{kind}'
                reached=int(group[key].notna().sum())
                row['n_reached_'+key]=reached
                row['reached_'+key]=reached/len(group)
                row['percentage_reached_'+key]=100*reached/len(group)
                row['median_'+key]=float(group[key].dropna().median()) if reached else np.nan
        summary.append(row)
    summary=pd.DataFrame(summary).set_index('ignition_pattern').loc[LAYOUTS].reset_index()
    save(summary,'temporal_layout_summary.csv')
    curves=ts.groupby(['fuel_model','curing_state','ignition_pattern','time_index']).agg(
        mean_consumption_t=('consumption_fraction_t','mean'), median_consumption_t=('consumption_fraction_t','median'),
        mean_active_area_t=('active_area_fraction_t','mean'), median_active_area_t=('active_area_fraction_t','median'),
        n_runs=('run_id','size')).reset_index()
    assert len(curves)==6100 and curves.n_runs.eq(16).all()
    curves['elapsed_time_min']=curves.time_index.astype(float)
    curves['elapsed_time_s']=curves.time_index*60
    save(curves,'condition_layout_curves.csv')
    report = dict(source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,series_path]},
                  n_runs=1600,trajectory_rows=97600,outputs_per_run=61,seconds_per_output=60,
                  anova_checks=checks,analysis_scope='Reproduce analyses from archived response metrics, not rerun the fire simulations.',
                  threshold_definition='First stored output at or above threshold; blank if not reached by 60 min; no interpolation.',
                  temporal_units='Threshold times and AUC are in minutes. Median threshold times exclude unreached runs; reach percentages include all 400 runs per layout.')
    (ROOT/'outputs/analysis_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Recomputed pooled ANOVA, group means, contrasts, rankings, margins and temporal metrics.')


if __name__ == '__main__':
    main()
