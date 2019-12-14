# -*- coding: utf-8 -*-
# Copyright: (C) 2018-2019 Lovac42
# Support: https://github.com/lovac42/AddonManager21
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.0.4


from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, runHook
from codecs import open
from anki.utils import json
import os, collections

from anki import version
ANKI21=version.startswith("2.1.")


class Config():
    config = {}

    def __init__(self, addonName):
        self.addonName=addonName
        addHook('profileLoaded', self._onProfileLoaded)

    def set(self, key, value):
        self.config[key]=value

    def get(self, key, default=None):
        return self.config.get(key, default)

    def has(self, key):
        return self.config.get(key)!=None


    def _onProfileLoaded(self):
        # wait for addonManager21 to load first.
        # Timer is no longer necessary for newer versions of AddonManager21
        mw.progress.timer(300,self._loadConfig,False)

    def _loadConfig(self):
        if getattr(mw.addonManager, "getConfig", None):
            self.config=mw.addonManager.getConfig(__name__)
            mw.addonManager.setConfigUpdatedAction(__name__, self._updateConfig)
        else:
            self.config=self._readConfig()
        runHook(self.addonName+'.configLoaded')

    def _updateConfig(self, config):
        self.config=nestedUpdate(self.config,config)
        runHook(self.addonName+'.configUpdated')

    def _readConfig(self):
        conf={}
        moduleDir, _ = os.path.split(__file__)
        # Read config.json
        path = os.path.join(moduleDir,'config.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data=f.read()
            conf=json.loads(data)
        # Read meta.json
        path = os.path.join(moduleDir,'meta.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data=f.read()
            meta=json.loads(data)
            conf=nestedUpdate(conf,meta.get('config',{}))
        return conf


#From: https://stackoverflow.com/questions/3232943/
def nestedUpdate(d, u):
    if ANKI21:
        itms=u.items()
    else:
        itms=u.iteritems()
    for k, v in itms:
        if isinstance(v, collections.Mapping):
            d[k] = nestedUpdate(d.get(k, {}), v)
        else:
            d[k] = v
    return d
