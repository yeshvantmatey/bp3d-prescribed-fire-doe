"""Reproduce corrected manuscript figure 9 and 10.

Run python run_all.py from the repository root to calculate prerequisites.
"""
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'outputs/fig9_fig10'
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
from matplotlib.ticker import PercentFormatter
import fitz

LAYOUTS = ['Strip_Broken', 'Strip_Dot', 'Flank_Broken', 'Flank_Dot']
LABELS = [layout.replace('_', ' ') for layout in LAYOUTS]
# Darker versions of the orange, purple, blue and green hues used in Fig. 8.
COLORS = ['#B86E00', '#8957A3', '#00759B', '#557E1E']
STYLES = ['-', '--', '-.', ':']
CASES = [('GS2', 'spring_after_greenup'), ('SH2', 'spring_after_greenup'),
         ('GS2', 'early_summer_senescence'), ('SH5', 'early_summer_senescence')]
CASE_TITLES = ['GS2: spring after green-up', 'SH2: spring after green-up',
               'GS2: early-summer senescence', 'SH5: early-summer senescence']


def check_equal(actual, expected, tolerance=1e-11):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=tolerance,
                               equal_nan=True)


def style_axis(ax):
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['bottom', 'left']].set_color('#777777')
    ax.spines[['bottom', 'left']].set_linewidth(.6)
    ax.tick_params(width=.6, length=3, color='#777777')
    ax.set_axisbelow(True)


