from anki.collection import _Collection
from anki.sched import Scheduler
from anki.schedv2 import Scheduler as SchedulerV2
from anki.cards import Card
from anki.utils import fmtTimeSpan
from aqt.qt import *
from aqt import mw

from .consts import *
from .memorizesrs import schedule
from .ebisuAllInOne import *
from datetime import datetime
import time
# import the "show info" tool from utils.py
from aqt.utils import showInfo

def answerButtons(self, card):
    return 2


Scheduler.answerButtons = answerButtons
SchedulerV2.answerButtons = answerButtons

oldFlush = Card.flush
oldFlushSched = Card.flushSched

def reprocess(card):
    currentSecond = time.time()
    lastReviewSecond = card.col.db.scalar("SELECT id FROM revlog WHERE cid = ? ORDER BY id DESC", card.id) // 1000
    ivlInHour = ResultsandTimes(card.id)
    ivlInDay = round(ivlInHour/24)
    ivlInSecond = ivlInHour * 3600
    nextReviewSecond = lastReviewSecond + ivlInSecond

    print(f"ivlInHour is {ivlInHour}, ivlInDay is {ivlInDay}, ivlInSecond is {ivlInSecond}")
    card.reps = 0
    remainingIntervalInSecond = nextReviewSecond - currentSecond
    remainingIntervalInDay = round(remainingIntervalInSecond / (24 * 60 * 60))

    remainingSecondsBeforeCutoff = card.col.sched.dayCutoff - currentSecond
    secondsSinceLastReview = currentSecond - lastReviewSecond
    print(f"--------------\nCard {card.id} was last reviewed {fmtTimeSpan(secondsSinceLastReview)} ago. Its interval was {card.ivl}. Interval should be {fmtTimeSpan(ivlInSecond)}. I.e. in {fmtTimeSpan(remainingIntervalInSecond)}. ")

    if nextReviewSecond <= currentSecond:
        # card is already due
        card.queue = QUEUE_REV
        card.type = CARD_REV
        card.ivl = ivlInHour
        card.due = self.today # TODO: find real day
        print(f"Setting its due date to today since already due.")
        return

    if ivlInHour >= 48:
        # more than 2 day. We can average and set to review
        card.queue = QUEUE_REV
        card.type = CARD_DUE
        card.due = card.col.sched.today + remainingIntervalInDay
        card.ivl = ivlInDay
        print(f"Setting its due date to the day {card.due}, in {remainingIntervalInDay} days.")
        return

    # at most 2 day. Stay in learning mode.
    card.queue = QUEUE_LRN
    card.type = CARD_LRN
    card.due = round(nextReviewSecond)
    t = time.localtime(nextReviewSecond)
    print(f"Setting its due date to {card.due}, i.e. {time.strftime('%y.%m.%d %H:%M:%S', t)}.")


def flush(self):
    print("our flush")
    if self.queue in {QUEUE_LRN, QUEUE_DAY_LRN, QUEUE_REV}:
        # Only consider review and learning
        reprocess(self)
    oldFlush(self)
Card.flush = flush
def flushSched(self):
    print("our flush")
    if self.queue in {QUEUE_LRN, QUEUE_DAY_LRN, QUEUE_REV}:
        # Only consider review and learning
        reprocess(self)
    oldFlushSched(self)
Card.flushSched = flushSched

def ResultsandTimes(cardID, initialModel=ebisuAllInOne.defaultModel(24, 3)):
    ''' 
    Takes as input the cardID and initial guess of the model, and returns the next interval in hours from the last interval
    The default model assumes a beta distribution with alpha = beta = 3, half life = 24 hours.
    '''

    # pull reviewresults from database
    reviewResults = mw.col.db.list("SELECT ease FROM revlog WHERE cid = ?", cardID) 

    # format properly: ease is encoded as 1(wrong), 2(hard), 3(ok), 4(easy) for review, and  1(wrong), 2(ok), 3(easy) for learn/relearn
    # just convert it to a list of True/False corresponding to review result
    reviewResults = [ease != 1 for ease in reviewResults]

    # pull review times from database
    reviewTimes = mw.col.db.list("SELECT id FROM revlog WHERE cid = ?", cardID)

    # format properly: id is actually the epoch-millisecond timestamp when the review was performed
    reviewTimes = [datetime.fromtimestamp(time / 1000.00) for time in reviewTimes]

    previousTime, model = reviewTimes[0], initialModel

    print(f"Review Results are {reviewResults},\n Review Times are {reviewTimes},\n previousTime is {previousTime},\n model is {model}")

    # Here, we start updating the recall successively based on the entire review history of the card. 

    for (reviewTime, result) in zip(reviewTimes[1:], reviewResults[1:]):

        # recursively update the model with the review result, and elapsed time (reviewTime - previousTime is a timeDelta object) in days
        model = ebisuAllInOne.updateRecall(model, result, (reviewTime - previousTime).total_seconds() / 86400)
        previousTime = reviewTime



    # modelToPercentileDecay estimates how long (in seconds) it will take for a model to decay to a given percentile 
    # Here, the percentile is 0.5, which is the half-life of the memory.
    print(f"model to percentile decay is {ebisuAllInOne.modelToPercentileDecay(model)}")
    return ebisuAllInOne.modelToPercentileDecay(model)

def ebisuAll():
    for cid in mw.col.db.list(f"SELECT id FROM cards where queue in ({QUEUE_LRN}, {QUEUE_DAY_LRN}, {QUEUE_REV})"):
        card = mw.col.getCard(cid)
        card.flush()

action = QAction(mw)
action.setText("Ebisu")
mw.form.menuTools.addAction(action)
action.triggered.connect(ebisuAll)

