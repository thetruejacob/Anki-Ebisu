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
    card.due = nextReviewSecond
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

def ResultsandTimes(cardID, initialModel=ebisuAllInOne.defaultModel(0.25, 3)):
    ''' Takes as input the cardID and initial guess of the model, and returns the next interval in hours from the last interval'''

    reviewResults = mw.col.db.list("SELECT ease FROM revlog WHERE cid = ?", cardID)
    reviewResults = [ease != 1 for ease in reviewResults]

    reviewTimes = mw.col.db.list("SELECT id FROM revlog WHERE cid = ?", cardID)
    reviewTimes = [datetime.fromtimestamp(time / 1000.00) for time in reviewTimes]

    previousTime, model = datetime.fromtimestamp(cardID / 1000.00), initialModel

    for (reviewTime, result) in zip(reviewTimes, reviewResults):
        model = ebisuAllInOne.updateRecall(model, result, (reviewTime - previousTime).total_seconds() / 3600)
        previousTime = reviewTime

    return ebisuAllInOne.modelToPercentileDecay(model)

def ebisuAll():
    for cid in mw.col.db.list(f"SELECT id FROM cards where queue in ({QUEUE_LRN}, {QUEUE_DAY_LRN}, {QUEUE_REV})"):
        card = mw.col.getCard(cid)
        card.flush()

action = QAction(mw)
action.setText("Ebisu")
mw.form.menuTools.addAction(action)
action.triggered.connect(ebisuAll)

