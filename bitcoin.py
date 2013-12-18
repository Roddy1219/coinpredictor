from httplib2 import Http
import json, time, base64
from datetime import datetime
from basecoin import BaseCoin
import redis
h = Http()

class BitcoinPredictor(BaseCoin):
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
        self.estimateLookback  = 144 #Lookback 10 blocks to estimate network hashrate
        ### Chain specific ###
        self.coinname = "Bitcoin"
        self.symbol = "BTC"
        self.subsidyfn = lambda height: 50*100000000 >> (height + 1)//210000
        self.subsidyint = 210000
        BaseCoin.__init__(self)

    def get_current_difficulty(self):
        return None

    def getlastblock(self):
        """
        Return number of last block
        """
        key = "%sgetlastblock" %(self.symbol)
        res = self.cache.get(key)
        if res is None:
            r,c = h.request("https://blockchain.info/q/getblockcount")
            res = c
            self.cache.set(key, res)
            self.cache.expire(key, 60)
        data = int(res)
        return data

    def getblock(self, number):
        """
        Given block number return the getblock eqiv
        """
        #print number
        key = "%s%s" %(self.symbol, number)
        res = self.cache.get(key)
        if res is None:
            r,c = h.request("http://blockexplorer.com/q/getblockhash/%s" %(number))
            blkhash = c.strip()
            url = "http://blockchain.info/rawblock/%s?format=json" %(blkhash)
            #print url
            r,c = h.request(url)
            blk = json.loads(c)
            del blk["tx"]
            res = blk
            blk["difficulty"] = self.bitstodiff(blk["bits"])
            self.cache.set(key, json.dumps(blk))
        else:
            res = json.loads(res)
        return res




if __name__ == "__main__":
    b = BitcoinPredictor()
    print b.get_predictions()
