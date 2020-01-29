from __future__ import division
from anki.hooks import addHook
from aqt import mw
from aqt.utils import tooltip

import sys
import os
import sqlite3
from .memorizesrs import schedule
from .ebisuAllInOne import *
from datetime import datetime, timedelta
from math import inf


def ResultsandTimes(cardID, initialModel = ebisu.defaultModel(0.25, 3)):
    ''' Takes as input the cardID and initial guess of the model, and returns the next interval in hours from the last interval'''
    
    reviewResults = mw.col.db.list("SELECT ease FROM revlog WHERE cid = ?", cardID) 
    reviewResults = [ease != 1 for ease in reviewResults]
    
    reviewTimes = mw.col.db.list("SELECT id FROM revlog WHERE cid = ?", cardID)
    reviewTimes = [datetime.fromtimestamp(time / 1000.00) for time in reviewTimes]
    
    previousTime, model = datetime.fromtimestamp(cardID / 1000.00), initialModel
    
    for (reviewTime, result) in zip(reviewTimes, reviewResults):
        model = ebisu.updateRecall(model, result, (reviewTime - previousTime).total_seconds() / 3600)
        previousTime = reviewTime
    
    return ebisu.modelToPercentileDecay(model)
    
    
def ivlAdjustFunc():
    '''Just a basic function: Arthur, please add code here to hook to showQuesiton or answerCard.'''



addHook('showQuestion', ivlAdjustFunc)