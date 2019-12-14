# https://eshapard.github.io/
#
from __future__ import division
from anki.hooks import addHook
from aqt import mw
from aqt.utils import tooltip
#from aqt.utils import showInfo
import math

targetRatio = 0.85

showCardStats=True #Show the card stats in a pop-up
minRevs = 4 #minium number of reviews before ease factors are adjusted


Q = 1.0  # parameter q defined in eq. 8 in the paper.
T = 10.0  # number of days in the future to generate reviewing timeself.


def intensity(t, n_t, q):
    return 1.0/np.sqrt(q)*(1-np.exp(-n_t*t))


def sampler(n_t, q, T):
    t = 0
    while(True):
        max_int = 1.0/np.sqrt(q)
        t_ = np.random.exponential(1 / max_int)
        if t_ + t > T:
            return None
        t = t+t_
        proposed_int = intensity(t, n_t, q)
        if np.random.uniform(0, 1, 1)[0] < proposed_int / max_int:
return t


def reviewsandresults(cardID):
    reviewtimes = mw.col.db.list("select ease from revlog where cid = ?", cardid)
    reviewresults = mw.col.db.list("select id from revlog where cid = ?", cardid)
    return reviewtimes, reviewresults

def calcNewEase(sRate, avgFactor, curFactor):
    top = int(round(curFactor * 1.2))
    bottom = int(round(curFactor * 0.8))
    #Ebbinghaus formula
    if sRate > 0.99:
        sRate = 0.99 # ln(1) = 0; avoid divide by zero error
    if sRate < 0.01:
        sRate = 0.01
    dRatio = math.log(targetRatio) / math.log(sRate)
    #showInfo("dRatio: %s" % dRatio)
    sugFactor = int(round(avgFactor * dRatio))
    if sugFactor > top:
        sugFactor = top
    if sugFactor < bottom:
        sugFactor = bottom
    return sugFactor

def easeAdjustFunc():
    #cardObj = mw.reviewer.card
    #showInfo("%s" % cardObj)
    queue = mw.reviewer.card.queue
    if queue == 2:
        cardID = mw.reviewer.card.id
        
        reviewtimes, reviewresults = reviewsandresults(cardID)
        
        
        if rev:
            sugFactor = calcNewEase(srate, fac, curFactor)
            
        else: #there were no reviews, so don't change a thing.
            sugFactor = curFactor
            
        #quick sanity checks
        
        if srate < targetRatio and sugFactor > curFactor: sugFactor = curFactor #if under target, decrease factor only
        if srate > targetRatio and sugFactor < curFactor: sugFactor = curFactor #if over target, increase factor only
        if rev:
            if showCardStats: 
                tooltip("cardID: %s\nsRate: %s\navgFactor: %s\ncurFactor: %s\nsugFactor: %s" % (cardID, round(srate,2), round(fac), curFactor, sugFactor))

        #Set new card ease factor
        mw.reviewer.card.factor = sugFactor

addHook('showQuestion', easeAdjustFunc)
