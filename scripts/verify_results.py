"""Compare recomputed analyses with frozen, previously verified CSV values."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / 'outputs/tables'
REFERENCE = ROOT / 'data/reference'


def compare(actual_file, reference_file, keys, selected=False):
    actual = pd.read_csv(TABLES / actual_file)
    expected = pd.read_csv(REFERENCE / reference_file)
    assert not actual.duplicated(keys).any(), actual_file
    assert not expected.duplicated(keys).any(), reference_file
    joined = expected.merge(actual,on=keys,suffixes=('_expected','_actual'),validate='one_to_one')
    assert len(joined) == len(expected), reference_file
    if not selected:
        assert len(joined) == len(actual), actual_file
    largest = 0.0
    fields = [field for field in expected if field not in keys and field in actual]
    assert fields
    for field in fields:
        a, b = joined[field+'_actual'], joined[field+'_expected']
        if pd.api.types.is_numeric_dtype(expected[field]):
            np.testing.assert_allclose(a,b,rtol=0,atol=1e-11,equal_nan=True,err_msg=field)
            valid = np.isfinite(a) & np.isfinite(b)
            if valid.any():
                largest = max(largest,float(np.max(np.abs(a[valid]-b[valid]))))
        else:
            assert a.equals(b), field
    return dict(actual=actual_file,reference=reference_file,rows=len(joined),fields=fields,
                maximum_absolute_difference=largest)


def main():
    checks = [
        compare('pooled_omega_squared.csv','fig4_omega_squared.csv',['term_clean']),
        compare('heatmap_values.csv','fig5_heatmap_values.csv',['fuel_model','curing_state','metric']),
        compare('wind_means.csv','verified_wind_response_by_fuel_model.csv',['fuel_model','wind_speed_mph']),
        compare('moisture_means.csv','verified_moisture_response_by_fuel_model.csv',['fuel_model','surface_moisture']),
        compare('pooled_strip_minus_flank.csv','fig7_pooled_contrasts.csv',['fuel_model','curing_state']),
        compare('winners.csv','fig8_winners.csv',['fuel_model','curing_state']),
        compare('top_two_margins.csv','fig8_top_two_margins.csv',['fuel_model','curing_state']),
        compare('temporal_layout_summary.csv','fig9_temporal_layout_summary.csv',['ignition_pattern']),
        compare('condition_layout_curves.csv','fig10_curve_points.csv',['fuel_model','curing_state','ignition_pattern','time_index'],selected=True),
    ]
    report = dict(status='passed',absolute_tolerance=1e-11,checks=checks,
                  scope='Recalculation of archived analyses from public CSV exports; no new simulation runs.')
    (ROOT/'outputs/reproduction_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('All nine reference-table comparisons passed.')


if __name__ == '__main__':
    main()
