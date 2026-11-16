"""Reproduce corrected manuscript figure 4.

Run python run_all.py from the repository root to calculate prerequisites.
"""
from pathlib import Path
import csv
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'outputs/fig4'
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

LABELS = {
    'Fuel model': 'Fuel model',
    'Curing state': 'Curing state',
    'Ignition family': 'Ignition-line orientation',
    'Ignition structure': 'Ignition continuity',
    'Wind speed': 'Wind speed',
    'Surface moisture': 'Surface fuel moisture',
    'Fuel model × curing state': 'Fuel model × curing state',
    'Curing state × ignition family': 'Curing state × ignition-line orientation',
    'Fuel model × ignition family': 'Fuel model × ignition-line orientation',
    'Fuel model × wind speed': 'Fuel model × wind speed',
    'Fuel model × surface moisture': 'Fuel model × surface fuel moisture',
    'Wind speed × surface moisture': 'Wind speed × surface fuel moisture',
}
COLUMNS = ['Consumption', 'Active area', 'Patchiness']


def read_matrix(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    return {r['term_clean']: np.array([float(r[c]) for c in COLUMNS]) for r in rows}


def annotation(value):
    return '<0.001' if 0 < value < 0.001 else f'{value:.3f}'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source_csv = DATA / 'doe_analysis_ready_response_table.csv'
    matrix = read_matrix(TABLES / 'pooled_omega_squared.csv')
    archived = read_matrix(REFERENCE / 'fig4_omega_squared.csv')
    assert set(matrix) == set(LABELS) == set(archived)
    assert len(matrix) == 12
    for term, values in matrix.items():
        np.testing.assert_allclose(values, archived[term], rtol=0, atol=1e-12)
    order = sorted(matrix, key=lambda term: -float(matrix[term].mean()))
    data = np.array([matrix[term] for term in order])
    assert data.shape == (12, 3) and np.isfinite(data).all()

    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 8.6,
        'axes.titlesize': 10, 'axes.labelsize': 8.6,
        'xtick.labelsize': 8.4, 'ytick.labelsize': 8.5,
        'pdf.fonttype': 42, 'ps.fonttype': 42,
    })
    fig = plt.figure(figsize=(7.4, 5.15))
    ax = fig.add_axes([0.45, 0.15, 0.425, 0.77])
    cmap = plt.get_cmap('cividis_r')
    heatmap = ax.imshow(data, cmap=cmap, vmin=0, vmax=0.21, aspect='auto',
                        interpolation='nearest')
    ax.set_title('Pooled analysis of 1,600 simulations', pad=11)
    ax.set_yticks(range(12), [LABELS[term] for term in order])
    ax.set_xticks(range(3), ['Fuel\nconsumption\n'+r'$C(T)$',
                            'Active treatment\narea\n'+r'$A(T)$',
                            'Consumption\npatchiness\n'+r'$P(T)$'])
    ax.tick_params(axis='both', length=0, pad=7)
    ax.set_xticks(np.arange(-.5, 3, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 12, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=.65)
    ax.tick_params(which='minor', length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    annotations = []
    for i, term in enumerate(order):
        for j, column in enumerate(COLUMNS):
            value = data[i, j]
            rgb = np.array(cmap(value/.21)[:3])
            linear = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
            luminance = float(linear @ np.array([.2126, .7152, .0722]))
            color = 'black' if luminance > .179 else 'white'
            label = annotation(value)
            ax.text(j, i, label, ha='center', va='center', color=color, fontsize=9)
            annotations.append({'term': term, 'display_label': LABELS[term],
                                'metric': column, 'omega_squared': float(value),
                                'annotation': label})
    cax = fig.add_axes([.90, .15, .018, .77])
    bar = fig.colorbar(heatmap, cax=cax, ticks=[0, .05, .10, .15, .20])
    bar.ax.tick_params(labelsize=8, length=3)
    bar.set_label(r'Omega-squared effect size, $\omega^2$', labelpad=7)
    bar.outline.set_linewidth(.6)
    stem = OUTPUT/'Fig04_ANOVA_pooled'
    fig.savefig(stem.with_suffix('.pdf'), bbox_inches='tight', pad_inches=.08,
                metadata={'Title': 'Fig. 4: pooled ANOVA effect sizes',
                          'Subject': 'Six main effects and six selected interactions; 1,600 simulations.'})
    fig.savefig(stem.with_suffix('.png'), dpi=400, bbox_inches='tight', pad_inches=.08)
    plt.close(fig)
    (HERE / 'verification.json').write_text(json.dumps({'figure': '4', 'status': 'passed', 'source': 'Portable CSV exports', 'reference_values': 'data/reference', 'output_directory': 'outputs/figures'}, indent=2)+'\n', encoding='utf-8')
    print('Generated figure 4; numerical checks passed.')


if __name__ == '__main__':
    main()
