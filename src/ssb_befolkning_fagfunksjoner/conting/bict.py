import time
from dataclasses import dataclass
from typing import Literal, TypeAlias
import math

import numpy as np
import pandas as pd
import glum
import statsmodels.api as sm
import statsmodels.formula.api as smf
from formulaic import Formula, FormulaSpec

PriorTypes: TypeAlias = Literal["SBH", "UIP"]


@dataclass
class BictResult:
    beta: np.ndarray
    model: list[str]
    sig: np.ndarray
    y0: np.ndarray
    missing_idx: pd.Index
    missing_details: pd.DataFrame
    rj_acc: float
    mh_acc: float
    prior: str
    X: pd.DataFrame
    ip: np.ndarray
    eta_hat: np.ndarray
    time_elapsed: float

@dataclass
class PosteriorMode:
    intercept: float


def _validate_input(
    iterations: int,
    null_move_prob: float,
    hyperparam_a: float,
    hyperparam_b: float,
) -> None:
    if iterations <= 0:
        raise ValueError("'iterations' must be positive.")
    if not 0 <= null_move_prob <= 1:
        raise ValueError("null_move_prob must be between 0 and 1")
    if hyperparam_a < 0 and hyperparam_a != -1:
        raise ValueError("'a' must be non-negative.")
    if hyperparam_b < 0:
        raise ValueError("'b' must be non-negative.")


def _log_y(y: np.ndarray, adj: float = 1/6) -> np.ndarray:
    y = y.copy()
    y[y == 0] = adj
    return np.log(y)


def get_posterior_mode(
    y,
    X,
    *,
    prior,
    ip,
    hyperparam_a: float,
    hyperparam_b: float,
) -> PosteriorMode:
    """
    Function finds the posterior mode of the log-linear parameters
    of a log-linear model with a given design matrix and prior distribution.

    Args:
        y: The (n x 1) vector of cell counts.
        X: The (n x p) matrix where n is the number of cells and p is the number of log-linear parameters.
        prior: The prior distribution. One of Unit Information Prior (UIP) or Sabanes-Bove & Held prior (SBH).
            Default is "SBH".
        ip: The (p x p) matrix inverse of the prior scale matrix.
        hyperparam_a: Shape parameter for the SBH prior.
        hyperparam_b: Scale parameter for the SBH prior. 

    """
    log_y = _log_y(y)
    start_beta = sm.OLS(log_y, X - 1).fit()
    p = len(X.columns) - 1
    i_sig = ip.iloc[1:, 1:]  # Dropping first row and first column

    if prior == "UIP":
        # TODO: Continue here
    pass

def bict(
    formula: FormulaSpec,
    df: pd.DataFrame,
    *,
    iterations: int,
    prior: PriorTypes = "SBH",
    save: bool = False,
    filename_prefix: str | None = None,
    null_move_prob: float = 0.5,
    hyperparam_a: float = 0.001,
    hyperparam_b: float = 0.001,
    progress_bar: bool = False,
) -> BictResult:
    """Bayesian Incomplete Contingency Table."""

    _validate_input(iterations, null_move_prob, hyperparam_a, hyperparam_b)

    t0 = time.time()

    # Fit the model to 
    df = pd.DataFrame(
        {
            "y": [1, 2, None, 4, 5],
            "x1": ["a", "b", "c", None, "e"],
            "x2": ["1", "0", "0", "1", None]
        }
    )
    formula = "y ~ C(x1, contr.sum) + C(x2, contr.sum)"
    y, X = Formula(formula).get_model_matrix(
        data=df, 
        na_action="ignore",
    )
    y_var = y.model_spec.terms[0]
    missing_details = df[df[y_var].isna()]

    y = y.fillna(0)
    ip = X.values.T @ X.values / len(y)
    ip[:, 0] = 0  # Fill intercept with nulls

    X[df[y_var].isna()]

    get_posterior_mode(
        X=X[df[y_var].isna()],
        y=y[df[y_var].isna()],
        prior=prior,
        ip=ip,
        hyperparam_a=hyperparam_a,
        hyperparam_b=hyperparam_b,
    )
