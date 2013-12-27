from httplib2 import Http
import json, time, base64
from datetime import datetime
from basecoin import BaseCoin
import redis, dateutil.parser
h = Http()

class PPcoinPredictor(BaseCoin):
    def __init__(self):
        ### Chain specific ###
        self.nInterval = 1
        self.nAveragingInterval = self.nInterval #540 blocks
        self.nTargetSpacing = 10 * 60 # 30 seconds
        self.nAveragingTargetTimespan = self.nAveragingInterval * self.nTargetSpacing #40 minutes
        #self.retargetVsInspectRatio = 12.0
        #nMaxAdjustDown = 20 # 20% adjustment down
        #nMaxAdjustUp = 1 # 1% adjustment up
        self.nMinActualTimespan = self.nAveragingTargetTimespan / 4.0
        self.nMaxActualTimespan = self.nAveragingTargetTimespan * 4
        self.estimateLookback  = 10 #Lookback 10 blocks to estimate network hashrate
        ### Chain specific ###
        self.coinname = "PPcoin (broken)"
        self.chaintype = "sha-256"
        self.symbol = "PPC"
        self.subsidyfn = lambda height: 50*100000000 >> (height + 1)//1
        self.subsidyint = 1
        BaseCoin.__init__(self)


    def getblock(self, number, cached=True):
        """
        Given block number return the getblock eqiv
        overiding for ppcoin to convert time string to ts
        """
        key = "%s%s" %(self.symbol, number)
        res = None
        if cached:
            res = self.cache.get(key)
        if res is None:
            blkhash = self.rpc("getblockhash", paramaters=[number])
            res = self.rpc("getblock", paramaters=[blkhash])
            res["time"] = (dateutil.parser.parse(res["time"]) - dateutil.parser.parse("1970-1-1 00:00:00 UTC")).total_seconds()
            self.cache.set(key, json.dumps(res))
            self.cache.expire(key, self.nTargetSpacing * 3)
        else:
            res = json.loads(res)
        return res

    def get_current_difficulty(self):
        try:
            target = self.rpc("getwork")["target"]
            #Convert to big-endian
            target = target.decode('hex')[::-1].encode('hex_codec')
            return 0x00000000FFFF0000000000000000000000000000000000000000000000000000 / float(int(target, 16))
        except:
            return None

    def predict_multiplyer(self, lastblk):
        """
        Ugly hack for now. use real client values
        """
        last = self.getblock(lastblk)
        lastdiff = last["difficulty"]
        lasttime = last["time"]
        new = self.get_current_difficulty()
        rate = self.get_rate_from_hashrate(lastblk, self.estimateLookback)
        multiplier = new/lastdiff
        timeremain = lasttime + rate
        return rate, lasttime, timeremain, multiplier, multiplier



if __name__ == "__main__":
    p = PPcoinPredictor()
    print p.get_predictions()
