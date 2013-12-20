import json, time, base64
from datetime import datetime
from basecoin import BaseCoin
import redis
from fractions import Fraction as mpq

class FreiPredictor(BaseCoin):
    def __init__(self):
        ### Chain specific ###
        self.nInterval = 9
        self.nAveragingInterval = self.nInterval * 20 #80 blocks
        self.nTargetSpacing = 10 * 60 # 10 minutes
        self.nAveragingTargetTimespan = self.nInterval * self.nTargetSpacing #40 minutes
        nMaxAdjustDown = 20 # 20% adjustment down
        nMaxAdjustUp = 1 # 1% adjustment up
        self.nMinActualTimespan = self.nAveragingTargetTimespan * (100.0 - nMaxAdjustUp) / 100
        self.nMaxActualTimespan = self.nAveragingTargetTimespan * (100.0 + nMaxAdjustDown) / 100
        self.estimateLookback  = 10 #Lookback 10 blocks to estimate network hashrate
        ### Chain specific ###
        self.coinname = "Friecoin"
        self.symbol = "FRC"
        self.chaintype = "sha-256"
        self.subsidyfn=lambda height: int(mpq((161280-height) * 15916928405, 161280) + mpq(9999999999999999, 1048576)) if height < 161280 else 9536743164
        self.subsidyint = 1
        BaseCoin.__init__(self)


    def predict_multiplyer(self, lastblk):
        """
        Overriding FRC
        """
        #currentblock = lastblk + 1
        nextintblk = ((lastblk / self.nInterval) + 1) * self.nInterval #Next change block
        rate = self.get_rate_from_hashrate(lastblk, self.estimateLookback)
        firstreal = nextintblk - self.nAveragingInterval
        #firstblocktime = self.getblock(firstreal)["time"]
        lastblocktime = self.getblock(lastblk)["time"]
        blocksremain = nextintblk - lastblk
        timeremain = blocksremain * rate
        kFilterCoeff = [-845859,  -459003,  -573589,  -703227,  -848199, -1008841,
        -1183669, -1372046, -1573247, -1787578, -2011503, -2243311,
        -2482346, -2723079, -2964681, -3202200, -3432186, -3650186,
        -3851924, -4032122, -4185340, -4306430, -4389146, -4427786,
        -4416716, -4349289, -4220031, -4022692, -3751740, -3401468,
        -2966915, -2443070, -1825548, -1110759,  -295281,   623307,
         1646668,  2775970,  4011152,  5351560,  6795424,  8340274,
         9982332, 11717130, 13539111, 15441640, 17417389, 19457954,
        21554056, 23695744, 25872220, 28072119, 30283431, 32493814,
        34690317, 36859911, 38989360, 41065293, 43074548, 45004087,
        46841170, 48573558, 50189545, 51678076, 53028839, 54232505,
        55280554, 56165609, 56881415, 57422788, 57785876, 57968085,
        57968084, 57785876, 57422788, 56881415, 56165609, 55280554,
        54232505, 53028839, 51678076, 50189545, 48573558, 46841170,
        45004087, 43074548, 41065293, 38989360, 36859911, 34690317,
        32493814, 30283431, 28072119, 25872220, 23695744, 21554057,
        19457953, 17417389, 15441640, 13539111, 11717130,  9982332,
         8340274,  6795424,  5351560,  4011152,  2775970,  1646668,
          623307,  -295281, -1110759, -1825548, -2443070, -2966915,
        -3401468, -3751740, -4022692, -4220031, -4349289, -4416715,
        -4427787, -4389146, -4306430, -4185340, -4032122, -3851924,
        -3650186, -3432186, -3202200, -2964681, -2723079, -2482346,
        -2243311, -2011503, -1787578, -1573247, -1372046, -1183669,
        -1008841,  -848199,  -703227,  -573589,  -459003,  -845858]
        WINDOW = 144
        kOne = mpq(1)
        kTwoToTheThirtyOne = mpq("2147483648")
        kGain = mpq(41, 400)
        kLimiterUp = mpq(211, 200)
        kLimiterDown = mpq(200, 211)
        kTargetInterval = mpq(self.nTargetSpacing)
        idx = 0
        pitr = lastblk
        vTimeDelta = []
        for idx in range(0,WINDOW):
            curblk = nextintblk - idx
            if curblk > lastblk:
                #Assuming each block from now will be found at assumed hashrate probility
                vTimeDelta += [int(rate)]
            else:
                vTimeDelta += [self.getblock(curblk)["time"] - self.getblock(curblk-1)["time"] ]
        #print vTimeDelta
        vFilteredTime = 0
        for idx in range(0,WINDOW):
            vFilteredTime += kFilterCoeff[idx] * vTimeDelta[idx]
        #print vFilteredTime
        dFilteredInterval = mpq(vFilteredTime) / kTwoToTheThirtyOne
        dFilteredIntervalUnbounded = sum(vTimeDelta) / WINDOW
        #print dFilteredInterval
        dAdjustmentFactor = kOne - (kGain * (dFilteredInterval - kTargetInterval) / kTargetInterval)
        dAdjustmentFactorUnbounded = kOne - (kGain * (dFilteredIntervalUnbounded - kTargetInterval) / kTargetInterval)
        #print dAdjustmentFactor
        if dAdjustmentFactor > kLimiterUp:
            dAdjustmentFactor = kLimiterUp
        elif dAdjustmentFactor < kLimiterDown:
            dAdjustmentFactor = kLimiterDown
        #print dAdjustmentFactor
        multiplier = float( dAdjustmentFactor)
        return rate, lastblocktime, timeremain, multiplier, float(dAdjustmentFactorUnbounded)



if __name__ == "__main__":
    f = FreiPredictor()
    print f.getlastblock()
    print f.humanize_hashrate(f.estimate_hashrate(f.getlastblock(), 10))
    print f.get_predictions()

