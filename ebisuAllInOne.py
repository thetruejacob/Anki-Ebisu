
# -*- coding: utf-8 -*-

## logsumexp.py

from math import exp, log


def logsumexp(a, b):
    a_max = max(a)
    s = 0
    for i in range(len(a) - 1, -1, -1):
      s += b[i] * exp(a[i] - a_max)
    sgn = 1 if s >= 0 else 0
    s *= sgn
    out = log(s) + a_max
    return [out, sgn]


## gamma.py

from math import nan, log, pi, sin, exp, sqrt, pow
g = 7
p = [
      0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
      -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
      1.5056327351493116e-7
]

g_ln = 607 / 128.0
p_ln = [
      0.99999999999999709182, 57.156235665862923517, -59.597960355475491248, 14.136097974741747174,
      -0.49191381609762019978, 0.33994649984811888699e-4, 0.46523628927048575665e-4,
      -0.98374475304879564677e-4, 0.15808870322491248884e-3, -0.21026444172410488319e-3,
      0.21743961811521264320e-3, -0.16431810653676389022e-3, 0.84418223983852743293e-4,
      -0.26190838401581408670e-4, 0.36899182659531622704e-5
]

HALF_LOG_2_PI = .5 * log(2 * pi)
SQRT_2_PI = sqrt(2 * pi)


# Spouge approximation (suitable for large arguments)
def gammaln(z):
    if (z < 0):
      return nan
    x = p_ln[0]
    for i in range(len(p_ln) - 1, 0, -1):
      x += p_ln[i] / (z + i)
    t = z + g_ln + 0.5
    return HALF_LOG_2_PI + (z + .5) * log(t) - t + log(x) - log(z)


def gamma(z):
    if (z < 0.5):
      return pi / (sin(pi * z) * gamma(1 - z))
    elif (z > 100):
      return exp(gammaln(z))
    else:
      z -= 1
      x = p[0]
      for i in range(1, g + 2):
        x += p[i] / (z + i)
      t = z + g + 0.5
      return SQRT_2_PI * pow(t, z + 0.5) * exp(-t) * x


## mingolden.py

from math import sqrt, isnan
PHI_RATIO = 2 / (1 + sqrt(5))


def mingolden(f, xL, xU, tol=1e-8, maxIterations=100):
    iteration = 1
    x1 = xU - PHI_RATIO * (xU - xL)
    x2 = xL + PHI_RATIO * (xU - xL)
    f1 = f(x1)
    f2 = f(x2)
    f10 = f(xL)
    f20 = f(xU)
    xL0 = xL
    xU0 = xU
    while (iteration < maxIterations and abs(xU - xL) > tol):
      if (f2 > f1):
        xU = x2
        x2 = x1
        f2 = f1
        x1 = xU - PHI_RATIO * (xU - xL)
        f1 = f(x1)
      else:
        xL = x1
        x1 = x2
        f1 = f2
        x2 = xL + PHI_RATIO * (xU - xL)
        f2 = f(x2)
    iteration += 1

    xF = 0.5 * (xU + xL)
    fF = 0.5 * (f1 + f2)

    if (f10 < fF):
      argmin = xL0
    elif (f20 < fF):
      argmin = xU0
    else:
      argmin = xF

    return dict(
        iterations=iteration,
        argmin=argmin,
        minimum=fF,
        converged=not (isnan(f2) or isnan(f1) or iteration == maxIterations))


def predictRecall(prior, tnow, exact=False):
    """Expected recall probability now, given a prior distribution on it. 🍏
    `prior` is a tuple representing the prior distribution on recall probability
    after a specific unit of time has elapsed since this fact's last review.
    Specifically,  it's a 3-tuple, `(alpha, beta, t)` where `alpha` and `beta`
    parameterize a Beta distribution that is the prior on recall probability at
    time `t`.
    `tnow` is the *actual* time elapsed since this fact's most recent review.
    Optional keyword parameter `exact` makes the return value a probability,
    specifically, the expected recall probability `tnow` after the last review: a
    number between 0 and 1. If `exact` is false (the default), some calculations
    are skipped and the return value won't be a probability, but can still be
    compared against other values returned by this function. That is, if

    > predictRecall(prior1, tnow1, exact=True) < predictRecall(prior2, tnow2, exact=True)
    then it is guaranteed that
    > predictRecall(prior1, tnow1, exact=False) < predictRecall(prior2, tnow2, exact=False)

    The default is set to false for computational efficiency.
    See README for derivation.
    """
    from math import exp
    a, b, t = prior
    dt = tnow / t
    ret = _betalnRatio(a + dt, a, b)
    return exp(ret) if exact else ret


from functools import lru_cache


@lru_cache(maxsize=None)
def _gammalnCached(x):
    return gammaln(x)


def _betalnRatio(a1, a, b):
    return gammaln(a1) - gammaln(a1 + b) + _gammalnCached(a + b) - _gammalnCached(a)


def betaln(a, b):
    return _gammalnCached(a) + _gammalnCached(b) - _gammalnCached(a + b)


