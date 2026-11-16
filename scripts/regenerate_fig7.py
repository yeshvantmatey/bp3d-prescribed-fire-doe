"""Reproduce corrected manuscript figure 7.

Run python run_all.py from the repository root to calculate prerequisites.
"""
from pathlib import Path
import csv
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'outputs/fig7'
HERE.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'data/source'
REFERENCE = ROOT / 'data/reference'
TABLES = ROOT / 'outputs/tables'
OUTPUT = ROOT / 'outputs/figures'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.matplotlib-cache'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FUELS = ['GR2', 'GS1', 'GS2', 'SH2', 'SH5']
CURING = ['early_spring_before_greenup', 'spring_after_greenup',
          'early_summer_senescence', 'fall_with_greenup', 'fall_without_greenup']
CURING_LABELS = ['Early spring\nbefore green-up', 'Spring\nafter green-up',
                 'Early-summer\nsenescence', 'Fall\nwith green-up', 'Fall\nwithout green-up']
METRICS = [
    ('consumption', 'C(T)', '(a) Fuel consumption', 1., [-1., -.5, 0., .5, 1.]),
    ('active_area', 'A(T)', '(b) Active treatment area', 1., [-1., -.5, 0., .5, 1.]),
    ('patchiness', 'P(T)', '(c) Consumption patchiness', 4., [-4., -2., 0., 2., 4.]),
]


def read_keyed(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    keyed = {(r['fuel_model'], r['curing_state']): r for r in rows}
    assert len(keyed) == len(rows) == 25
    assert set(keyed) == {(f,c) for f in FUELS for c in CURING}
    return keyed


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = read_keyed(TABLES / 'pooled_strip_minus_flank.csv')
    archived = read_keyed(REFERENCE / 'fig7_pooled_contrasts.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':9.5,
                         'axes.titlesize':10, 'axes.labelsize':9.5,
                         'xtick.labelsize':9.5, 'ytick.labelsize':9.5,
                         'pdf.fonttype':42, 'ps.fonttype':42})
    fig = plt.figure(figsize=(9.2, 4.6))
    fig.text(.58, .98, 'Strip minus Flank, averaged across Broken and Dot',
             ha='center', va='top', fontsize=11)
    cmap = plt.get_cmap('RdBu_r')
    annotations, maximum_error = [], 0.
    first_axis = None
    for index, (metric, symbol, title, bound, ticks) in enumerate(METRICS):
        x = [.185, .455, .725][index]
        ax = fig.add_axes([x,.30,.25,.49], sharey=first_axis)
        if first_axis is None:
            first_axis = ax
        column = 'delta_mean_'+metric+'_strip_minus_flank'
        values = np.array([[float(rows[(fuel,curing)][column]) for fuel in FUELS] for curing in CURING])
        assert values.shape == (5,5) and np.isfinite(values).all()
        assert abs(values).max() <= bound
        image = ax.imshow(values,cmap=cmap,vmin=-bound,vmax=bound,
                          aspect='auto',interpolation='nearest')
        ax.set_title(title+'\n'+f'${symbol}$',pad=10)
        ax.set_xticks(range(5),FUELS)
        ax.set_xlabel('Fuel model',labelpad=7)
        ax.set_yticks(range(5),CURING_LABELS)
        ax.tick_params(axis='both',length=0,pad=7)
        if index:
            ax.tick_params(axis='y',labelleft=False)
        else:
            ax.set_ylabel('Curing state',labelpad=10)
        ax.set_xticks(np.arange(-.5,5,1),minor=True)
        ax.set_yticks(np.arange(-.5,5,1),minor=True)
        ax.grid(which='minor',color='white',linewidth=.8)
        ax.tick_params(which='minor',length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for i,curing in enumerate(CURING):
            for j,fuel in enumerate(FUELS):
                value = float(values[i,j])
                source_row = rows[(fuel,curing)]
                from_means = float(source_row['mean_'+metric+'_Strip'])-float(source_row['mean_'+metric+'_Flank'])
                error = max(abs(value-float(archived[(fuel,curing)][column])),abs(value-from_means))
                maximum_error = max(maximum_error,error)
                assert error < 1e-12
                label = f'{value:.3f}'
                assert label not in ['0.000','-0.000']
                rgb = np.array(cmap((value+bound)/(2*bound))[:3])
                linear = np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
                luminance = float(linear @ np.array([.2126,.7152,.0722]))
                ax.text(j,i,label,ha='center',va='center',fontsize=9.2,
                        color='black' if luminance>.179 else 'white')
                annotations.append(dict(metric=metric,fuel_model=fuel,curing_state=curing,
                                        difference=value,annotation=label))
        cax = fig.add_axes([x+.01,.12,.23,.033])
        bar = fig.colorbar(image,cax=cax,orientation='horizontal',ticks=ticks)
        bar.ax.tick_params(labelsize=8.5,length=3,pad=3)
        bar.set_label(f'Difference in mean ${symbol}$',labelpad=5,fontsize=9)
        bar.outline.set_linewidth(.6)
    stem = OUTPUT/'Fig07_pooled_strip_minus_flank'
    fig.savefig(stem.with_suffix('.pdf'),bbox_inches='tight',pad_inches=.08,
                metadata={'Title':'Fig. 7: pooled Strip-minus-Flank differences',
                          'Subject':'Three final-state metrics; 25 condition combinations; 32 runs per orientation mean.'})
    fig.savefig(stem.with_suffix('.png'),dpi=400,bbox_inches='tight',pad_inches=.08)
    plt.close(fig)
    (HERE / 'verification.json').write_text(json.dumps({'figure': '7', 'status': 'passed', 'source': 'Portable CSV exports', 'reference_values': 'data/reference', 'output_directory': 'outputs/figures'}, indent=2)+'\n', encoding='utf-8')
    print('Generated figure 7; numerical checks passed.')


if __name__ == '__main__':
    main()
