import json, time, base64
from datetime import datetime
from basecoin import BaseCoin

class TerraPredictor(BaseCoin):
    def __init__(self):
        ### Chain specific ###
        self.nInterval = 540
        self.nAveragingInterval = self.nInterval #540 blocks
        self.nTargetSpacing = 120 # 30 seconds
        self.nAveragingTargetTimespan = self.nAveragingInterval * self.nTargetSpacing #40 minutes
        self.retargetVsInspectRatio = 12.0
        #nMaxAdjustDown = 20 # 20% adjustment down
        #nMaxAdjustUp = 1 # 1% adjustment up
        self.nMinActualTimespan = self.nAveragingTargetTimespan / 1.25
        self.nMaxActualTimespan = self.nAveragingTargetTimespan * 1.25
        self.estimateLookback  = 10 #Lookback 10 blocks to estimate network hashrate
        ### Chain specific ###
        self.coinname = "Terracoin"
        self.symbol = "TRC"
        self.subsidyfn = lambda height: 20*100000000 >> (height + 1)//1050000
        self.subsidyint = 1050000
        BaseCoin.__init__(self)

if __name__ == "__main__":
    t = TerraPredictor()
    previous = (275063/t.nInterval)*t.nInterval - 1
    print previous
    print json.dumps(t.get_predictions(lastblk=previous), indent=4)