def updateRecall(prior, result, tnow, rebalance=True, tback=None):
    """Update a prior on recall probability with a quiz result and time. 🍌
    `prior` is same as in `ebisu.predictRecall`'s arguments: an object
    representing a prior distribution on recall probability at some specific time
    after a fact's most recent review.
    `result` is truthy for a successful quiz, falsy otherwise.
    `tnow` is the time elapsed between this fact's last review and the review
    being used to update.
    (The keyword arguments `rebalance` and `tback` are intended for internal use.)
    Returns a new object (like `prior`) describing the posterior distribution of
    recall probability at `tback` (which is an optional input, defaults to `tnow`).
    """
    from math import exp

    (alpha, beta, t) = prior
    if tback is None:
      tback = t
    dt = tnow / t
    et = tnow / tback

    if result:

      if tback == t:
        proposed = alpha + dt, beta, t
        return _rebalace(prior, result, tnow, proposed) if rebalance else proposed

      logmean = _betalnRatio(alpha + dt / et * (1 + et), alpha + dt, beta)
      logm2 = _betalnRatio(alpha + dt / et * (2 + et), alpha + dt, beta)
      mean = exp(logmean)
      var = _subexp(logm2, 2 * logmean)

    else:

      logDenominator = _logsubexp(betaln(alpha, beta), betaln(alpha + dt, beta))
      mean = _subexp(
          betaln(alpha + dt / et, beta) - logDenominator,
          betaln(alpha + dt / et * (et + 1), beta) - logDenominator)
      m2 = _subexp(
          betaln(alpha + 2 * dt / et, beta) - logDenominator,
          betaln(alpha + dt / et * (et + 2), beta) - logDenominator)
      assert m2 > 0
      var = m2 - mean**2

    assert mean > 0
    assert var > 0
    newAlpha, newBeta = _meanVarToBeta(mean, var)
    proposed = newAlpha, newBeta, tback
    return _rebalace(prior, result, tnow, proposed) if rebalance else proposed


def _rebalace(prior, result, tnow, proposed):
    newAlpha, newBeta, _ = proposed
    if (newAlpha > 2 * newBeta or newBeta > 2 * newAlpha):
      roughHalflife = modelToPercentileDecay(proposed, coarse=True)
      return updateRecall(prior, result, tnow, rebalance=False, tback=roughHalflife)
    return proposed


def _logsubexp(a, b):
    """Evaluate `log(exp(a) - exp(b))` preserving accuracy.

    Subtract log-domain numbers and return in the log-domain.
    Wraps `scipy.special.logsumexp`.
    """
    return logsumexp([a, b], b=[1, -1])[0]


def _subexp(x, y):
    """Evaluates `exp(x) - exp(y)` a bit more accurately than that. ⚾️
    Subtract log-domain numbers and return in the *linear* domain.
    Similar to `scipy.special.logsumexp` except without the final `log`.
    """
    from math import exp
    maxval = max(x, y)
    return exp(maxval) * (exp(x - maxval) - exp(y - maxval))


def _meanVarToBeta(mean, var):
    """Fit a Beta distribution to a mean and variance."""
    # [betaFit] https://en.wikipedia.org/w/index.php?title=Beta_distribution&oldid=774237683#Two_unknown_parameters
    tmp = mean * (1 - mean) / var - 1
    alpha = mean * tmp
    beta = (1 - mean) * tmp
    return alpha, beta


def modelToPercentileDecay(model, percentile=0.5, coarse=False):
    """When will memory decay to a given percentile? 🏀
    
    Given a memory `model` of the kind consumed by `predictRecall`,
    etc., and optionally a `percentile` (defaults to 0.5, the
    half-life), find the time it takes for memory to decay to
    `percentile`. If `coarse`, the returned time (in the same units as
    `model`) is approximate.
    """
    # Use a root-finding routine in log-delta space to find the delta that
    # will cause the GB1 distribution to have a mean of the requested quantile.
    # Because we are using well-behaved normalized deltas instead of times, and
    # owing to the monotonicity of the expectation with respect to delta, we can
    # quickly scan for a rough estimate of the scale of delta, then do a finishing
    # optimization to get the right value.

    assert (percentile > 0 and percentile < 1)
    from math import log, exp
    alpha, beta, t0 = model
    logBab = betaln(alpha, beta)
    logPercentile = log(percentile)

    def f(lndelta):
      logMean = betaln(alpha + exp(lndelta), beta) - logBab
      return logMean - logPercentile

    # Scan for a bracket.
    bracket_width = 1.0 if coarse else 6.0
    blow = -bracket_width / 2.0
    bhigh = bracket_width / 2.0
    flow = f(blow)
    fhigh = f(bhigh)
    while flow > 0 and fhigh > 0:
      # Move the bracket up.
      blow = bhigh
      flow = fhigh
      bhigh += bracket_width
      fhigh = f(bhigh)
    while flow < 0 and fhigh < 0:
      # Move the bracket down.
      bhigh = blow
      fhigh = flow
      blow -= bracket_width
      flow = f(blow)

    assert flow > 0 and fhigh < 0

    if coarse:
      return (exp(blow) + exp(bhigh)) / 2 * t0

    sol = mingolden(lambda x: abs(f(x)), blow, bhigh)
    if not sol['converged']:
      raise ValueError('minimization failed to converge')
    t1 = exp(sol['argmin']) * t0
    return t1


def defaultModel(t, alpha=3.0, beta=None):
    """Convert recall probability prior's raw parameters into a model object. 🍗
    `t` is your guess as to the half-life of any given fact, in units that you
    must be consistent with throughout your use of Ebisu.
    `alpha` and `beta` are the parameters of the Beta distribution that describe
    your beliefs about the recall probability of a fact `t` time units after that
    fact has been studied/reviewed/quizzed. If they are the same, `t` is a true
    half-life, and this is a recommended way to create a default model for all
    newly-learned facts. If `beta` is omitted, it is taken to be the same as
    `alpha`.
    """
    return (alpha, beta or alpha, t)
