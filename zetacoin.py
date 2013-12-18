import json, time, base64
from datetime import datetime
from basecoin import BaseCoin
import redis
import settings

class ZetaPredictor(BaseCoin):
    def __init__(self):
        ### Chain specific ###
        self.nInterval = 4
        self.nAveragingInterval = self.nInterval * 20 #80 blocks
        self.nTargetSpacing = 30 # 30 seconds
        self.nAveragingTargetTimespan = self.nAveragingInterval * self.nTargetSpacing #40 minutes
        nMaxAdjustDown = 20 # 20% adjustment down
        nMaxAdjustUp = 1 # 1% adjustment up
        self.nMinActualTimespan = self.nAveragingTargetTimespan * (100.0 - nMaxAdjustUp) / 100
        self.nMaxActualTimespan = self.nAveragingTargetTimespan * (100.0 + nMaxAdjustDown) / 100
        self.estimateLookback  = 10 #Lookback 10 blocks to estimate network hashrate
        ### Chain specific ###
        self.coinname = "Zetacoin"
        self.symbol = "ZET"
        self.subsidyfn=lambda height: 1000*100000000 >> (height + 1)//80640
        self.subsidyint = 80640
        BaseCoin.__init__(self)


if __name__ == "__main__":
    z = ZetaPredictor()
    print z.get_cached_predictions()


