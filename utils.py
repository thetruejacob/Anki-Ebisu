# -*- coding: utf-8 -*-
# Copyright: (C) 2018-2019 Lovac42
# Support: https://github.com/lovac42/ReMemorize
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip, showInfo
from anki.utils import intTime, ids2str
import random, time, datetime
import aqt.utils
from anki.lang import _
from .const import *


#From: anki.sched.Scheduler
#Mods: removed resetting ease factor, added logs
# if lbal is true, only imin is used.
def customReschedCards(ids, imin, imax, logging=True, lbal=False):
    revCard=mw.reviewer.card
    markForUndo=True
    if mw.state!='review' or len(ids)>1 or not logging:
        markForUndo=False
        mw.checkpoint(_("ReM Rescheduled")) #undo state, inc siblings

    d = []
    t = mw.col.sched.today
    mod = intTime()
    for id in ids:
        card=mw.col.getCard(id)
        if markForUndo: #if size of array is one
            mw.col.markReview(card)
        else: #if not in reviewer
            mw.reviewer.card=card #swap for config checking (e.g. deFuzz/FreeWeekEnd deck options)

        if card.type in (0,1):
            initNewCard(card)
        r=adjInterval(card,imin,imax,lbal)
        ivl = max(1, r)
        d.append(dict(id=id, due=r+t, ivl=ivl, mod=mod, usn=mw.col.usn(), fact=card.factor))
        if logging: trylog(card,ivl)

    mw.col.sched.remFromDyn(ids)
    mw.col.db.executemany("""
update cards set type=2,queue=2,left=0,ivl=:ivl,due=:due,odue=0,
usn=:usn,mod=:mod,factor=:fact where id=:id""", d)
    mw.col.log(ids)
    mw.reviewer.card=revCard



#From: anki.sched.Scheduler
#Mods: added logging, changed sql
def customForgetCards(cids, logging=True):
    "Put cards at the end of the new queue."
    mw.checkpoint(_("ReM forget cards"))
    mw.col.sched.remFromDyn(cids)
    for id in cids:
        card=mw.col.getCard(id)
        if logging and card.type and card.queue:
            card.factor=0 #log as n/a
            trylog(card,0) #shows in log as "0d"

    mw.col.db.execute(
        "update cards set type=0,queue=0,left=0,ivl=0,due=0,odue=0,factor=0"
        " where id in "+ids2str(cids))
    pmax = mw.col.db.scalar(
        "select max(due) from cards where type=0") or 0
    # takes care of mod + usn
    mw.col.sched.sortCards(cids, start=pmax+1)
    mw.col.log(cids)



def trylog(card,ivl):
    try:
        log(card,ivl)
    except:
        time.sleep(0.01) # duplicate pk; retry in 10ms
        log(card,ivl)


#lastIvl = card.ivl
#ease=0, timeTaken=0
#custom log type: 4 = rescheduled
def log(card, ivl):
    lastIvl=getLastIvl(card)
    logId = intTime(1000)
    mw.col.db.execute(
        "insert into revlog values (?,?,?,0,?,?,?,0,4)",
        logId, card.id, mw.col.usn(),
        ivl, lastIvl, card.factor)



def getLastIvl(card):
    # records the from ivl from data recorded in the revlog.
    timeOrIvl=mw.col.db.scalar("""
Select ivl from revlog where cid = ? 
order by id desc limit 1""",card.id)
    if timeOrIvl:
        return timeOrIvl
    #no logged data, new cards
    conf=mw.col.sched._lrnConf(card)
    left=mw.col.sched._startingLeft(card)
    return - mw.col.sched._delayForGrade(conf,left) #negate



#triggers NC initialization, compatible w/ addon:noFuzzWhatsoever
def initNewCard(card):
    conf=mw.col.sched._lrnConf(card)
    mw.col.sched._rescheduleNew(card,conf,False)
    card.type=card.queue=1 #log delay as lrn



#Invoke Load Balancer or noFuzzWSE
def adjInterval(card,imin,imax,lbal=False):
    if not lbal:
        return random.randint(imin,imax) #likely the same num
    if mw.col.sched.name=="std2": #xquercus LBal, noFuzzWSE
        return mw.col.sched._fuzzedIvl(imin)
    else: #jake/xquercus LBal, noFuzzWSE
        return mw.col.sched._adjRevIvl(card,imin)




def parseDate(days):
    try:
        return getDays(days)
    except ValueError: #non date format
        return days
    except TypeError: #passed date
        showInfo("Already passed due date")
        return None


def getDays(date_str):
    d=datetime.datetime.today()
    today=datetime.datetime(d.year, d.month, d.day)
    try:
        due=datetime.datetime.strptime(date_str,'%m/%d/%Y')
    except ValueError:
        date_str=date_str+'/'+str(d.year)
        due=datetime.datetime.strptime(date_str,'%m/%d/%Y')
    diff=(due-today).days
    if diff<1: raise TypeError
    return diff



def tooltipHint(msg, period):
    tooltip(_(msg), period=period)
    aw=mw.app.activeWindow() or mw
    aqt.utils._tooltipLabel.move(
        aw.mapToGlobal(QPoint( aw.width()/2 -100, aw.height() -200)))

