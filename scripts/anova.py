"""Orthogonal ANOVA calculation for the complete balanced factorial.

Called by the analysis pipeline; never changes source data.
For the verified complete balanced factorial, orthogonal marginal contrasts
give Type II sums of squares. Cross-check group-mean decomposition against
least-squares regression using centered orthonormal categorical contrasts.
The six selected two-way interactions match Codes/Paper_1.ipynb cell 50.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

FACTORS = ['fuel_model', 'curing_state', 'ignition_family',
           'ignition_structure', 'wind_speed_mph', 'surface_moisture']
LABELS = dict(zip(FACTORS, ['Fuel model', 'Curing state', 'Ignition family',
                          'Ignition structure', 'Wind speed', 'Surface moisture']))
PAIRS = [('fuel_model', 'curing_state'), ('curing_state', 'ignition_family'),
         ('fuel_model', 'ignition_family'), ('fuel_model', 'wind_speed_mph'),
         ('fuel_model', 'surface_moisture'), ('wind_speed_mph', 'surface_moisture')]
RESPONSES = {'consumption_fraction_surface': 'Consumption',
             'active_consumed_area_fraction_1pct': 'Active area',
             'cell_consumption_cv': 'Patchiness'}


def calculate(data, name):
    factors = [f for f in FACTORS if data[f].nunique() > 1]
    sizes = data.groupby(factors).size()
    assert len(sizes) == np.prod([data[f].nunique() for f in factors])
    assert sizes.nunique() == 1
    n = len(data)
    # Independent regression design, with centered orthonormal level contrasts.
    blocks, codes = {}, {}
    for f in factors:
        cat = pd.Categorical(data[f], categories=sorted(data[f].unique()))
        k = len(cat.categories)
        centered = np.eye(k) - np.ones((k, k))/k
        contrasts = np.linalg.qr(centered[:, :-1])[0]
        codes[f] = contrasts[cat.codes]
        blocks[f] = codes[f]
    for a, b in PAIRS:
        blocks[a+':'+b] = (codes[a][:, :, None]*codes[b][:, None, :]).reshape(n, -1)
    X = np.column_stack([np.ones(n)] + list(blocks.values()))
    gram = X.T @ X
    assert np.max(np.abs(gram - np.diag(np.diag(gram)))) < 1e-9
    columns = {}; start = 1
    for term, block in blocks.items():
        columns[term] = slice(start, start+block.shape[1])
        start += block.shape[1]
    rows, checks = [], []
    for response, response_label in RESPONSES.items():
        values = data[response].to_numpy(dtype=float)
        mean = values.mean()
        total_ss = np.sum((values-mean)**2)
        ss, dfs = {}, {}
        for f in factors:
            g = data.groupby(f)[response].agg(['mean', 'size'])
            ss[f] = float(np.sum(g['size']*(g['mean']-mean)**2))
            dfs[f] = len(g)-1
        for a, b in PAIRS:
            g = data.groupby([a, b])[response].agg(['mean', 'size']).reset_index()
            deviation = (g['mean']-g[a].map(data.groupby(a)[response].mean())
                         -g[b].map(data.groupby(b)[response].mean())+mean)
            term = a+':'+b
            ss[term] = float(np.sum(g['size']*deviation**2))
            dfs[term] = (data[a].nunique()-1)*(data[b].nunique()-1)
        residual_df = n-1-sum(dfs.values())
        residual_ss = total_ss-sum(ss.values())
        mse = residual_ss/residual_df
        beta, _, rank, _ = np.linalg.lstsq(X, values, rcond=None)
        assert rank == X.shape[1]
        residual_ols = values-X @ beta
        ols_ss_resid = float(residual_ols @ residual_ols)
        assert np.isclose(residual_ss, ols_ss_resid, rtol=1e-12, atol=1e-11)
        discrepancies = []
        for term in ss:
            part = X[:, columns[term]] @ beta[columns[term]]
            ss_ols = float(part @ part)
            omega = max(0., (ss[term]-dfs[term]*mse)/(total_ss+mse))
            mse_ols = ols_ss_resid/residual_df
            omega_ols = max(0., (ss_ols-dfs[term]*mse_ols)/(total_ss+mse_ols))
            discrepancies.append(abs(omega-omega_ols))
            assert np.isclose(ss[term], ss_ols, rtol=1e-11, atol=1e-10)
            label = ' × '.join(LABELS[f] for f in term.split(':'))
            if ':' in term:
                # Existing archives use lower case after the interaction sign.
                a, b = term.split(':')
                label = LABELS[a]+' × '+LABELS[b].lower()
            rows.append(dict(analysis=name, response=response, metric=response_label,
                             term=term, term_clean=label, sum_sq=ss[term],
                             df=dfs[term], omega_sq=omega, omega_sq_ols=omega_ols))
        checks.append(dict(analysis=name, response=response, n=n,
                           model_rank=int(rank), residual_df=int(residual_df),
                           total_ss=float(total_ss), residual_ss=float(residual_ss),
                           mean_square_residual=float(mse),
                           max_omega_difference_between_methods=max(discrepancies)))
    return pd.DataFrame(rows), checks

