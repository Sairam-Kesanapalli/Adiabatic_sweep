"""
The energy model shared by check_calibration.py and check_lc_scaling.py.

    E(T) = K*g(T, tau) + b + c*T

T = TPHASE (ns), E in fJ.  g is the exact loss of one RC ramp of duration
T in units of C*V^2 (-> tau/T when T >> tau), so a = K*tau is the familiar
1/T coefficient; b is a fixed (non-adiabatic) residue and c*T is leakage.

Standard library only.
"""
import math


def solve(A, y):
    """Gaussian elimination with partial pivoting, small dense systems"""
    n = len(y)
    M = [row[:] + [y[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][k] * x[k] for k in range(r + 1, n))) / M[r][r]
    return x

def lstsq(cols, y, w=None):
    """least squares y ~ sum_j p_j*cols[j], optional per-point weights"""
    w = w or [1.0] * len(y)
    A = [[sum(w[i] ** 2 * ci[i] * cj[i] for i in range(len(y))) for cj in cols] for ci in cols]
    b = [sum(w[i] ** 2 * ci[i] * y[i] for i in range(len(y))) for ci in cols]
    return solve(A, b)

def line_fit(x, y):
    slope, icpt = lstsq([x, [1.0] * len(x)], y)
    return slope, icpt

def g(T, tau):
    """loss of one RC ramp of duration T, in units of C*V^2"""
    r = tau / T
    return r * (1 - r * (1 - math.exp(-T / tau)))

def fit_energy(T, E, with_b, tau_max=5.0):
    """best tau on a log grid 0.01 .. tau_max ns; K, c (and b) by
    relative-error least squares"""
    best = None
    w = [1 / e for e in E]
    span = tau_max / 0.01
    for i in range(1200):
        tau = 0.01 * (span ** (i / 1199))
        cols = [[g(t, tau) for t in T], list(T)] + ([[1.0] * len(T)] if with_b else [])
        p = lstsq(cols, E, w)
        pred = [sum(p[j] * cols[j][k] for j in range(len(cols))) for k in range(len(T))]
        rel = [pk / ek - 1 for pk, ek in zip(pred, E)]
        rms = math.sqrt(sum(r * r for r in rel) / len(rel))
        if best is None or rms < best["rms"]:
            best = dict(tau=tau, K=p[0], c=p[1], b=p[2] if with_b else 0.0,
                        rms=rms, max=max(abs(r) for r in rel))
    best["a"] = best["K"] * best["tau"]                  # fJ*ns
    return best
