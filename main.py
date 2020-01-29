from __future__ import division
from anki.hooks import addHook
from aqt import mw
from aqt.utils import tooltip

import sys
import os
import sqlite3
import ebisu
from .memorizesrs import schedule
from .ebisu import *
from datetime import datetime, timedelta
from math import inf


def ResultsandTimes(cardID):
    reviewResults = mw.col.db.list("SELECT ease FROM revlog WHERE cid = ?", cardID) 
    reviewTimes = mw.col.db.list("SELECT id FROM revlog WHERE cid = ?", cardID)
    
    return [ease != 1 for ease in reviewResults], [datetime.fromtimestamp(time / 1000.00) for time in reviewTimes]

def historyToEbisuModel(learnTime, reviewTimes, reviewResults, initialModel = ebisu.defaultModel(0.25,3)):
    previousTime, model = learnTime, initialModel
    
    for (reviewTime, result) in zip(reviewTimes, reviewResults):
        model = ebisu.updateRecall(model, result, (reviewTime - previousTime).total_seconds() / 3600)
        previousTime = reviewTime
        
    return model
    
def ebisuModelToMemorizeInterval(model, q=10.0, T=inf):
    """Use an Ebisu model to draw a MEMORIZE interval"""
    return schedule(lambda t: ebisu.predictRecall(initialModel, t, exact=True), q, T)
    
    
def ivlAdjustFunc():
    #cardObj = mw.reviewer.card
    #showInfo("%s" % cardObj)
    queue = mw.reviewer.card.queue
    if queue == 2:
        curFactor = mw.reviewer.card.factor
        cardID = mw.reviewer.card.id
        rev, cor, fac, srate = findSuccessRate(cardID)
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

addHook('showQuestion', ivlAdjustFunc)