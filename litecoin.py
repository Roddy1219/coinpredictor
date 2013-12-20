from httplib2 import Http
import json, time, base64
from datetime import datetime
from basecoin import BaseCoin
import redis
h = Http()

class LitecoinPredictor(BaseCoin):
    def __init__(self):
        ### Chain specific ###
        self.nInterval = 2016
        self.nAveragingInterval = self.nInterval #540 blocks
        self.nTargetSpacing = int(2.5 * 60) # Litecoin: 2.5 minutes
        self.nAveragingTargetTimespan = self.nAveragingInterval * self.nTargetSpacing #40 minutes
        #self.retargetVsInspectRatio = 12.0
        #nMaxAdjustDown = 20 # 20% adjustment down
        #nMaxAdjustUp = 1 # 1% adjustment up
        self.nMinActualTimespan = self.nAveragingTargetTimespan / 4.0
        self.nMaxActualTimespan = self.nAveragingTargetTimespan * 4
        self.estimateLookback  = 144 #6 hours worth of blocks
        ### Chain specific ###
        self.coinname = "Litecoin"
        self.symbol = "LTC"
        self.chaintype = "scrypt"
        self.subsidyfn = lambda height: 50*100000000 >> (height + 1)//840000
        self.subsidyint = 840000
        BaseCoin.__init__(self)

if __name__ == "__main__":
    l = LitecoinPredictor()
    print l.get_predictions()
