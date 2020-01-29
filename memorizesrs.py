# -*- coding: utf-8 -*-
from typing import Callable
from math import sqrt, log, inf
from random import expovariate, random


def schedule(timeToRecallProb: Callable[[float], float], q: float, T: float, rng=None):
    """Suggest a due date for flashcard given its time-varying probability of recall
  
    Inputs:
    - `timeToRecallProb` function that returns recall probability at any given time
    - `q` tunable parameter balancing forgetting versus high review rates
    - `T` maximum time horizon (may be `math.inf`)
    - `rng` an instance of `random.Random`, or `None` for default random number generator
    Returns a time in the future to schedule this item *or* `inf` if the item should not be
    scheduled within `T` time units.
    Note that "time" here means "units from now", and "now" means 0. The average value
    returned by this function will be `>= sqrt(q)` (though of course the minimum value is 0
    and the maximum finite value is `T`).
    Implements the Memorize algorithm from "Enhancing human learning via spaced
    repetition optimization" by Behzad Tabibian, Utkarsh Upadhyay, Abir De, Ali
    Zarezade, Bernhard Schölkopf, and Manuel Gomez-Rodriguez in PNAS, 2019.
    See https://doi.org/10.1073/pnas.1815156116 and http://learning.mpi-sws.org/memorize/
    """
    maxIntensity = 1.0 / sqrt(q)
    expo = expovariate if rng is None else rng.expovariate
    unif = random if rng is None else rng.random
    t = expo(maxIntensity)
    while t <= T:
        p = timeToRecallProb(t)
        assert p >= 0 and p <= 1
        if unif() < (1 - p):
            return t
        t += expo(maxIntensity)
    return inf
