"""Reproduce corrected manuscript figure 8.

Run python run_all.py from the repository root to calculate prerequisites.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'outputs/fig8'
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
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

FUELS = ['GR2', 'GS1', 'GS2', 'SH2', 'SH5']
CURING = ['early_spring_before_greenup', 'spring_after_greenup',
          'early_summer_senescence', 'fall_with_greenup', 'fall_without_greenup']
CURING_LABELS = ['Early spring\nbefore green-up', 'Spring\nafter green-up',
                 'Early-summer\nsenescence', 'Fall\nwith green-up', 'Fall\nwithout green-up']
LAYOUTS = ['Strip_Broken', 'Strip_Dot', 'Flank_Broken', 'Flank_Dot']
COLORS = ['#fbc47c', '#cab6d9', '#a4cfe0', '#b9d98d']


def read_keyed(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    mapping = {(row['fuel_model'], row['curing_state']): row for row in rows}
    assert len(mapping) == len(rows) == 25
    assert set(mapping) == {(f, c) for f in FUELS for c in CURING}
    return mapping


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    winner_file = TABLES / 'winners.csv'
    margin_file = TABLES / 'top_two_margins.csv'
    winners = read_keyed(winner_file)
    margins = read_keyed(margin_file)
    winner_grid = np.zeros((5, 5), dtype=int)
    margin_grid = np.zeros((5, 5), dtype=float)
    cells = []
    for i, curing in enumerate(CURING):
        for j, fuel in enumerate(FUELS):
            key = (fuel, curing)
            row = winners[key]
            choices = [row[k] for k in ['best_for_consumption', 'best_for_active_area', 'best_for_low_patchiness']]
            assert len(set(choices)) == 1
            choice = choices[0]
            margin = margins[key]
            assert choice == margin['best_pattern_consumption']
            value = float(margin['margin_consumption'])
            assert abs(value-(float(margin['best_value_consumption'])-float(margin['second_value_consumption']))) < 1e-12
            assert value > 0
            winner_grid[i, j] = LAYOUTS.index(choice)
            margin_grid[i, j] = value
            cells.append(dict(fuel_model=fuel, curing_state=curing, winner=choice,
                              runner_up_consumption=margin['second_pattern_consumption'],
                              consumption_margin=value, displayed_margin=f'{value:.3f}'))
    counts = Counter(cell['winner'] for cell in cells)
    assert [counts[p] for p in LAYOUTS] == [16, 8, 1, 0]

    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':8.8,
                         'axes.titlesize':10, 'axes.labelsize':9,
                         'xtick.labelsize':9, 'ytick.labelsize':9,
                         'pdf.fonttype':42, 'ps.fonttype':42})
    fig = plt.figure(figsize=(8.2, 4.6))
    left = fig.add_axes([.22, .24, .30, .62])
    right = fig.add_axes([.57, .24, .30, .62], sharey=left)
    axes = [left, right]
    left.imshow(winner_grid, cmap=ListedColormap(COLORS),
                norm=BoundaryNorm(np.arange(-.5, 4, 1), 4),
                aspect='auto', interpolation='nearest')
    cmap = plt.get_cmap('cividis_r')
    image = right.imshow(margin_grid, cmap=cmap, vmin=0, vmax=.9,
                         aspect='auto', interpolation='nearest')
    left.set_title('(a) Highest-ranked layout\nAll three treatment objectives', pad=12)
    right.set_title('(b) Top-two consumption margin\nDifference in mean '+r'$C(T)$', pad=12)
    for ax in axes:
        ax.set_xticks(range(5), FUELS)
        ax.set_xlabel('Fuel model', labelpad=8)
        ax.set_yticks(range(5), CURING_LABELS)
        ax.tick_params(axis='both', length=0, pad=7)
        ax.set_xticks(np.arange(-.5, 5, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=.8)
        ax.tick_params(which='minor', length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    left.set_ylabel('Curing state', labelpad=10)
    right.tick_params(axis='y', labelleft=False)
    for cell in cells:
        i, j = CURING.index(cell['curing_state']), FUELS.index(cell['fuel_model'])
        left.text(j, i, cell['winner'].replace('_', '\n'), ha='center', va='center', fontsize=8.2)
        rgb = np.array(cmap(cell['consumption_margin']/.9)[:3])
        linear = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
        luminance = float(linear @ np.array([.2126, .7152, .0722]))
        right.text(j, i, cell['displayed_margin'], ha='center', va='center', fontsize=8.7,
                   color='black' if luminance > .179 else 'white')
    cax = fig.add_axes([.90, .24, .018, .62])
    bar = fig.colorbar(image, cax=cax, ticks=[0, .2, .4, .6, .8])
    bar.ax.tick_params(labelsize=8, length=3)
    bar.set_label('Consumption margin', labelpad=8)
    bar.outline.set_linewidth(.6)
    handles = [Patch(facecolor=color, edgecolor='#666666', linewidth=.4,
                     label=layout.replace('_', ' ')) for layout,color in zip(LAYOUTS,COLORS)]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.55,.035),
               ncol=4, frameon=False, fontsize=8.5, handlelength=1.4, columnspacing=1.6)
    stem = OUTPUT/'Fig08_four_layout_rankings_and_margins'
    fig.savefig(stem.with_suffix('.pdf'), bbox_inches='tight', pad_inches=.08,
                metadata={'Title':'Fig. 8: four-layout rankings and top-two consumption margins',
                          'Subject':'All four layouts compared within 25 fuel-model and curing-state combinations.'})
    fig.savefig(stem.with_suffix('.png'), dpi=400, bbox_inches='tight', pad_inches=.08)
    plt.close(fig)
    (HERE / 'verification.json').write_text(json.dumps({'figure': '8', 'status': 'passed', 'source': 'Portable CSV exports', 'reference_values': 'data/reference', 'output_directory': 'outputs/figures'}, indent=2)+'\n', encoding='utf-8')
    print('Generated figure 8; numerical checks passed.')


if __name__ == '__main__':
    main()
