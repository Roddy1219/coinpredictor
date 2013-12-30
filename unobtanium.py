from httplib2 import Http
import json, time, base64
from datetime import datetime
from basecoin import BaseCoin
import redis
h = Http()

class UnobtaniumPredictor(BaseCoin):
    def __init__(self):
        ### Chain specific ###
        self.nInterval = 3
        self.nAveragingInterval = 60
        self.nTargetSpacing = 60
        self.nAveragingTargetTimespan = self.nAveragingInterval * self.nTargetSpacing #40 minutes
        #self.retargetVsInspectRatio = 12.0
        #nMaxAdjustDown = 20 # 20% adjustment down
        #nMaxAdjustUp = 1 # 1% adjustment up
        self.nMinActualTimespan = self.nAveragingTargetTimespan * 0.9
        self.nMaxActualTimespan = self.nAveragingTargetTimespan * 1.2
        self.estimateLookback  = 10 #Lookback 10 blocks to estimate network hashrate
        ### Chain specific ###
        self.coinname = "Unobtanium (experimental)"
        self.chaintype = "sha-256"
        self.symbol = "UNO"
        self.subsidyfn = lambda height: 0.001*100000000 if height<2000  else 1*100000000 >> (height * 1)//120000
        self.subsidyint = 120000
        BaseCoin.__init__(self)

if __name__ == "__main__":
    u = UnobtaniumPredictor()
    print u.get_predictions()
