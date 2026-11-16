"""Reproduce corrected manuscript figure 6.

Run python run_all.py from the repository root to calculate prerequisites.
"""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'outputs/fig6'
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
import fitz

FUELS = ['GR2', 'GS1', 'GS2', 'SH2', 'SH5']
COLORS = ['#0072B2', '#D17A00', '#008760', '#C64D16', '#9C5AA2']
MARKERS = ['o', 's', '^', 'D', 'v']
STYLES = ['-', '--', '-.', ':', (0, (5, 1, 1, 1))]


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA / 'doe_analysis_ready_response_table.csv')
    assert len(data) == 1600 and data.run_id.is_unique
    factor = Decimal('0.44704')
    wind_levels = np.array([1., 4., 8., 12.])
    exact_winds = np.array([float(Decimal(str(x)) * factor) for x in wind_levels])
    display_winds = [f'{x:.2f}' for x in exact_winds]
    assert display_winds == ['0.45', '1.79', '3.58', '5.36']
    moisture_levels = np.array([.06, .08, .10, .12])
    moisture_percent = moisture_levels * 100
    np.testing.assert_array_equal(moisture_percent, [6, 8, 10, 12])

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.titlesize': 10, 'axes.labelsize': 9,
                         'xtick.labelsize': 9, 'ytick.labelsize': 9,
                         'pdf.fonttype': 42, 'ps.fonttype': 42,
                         'axes.unicode_minus': False})
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.8), sharey=True)
    fig.subplots_adjust(left=.085, right=.98, bottom=.32, top=.89, wspace=.28)
    points = []
    point_errors = []
    for panel, (ax, field, levels, xvalues, name) in enumerate(zip(
            axes, ['wind_speed_mph', 'surface_moisture'],
            [wind_levels, moisture_levels], [exact_winds, moisture_percent],
            ['wind', 'moisture'])):
        verified = pd.read_csv(REFERENCE / f'verified_{name}_response_by_fuel_model.csv')
        keys = ['fuel_model', field]
        recalculated = data.groupby(keys).agg(
            mean_C_T=('consumption_fraction_surface', 'mean'),
            n_runs=('run_id', 'size')).reset_index()
        matched = verified.merge(recalculated, on=keys, suffixes=('_verified', '_new'),
                                 validate='one_to_one')
        assert len(matched) == 20
        assert matched.n_runs_verified.eq(80).all() and matched.n_runs_new.eq(80).all()
        np.testing.assert_allclose(matched.mean_C_T_verified, matched.mean_C_T_new,
                                   rtol=0, atol=1e-14)
        for fuel, color, marker, style in zip(FUELS, COLORS, MARKERS, STYLES):
            rows = recalculated[recalculated.fuel_model.eq(fuel)].sort_values(field)
            np.testing.assert_array_equal(rows[field], levels)
            response = rows.mean_C_T.to_numpy()
            line, = ax.plot(xvalues, response, label=fuel, color=color,
                            marker=marker, markersize=4.6, markerfacecolor='white',
                            markeredgewidth=1.15, linestyle=style, linewidth=1.5,
                            clip_on=False)
            np.testing.assert_array_equal(line.get_xdata(), xvalues)
            np.testing.assert_array_equal(line.get_ydata(), response)
            point_errors.append(float(np.max(np.abs(line.get_ydata() - response))))
            for original_x, plotted_x, y in zip(levels, xvalues, response):
                points.append({'panel': 'ab'[panel], 'fuel_model': fuel,
                               'original_input_field': field, 'original_input_value': float(original_x),
                               'displayed_input_unit': 'm/s' if panel == 0 else '%',
                               'plotted_x': float(plotted_x), 'mean_C_T': float(y), 'n_runs': 80})
        ax.set_title(['(a) Wind-speed response', '(b) Surface fuel-moisture response'][panel],
                     loc='left', pad=10)
        ax.set_ylim(0, .6)
        ax.set_yticks(np.arange(0, .61, .1))
        ax.set_ylabel(r'Mean $C(T)$', labelpad=7)
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='#DDDDDD', linewidth=.55)
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['bottom', 'left']].set_color('#777777')
        ax.spines[['bottom', 'left']].set_linewidth(.6)
        ax.tick_params(width=.6, length=3, color='#777777', labelleft=True)
        if panel == 0:
            ax.set_xticks(exact_winds, display_winds)
            ax.set_xlim(exact_winds[0]-.23, exact_winds[-1]+.23)
            ax.set_xlabel(r'Wind speed (m s$^{-1}$)', labelpad=8)
        else:
            ax.set_xticks(moisture_percent, [str(int(x)) for x in moisture_percent])
            ax.set_xlim(5.7, 12.3)
            ax.set_xlabel('Surface fuel moisture (%)', labelpad=8)
    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, title='Fuel model', loc='lower center',
                        bbox_to_anchor=(.53, .005), ncol=5, frameon=False,
                        fontsize=9, title_fontsize=9, columnspacing=1.8,
                        handlelength=3.1)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label_bottom = min(ax.xaxis.label.get_window_extent(renderer).y0 for ax in axes)
    legend_top = legend.get_window_extent(renderer).y1
    assert label_bottom - legend_top > 5

    stem = OUTPUT / 'Fig06_wind_moisture_response_SI'
    fig.savefig(stem.with_suffix('.pdf'), bbox_inches='tight', pad_inches=.10,
                metadata={'Title': 'Fig. 6: wind and surface fuel-moisture responses',
                          'Subject': 'Verified 80-run means; nominal wind inputs in m/s and moisture in percent.'})
    fig.savefig(stem.with_suffix('.png'), dpi=400, bbox_inches='tight', pad_inches=.10)
    plt.close(fig)
    with fitz.open(stem.with_suffix('.pdf')) as doc:
        exported = doc[0].get_text()
        assert len(doc) == 1
        for label in display_winds + FUELS + ['Surface fuel moisture (%)', 'Wind speed']:
            assert label in exported, label
        assert 'mph' not in exported
        assert exported.count('Mean C(T)') == 2
    pd.DataFrame(points).to_csv(HERE / 'fig6_plotted_values.csv', index=False)
    (HERE / 'verification.json').write_text(json.dumps({'figure': '6', 'status': 'passed', 'source': 'Portable CSV exports', 'reference_values': 'data/reference', 'output_directory': 'outputs/figures'}, indent=2)+'\n', encoding='utf-8')
    print('Generated figure 6; numerical checks passed.')


if __name__ == '__main__':
    main()
