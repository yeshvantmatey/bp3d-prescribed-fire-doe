"""Reproduce corrected manuscript figure 5.

Run python run_all.py from the repository root to calculate prerequisites.
"""
from pathlib import Path
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'outputs/fig5'
HERE.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'data/source'
REFERENCE = ROOT / 'data/reference'
TABLES = ROOT / 'outputs/tables'
OUTPUT = ROOT / 'outputs/figures'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.matplotlib-cache'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import fitz

FUELS = ['GR2', 'GS1', 'GS2', 'SH2', 'SH5']
CURING = ['early_spring_before_greenup', 'spring_after_greenup',
          'early_summer_senescence', 'fall_with_greenup', 'fall_without_greenup']
CURING_LABELS = ['Early spring\nbefore green-up', 'Spring\nafter green-up',
                 'Early-summer\nsenescence', 'Fall\nwith green-up', 'Fall\nwithout green-up']
METRICS = [('C_T', 'consumption_fraction_surface', 'C(T)', 'Consumption fraction', 1),
           ('A_T', 'active_consumed_area_fraction_1pct', 'A(T)', 'Active treatment area fraction', 1),
           ('P_T', 'cell_consumption_cv', 'P(T)', 'Consumption patchiness', 4)]


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA / 'doe_analysis_ready_response_table.csv')
    assert len(data) == 1600 and data.run_id.is_unique
    verified = pd.read_csv(REFERENCE / 'fig5_heatmap_values.csv')
    assert len(verified) == 75 and verified.n_runs.eq(64).all()
    assert data.groupby(['fuel_model', 'curing_state']).size().eq(64).all()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.labelsize': 10, 'axes.titlesize': 10.5,
                         'xtick.labelsize': 10, 'ytick.labelsize': 10,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig = plt.figure(figsize=(9.2, 4.6))
    cmap = LinearSegmentedColormap.from_list(
        'readable_YlGnBu', plt.get_cmap('YlGnBu')(np.linspace(.05, .90, 256)))
    first_axis = None
    records, text_objects, contrast_ratios = [], [], []
    maximum_error = 0.
    axes = []
    for panel, (metric, column, symbol, description, bound) in enumerate(METRICS):
        x = [.185, .455, .725][panel]
        ax = fig.add_axes([x, .29, .25, .56], sharey=first_axis)
        axes.append(ax)
        if first_axis is None:
            first_axis = ax
        actual = data.groupby(['curing_state', 'fuel_model'])[column].mean().unstack().loc[CURING, FUELS]
        saved = verified[verified.metric.eq(metric)].pivot(index='curing_state', columns='fuel_model', values='mean_value').loc[CURING, FUELS]
        np.testing.assert_allclose(actual, saved, rtol=0, atol=1e-14)
        maximum_error = max(maximum_error, float(np.max(np.abs(actual.to_numpy()-saved.to_numpy()))))
        values = actual.to_numpy()
        assert np.isfinite(values).all() and values.min() >= 0 and values.max() <= bound
        im = ax.imshow(values, cmap=cmap, vmin=0, vmax=bound, aspect='auto', interpolation='nearest')
        ax.set_title(f'({"abc"[panel]}) Mean ${symbol}$\n{description}', pad=12, fontsize=10)
        ax.set_xticks(range(5), FUELS)
        ax.set_xlabel('Fuel model', labelpad=8)
        ax.set_yticks(range(5), CURING_LABELS)
        ax.tick_params(axis='both', length=0, pad=7)
        if panel:
            ax.tick_params(axis='y', labelleft=False)
        else:
            ax.set_ylabel('Curing state', labelpad=10)
        ax.set_xticks(np.arange(-.5, 5, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=.65)
        ax.tick_params(which='minor', length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for row, curing in enumerate(CURING):
            for col, fuel in enumerate(FUELS):
                value = float(values[row, col])
                rgb = np.array(cmap(value/bound)[:3])
                linear = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
                luminance = float(linear @ np.array([.2126, .7152, .0722]))
                black_contrast = (luminance+.05)/.05
                white_contrast = 1.05/(luminance+.05)
                color = 'black' if black_contrast >= white_contrast else 'white'
                contrast_ratios.append(max(black_contrast, white_contrast))
                label = f'{value:.3f}'
                text = ax.text(col, row, label, ha='center', va='center', fontsize=9.4, color=color)
                text_objects.append((ax, row, col, text))
                records.append({'panel': 'abc'[panel], 'metric': metric,
                                'fuel_model': fuel, 'curing_state': curing, 'mean_value': value,
                                'displayed_value': label, 'n_runs': 64, 'text_color': color})
        cax = fig.add_axes([x+.01, .11, .23, .031])
        ticks = [0, .25, .5, .75, 1] if bound == 1 else [0, 1, 2, 3, 4]
        bar = fig.colorbar(im, cax=cax, orientation='horizontal', ticks=ticks)
        bar.ax.set_xticklabels([f'{value:g}' for value in ticks])
        bar.ax.tick_params(labelsize=9, length=3, pad=4)
        bar.outline.set_linewidth(.6)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    horizontal_gaps = []
    for ax, row, col, text in text_objects:
        box = text.get_window_extent(renderer)
        left = ax.transData.transform((col-.5, row))[0]
        right = ax.transData.transform((col+.5, row))[0]
        horizontal_gaps.extend([box.x0-left, right-box.x1])
    min_gap = min(horizontal_gaps)*72/fig.dpi
    assert min_gap > 1, min_gap
    assert min(contrast_ratios) >= 4.5
    stem = OUTPUT / 'Fig05_fuel_model_curing_responses_verified'
    fig.savefig(stem.with_suffix('.pdf'), bbox_inches='tight', pad_inches=.10,
                metadata={'Title': 'Fig. 5: mean final-state treatment outcomes by fuel model and curing state',
                          'Subject': '75 verified means; 64 simulations per cell; consistent C(T), A(T), P(T) notation.'})
    fig.savefig(stem.with_suffix('.png'), dpi=400, bbox_inches='tight', pad_inches=.10)
    plt.close(fig)
    with fitz.open(stem.with_suffix('.pdf')) as doc:
        page = doc[0]
        words = page.get_text('words')
        cells = [word for word in words if re.fullmatch(r'\d\.\d{3}', word[4])]
        assert [word[4] for word in cells] == [record['displayed_value'] for record in records]
        for panel in range(3):
            panel_cells = cells[panel*25:(panel+1)*25]
            for row in range(5):
                centers = [(word[0]+word[2])/2 for word in panel_cells[row*5:(row+1)*5]]
                assert np.all(np.diff(centers) > 0)
            heights = [(panel_cells[row*5][1]+panel_cells[row*5][3])/2 for row in range(5)]
            assert np.all(np.diff(heights) > 0)
        exported = page.get_text()
        for symbol in ['C(T)', 'A(T)', 'P(T)']:
            assert symbol in exported
        assert 'consumption CV' not in exported
        pdf_width = float(page.rect.width)
    pd.DataFrame(records).to_csv(HERE / 'fig5_plotted_values.csv', index=False)
    (HERE / 'verification.json').write_text(json.dumps({'figure': '5', 'status': 'passed', 'source': 'Portable CSV exports', 'reference_values': 'data/reference', 'output_directory': 'outputs/figures'}, indent=2)+'\n', encoding='utf-8')
    print('Generated figure 5; numerical checks passed.')


if __name__ == '__main__':
    main()