def save_figure(fig, stem, title):
    fig.savefig(stem.with_suffix('.pdf'), bbox_inches='tight', pad_inches=.10,
                metadata={'Title': title,
                          'Subject': 'Verified CSV values; elapsed time and consumption AUC in minutes.'})
    fig.savefig(stem.with_suffix('.png'), dpi=400, bbox_inches='tight', pad_inches=.10)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    seconds_per_output = 60.0
    minutes_per_output = seconds_per_output / 60.0
    summary = pd.read_csv(TABLES / 'temporal_layout_summary.csv').set_index('ignition_pattern').loc[LAYOUTS]
    recomputed = pd.read_csv(REFERENCE / 'fig9_temporal_layout_summary.csv').set_index('ignition_pattern').loc[LAYOUTS]
    assert summary.n_runs.eq(400).all()
    fields = ['mean_final_consumption', 'reached_t50_consumption',
              'median_t50_consumption', 'mean_auc_consumption']
    for field in fields:
        check_equal(summary[field], recomputed[field])
    counts = recomputed.n_reached_t50_consumption.to_numpy(dtype=int)
    assert counts.tolist() == [189, 175, 82, 105]
    reach_percent = summary.reached_t50_consumption.to_numpy() * 100
    check_equal(reach_percent, 100 * counts / 400)
    time_minutes = summary.median_t50_consumption.to_numpy() * minutes_per_output
    auc_minutes = summary.mean_auc_consumption.to_numpy() * minutes_per_output
    check_equal(time_minutes, [23, 23, 37, 38])
    values = [summary.mean_final_consumption.to_numpy(), reach_percent, time_minutes, auc_minutes]
    formats = [lambda v: f'{v:.3f}', lambda v: f'{v:.2f}%',
               lambda v: f'{v:.0f}', lambda v: f'{v:.3f}']
    titles = ['(a) Final consumption', '(b) Threshold attainment',
              '(c) Time to 50% consumption', '(d) Consumption AUC']
    xlabels = [r'Mean $C(T)$', 'Runs reaching 50% consumption (%)',
               'Median time to 50% consumption (min)', r'Mean $\mathrm{AUC}_{C}$ (min)']
    limits = [(0, .65), (0, 65), (0, 50), (0, 26)]
    ticks = [[0, .2, .4, .6], [0, 20, 40, 60], [0, 10, 20, 30, 40, 50], [0, 5, 10, 15, 20]]

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.titlesize': 10, 'axes.labelsize': 9,
                         'xtick.labelsize': 8.5, 'ytick.labelsize': 9,
                         'pdf.fonttype': 42, 'ps.fonttype': 42,
                         'axes.unicode_minus': False})
    fig9, axes9 = plt.subplots(2, 2, figsize=(8.2, 4.65))
    fig9.subplots_adjust(left=.15, right=.97, bottom=.12, top=.92,
                         wspace=.67, hspace=.70)
    annotations = []
    bars_audit = []
    for panel, (ax, data, formatter, title, xlabel, limit, tick) in enumerate(
            zip(axes9.flat, values, formats, titles, xlabels, limits, ticks)):
        bars = ax.barh(np.arange(4), data, height=.57, color=COLORS, zorder=3)
        ax.set_yticks(np.arange(4), LABELS)
        ax.invert_yaxis()
        ax.set_xlim(*limit)
        ax.set_xticks(tick)
        ax.set_xlabel(xlabel, labelpad=7, fontsize=8.6)
        ax.set_title(title, loc='left', pad=11)
        if panel == 1:
            ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.grid(axis='x', color='#E1E1E1', linewidth=.55)
        ax.tick_params(axis='y', length=0)
        style_axis(ax)
        for layout, bar, value in zip(LAYOUTS, bars, data):
            label = formatter(value)
            text = ax.annotate(label, (value, bar.get_y()+bar.get_height()/2),
                               xytext=(4, 0), textcoords='offset points',
                               va='center', ha='left', fontsize=8.7)
            annotations.append((panel, label, text))
            bars_audit.append({'panel': 'abcd'[panel], 'layout': layout,
                               'plotted_value': float(bar.get_width()), 'label': label})
        check_equal([bar.get_width() for bar in bars], data)
    fig9.canvas.draw()
    renderer = fig9.canvas.get_renderer()
    min_gap = min(axes9.flat[panel].get_window_extent(renderer).x1 - text.get_window_extent(renderer).x1
                  for panel, label, text in annotations)
    assert min_gap > 2, f'Annotation exceeds axis boundary: {min_gap}'
    stem9 = OUTPUT / 'Fig09_temporal_summary_verified'
    save_figure(fig9, stem9, 'Fig. 9: consumption development by ignition layout')
    with fitz.open(stem9.with_suffix('.pdf')) as doc:
        exported_text9 = doc[0].get_text()
        assert 'Time index' not in exported_text9 and 'Fraction of runs' not in exported_text9
        for panel, label, text in annotations:
            assert label in exported_text9, f'Missing exported annotation: {label}'
        assert exported_text9.count('(min)') == 2
    plt.close(fig9)

    curves = pd.read_csv(TABLES / 'condition_layout_curves.csv')
    verified_curves = pd.read_csv(REFERENCE / 'fig10_curve_points.csv')
    keys = ['fuel_model', 'curing_state', 'ignition_pattern', 'time_index']
    curves = curves.merge(verified_curves[keys + ['mean_consumption_t']],
                          on=keys, suffixes=('', '_verified'), validate='one_to_one')
    assert len(curves) == 976 and curves.n_runs.eq(16).all()
    check_equal(curves.mean_consumption_t, curves.mean_consumption_t_verified)
    fig10, axes10 = plt.subplots(2, 2, figsize=(8.2, 4.8), sharex=True, sharey=True)
    fig10.subplots_adjust(left=.09, right=.98, bottom=.21, top=.92,
                          wspace=.24, hspace=.43)
    plotted_curves = []
    for panel, (ax, case, title) in enumerate(zip(axes10.flat, CASES, CASE_TITLES)):
        fuel, curing = case
        for layout, label, color, linestyle in zip(LAYOUTS, LABELS, COLORS, STYLES):
            data = curves.loc[(curves.fuel_model == fuel) &
                              (curves.curing_state == curing) &
                              (curves.ignition_pattern == layout)].sort_values('time_index')
            assert len(data) == 61 and np.array_equal(data.time_index, np.arange(61))
            time = data.time_index.to_numpy() * minutes_per_output
            mean = data.mean_consumption_t.to_numpy()
            line, = ax.plot(time, mean, label=label, color=color, linestyle=linestyle,
                            linewidth=1.8, solid_capstyle='round')
            check_equal(line.get_xdata(), time)
            check_equal(line.get_ydata(), data.mean_consumption_t_verified)
            plotted_curves.append({'panel': 'abcd'[panel], 'fuel_model': fuel,
                                   'curing_state': curing, 'layout': layout,
                                   'n_runs_per_point': 16, 'time_minutes': time.tolist(),
                                   'mean_consumption': mean.tolist()})
        ax.set_title(f'({"abcd"[panel]}) {title}', loc='left', pad=10, fontsize=9.5)
        ax.set_xlim(0, 60)
        ax.set_ylim(0, 1)
        ax.set_xticks(np.arange(0, 61, 10))
        ax.set_yticks(np.arange(0, 1.01, .2))
        ax.grid(color='#E1E1E1', linewidth=.55)
        style_axis(ax)
        if panel % 2 == 0:
            ax.set_ylabel(r'Mean $C(t)$', labelpad=7)
        if panel >= 2:
            ax.set_xlabel('Elapsed simulation time (min)', labelpad=7)
    handles, legend_labels = axes10[0, 0].get_legend_handles_labels()
    fig10.legend(handles, legend_labels, loc='lower center', bbox_to_anchor=(.54, .025),
                 ncol=4, frameon=False, fontsize=9, handlelength=2.9,
                 columnspacing=1.7)
    stem10 = OUTPUT / 'Fig10_consumption_trajectories_verified'
    save_figure(fig10, stem10, 'Fig. 10: selected mean consumption trajectories')
    with fitz.open(stem10.with_suffix('.pdf')) as doc:
        exported_text10 = doc[0].get_text()
        assert 'Time index' not in exported_text10
        assert exported_text10.count('Elapsed simulation time (min)') == 2
        for title in CASE_TITLES:
            assert title in exported_text10, title
        for label in LABELS:
            assert label in exported_text10, label
    plt.close(fig10)

    summary.assign(reach_50_percent=reach_percent,
                   median_time_to_50_min=time_minutes,
                   mean_consumption_auc_min=auc_minutes).to_csv(HERE / 'fig9_plotted_values.csv')
    curves.assign(elapsed_time_min=curves.time_index * minutes_per_output).drop(
        columns='mean_consumption_t_verified').to_csv(HERE / 'fig10_plotted_curves.csv', index=False)
    (HERE / 'verification.json').write_text(json.dumps({'figure': '9_fig10', 'status': 'passed', 'source': 'Portable CSV exports', 'reference_values': 'data/reference', 'output_directory': 'outputs/figures'}, indent=2)+'\n', encoding='utf-8')
    print('Generated figure 9 and 10; numerical checks passed.')


if __name__ == '__main__':
    main()
