from httplib2 import Http
import json, time, base64
from datetime import datetime
from basecoin import BaseCoin
import redis
h = Http()

class BytecoinPredictor(BaseCoin):
    """
    Exact clone of bitcoin
    """
    def __init__(self):
        ### Chain specific ###
        self.nInterval = 2016
        self.nAveragingInterval = self.nInterval #540 blocks
        self.nTargetSpacing = 10 * 60 # 30 seconds
        self.nAveragingTargetTimespan = self.nAveragingInterval * self.nTargetSpacing #40 minutes
        #self.retargetVsInspectRatio = 12.0
        #nMaxAdjustDown = 20 # 20% adjustment down
        #nMaxAdjustUp = 1 # 1% adjustment up
        self.nMinActualTimespan = self.nAveragingTargetTimespan / 4.0
        self.nMaxActualTimespan = self.nAveragingTargetTimespan * 4
        self.estimateLookback  = 20 #Lookback 10 blocks to estimate network hashrate
        ### Chain specific ###
        self.coinname = "Bytecoin"
        self.chaintype = "sha-256"
        self.symbol = "BTE"
        self.subsidyfn = lambda height: 50*100000000 >> (height + 1)//210000
        self.subsidyint = 210000
        BaseCoin.__init__(self)


if __name__ == "__main__":
    b = BytecoinPredictor()
    print b.get_predictions()
