from datetime import datetime
import json, base64, settings, redis, time
from httplib2 import Http

h = Http()

class BaseCoin():

    def __init__(self):
        self.cache = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.auth_header = "Basic %s" % base64.b64encode(settings.CHAINS[self.symbol]["auth"])
        self.rpcurl = settings.CHAINS[self.symbol]["url"]
        self.marketid = settings.CHAINS[self.symbol].get("marketid")

    def get_rate_from_hashrate(self, previous, lookback):
        """
        Gets time for a new block based on hashrate
        """
        hashrate = self.estimate_hashrate(previous, lookback)
        diff = float(self.getblock(previous)["difficulty"])
        hashesperblk = diff * 2**48 / 0xffff
        timeperblk = hashesperblk/hashrate
        return timeperblk

    def update_btc_price(self):
        """
        How much btc for 1 coin
        """
        print self.marketid
        try:
            if self.marketid is not None:
                url = "http://pubapi.cryptsy.com/api.php?method=singlemarketdata&marketid=%s" %(self.marketid)
                print url
                r,c = h.request(url)
                data = json.loads(c)['return']['markets'][self.symbol]
                last = data['lasttradeprice']
                bestbid = max([i['price'] for i in data['buyorders']])
                rate = min(last, bestbid) #use lower of last trade and best bid to avoid ghost bids to jack up everything
                print rate
                key = "%sprice" %(self.symbol)
                self.cache.set(key, rate)
        except:
            print "%s pricecheck error" %(self.symbol)

    def fetch_btc_price(self):
        """
        How much btc for 1 coin
        """
        key = "%sprice" %(self.symbol)
        rate = self.cache.get(key)
        return rate

    def getlastblock(self):
        """
        Return number of last block
        """
        return int(self.rpc("getblockcount"))

    def rpc(self, method, paramaters=[]):
        """
        rpc call to wallet without needing any shitty deps
        """
        req = {"jsonrpc": "1.0", "id":"fortuneteller", "method": method , "params": paramaters}
        r,c = h.request(self.rpcurl , headers = { 'Authorization' : self.auth_header} , method="POST", body=json.dumps(req))
        #print c
        return json.loads(c)["result"]

    def get_current_difficulty(self):
        try:
            target = self.rpc("getblocktemplate")["target"]
            return 0x00000000FFFF0000000000000000000000000000000000000000000000000000 / float(eval("0x" + target))
        except:
            return None

    def getblock(self, number, cached=True):
        """
        Given block number return the getblock eqiv
        """
        key = "%s%s" %(self.symbol, number)
        res = None
        if cached:
            res = self.cache.get(key)
        if res is None:
            blkhash = self.rpc("getblockhash", paramaters=[number])
            res = self.rpc("getblock", paramaters=[blkhash])
            self.cache.set(key, json.dumps(res))
            self.cache.expire(key, self.nTargetSpacing * 3)
        else:
            res = json.loads(res)
        return res


    def bitstodiff(self, bits):
        unpacked = (bits % 16777216) * 2**(8*((bits / 16777216) - 3))
        diff = float(0x00000000FFFF0000000000000000000000000000000000000000000000000000) / unpacked
        return diff


    def estimate_hashrate(self, lastblock, lookback):
        oldest = self.getblock(lastblock - lookback)["time"]
        newest = self.getblock(lastblock)["time"]
        avgtime = (newest - oldest) / float(lookback)
        #make weighted average difficulty
        avdiff = 0.0
        for blk in range(lastblock - lookback + 1, lastblock + 1):
            avdiff += float(self.getblock(blk)["difficulty"]) / lookback
        hashesperblk = avdiff * 2**48 / 0xffff
        hashrate = hashesperblk / avgtime
        return hashrate

    def humanize_hashrate(self, hashrate):
        """
        Given hashrate in float (or int) return humanized form
        """
        hashrate = hashrate * 1.0 #make float
        if int(hashrate) / 1000000000000000 > 1:
            return "%.2f PH/s" %(hashrate / 1000000000000000)
        if int(hashrate) / 1000000000000 > 1:
            return "%.2f TH/s" %(hashrate / 1000000000000)
        if int(hashrate) / 1000000000 > 1:
            return "%.2f GH/s" %(hashrate / 1000000000)
        if int(hashrate) / 1000000 > 1:
            return "%.2f MH/s" %(hashrate / 1000000)
        if int(hashrate) / 1000 > 1:
            return "%.2f KH/s" %(hashrate / 1000)
        return "%.2f H/s" %(hashrate )

    def predict_multiplyer(self, lastblk):
        """
        DRY for other coins because FRC is different
        """
        self.getblock(lastblk)
        #currentblock = lastblk + 1
        nextintblk = ((lastblk / self.nInterval) + 1) * self.nInterval #Next change block
        rate = self.get_rate_from_hashrate(lastblk, self.estimateLookback) #Current network hashrate
        firstreal = nextintblk - self.nAveragingInterval #Real start block of current round
        firstblocktime = self.getblock(firstreal)["time"]
        lastblocktime = self.getblock(lastblk)["time"]
        blocksremain = nextintblk - lastblk
        timeremain = blocksremain * rate
        nActualTimespanUnbounded = lastblocktime + timeremain  - firstblocktime
        nActualTimespan = self.bound_timespan(nActualTimespanUnbounded)
        return rate, lastblocktime, timeremain, self.nAveragingTargetTimespan / nActualTimespan, self.nAveragingTargetTimespan / nActualTimespanUnbounded

    def bound_timespan(self, nActualTimespan):
        """
        This varies per chan, but we define min/max per chain
        """
        nActualTimespan = float(nActualTimespan) #/ self.retargetVsInspectRatio;
        if nActualTimespan < self.nMinActualTimespan:
            nActualTimespan = self.nMinActualTimespan
        if nActualTimespan > self.nMaxActualTimespan:
            nActualTimespan = self.nMaxActualTimespan
        return nActualTimespan


    def get_predictions(self, lastblk=None):
        if lastblk is None:
            lastblk = self.getlastblock()
        #print lastblk
        currentblock = lastblk + 1
        nextintblk = ((lastblk / self.nInterval) + 1) * self.nInterval #Next change block
        
        rate, lastblocktime, timeremain, multiplier, multiplierunbounded = self.predict_multiplyer(lastblk) #Override hook here for FRC things

        nextdiff = self.getblock(lastblk)["difficulty"] * multiplier
        output = {
            "asof": time.time(),
            "coinname": self.coinname,
            "symbol": self.symbol,
            "last_block" : lastblk,
            "chaintype": self.chaintype,
            "time_per_block": rate,
            "last_block_time": lastblocktime * 1000,
            "last_block_difficulty": self.getblock(lastblk)["difficulty"],
            "next_change_block": nextintblk,
            "next_change_block_difficulty": nextdiff,
            "next_change_block_difficulty_unbounded": self.getblock(lastblk)["difficulty"] * multiplierunbounded,
            "next_change": (multiplier - 1) * 100,
            "next_change_unbounded": (multiplierunbounded - 1) * 100,
            "lookback": self.estimateLookback,
            "next_change_block_time": (lastblocktime + timeremain) * 1000,
            "market_price": self.fetch_btc_price()
        }
        output["current_subsidy"] = self.subsidyfn(currentblock) * 1.0 / 100000000
        output["next_subsidy_int"] = ((int(lastblk) / self.subsidyint) + 1) * self.subsidyint
        output["next_subsidy"] = self.subsidyfn(output["next_subsidy_int"]) * 1.0 / 100000000
        output["next_subsidy_time"] = output["last_block_time"] + ((output["next_subsidy_int"] - lastblk )* self.nTargetSpacing * 1000)
        output["current_block"] = currentblock
        output["current_block_difficulty"] = self.get_current_difficulty()
        output["network_hashrate"] = self.estimate_hashrate(lastblk, self.estimateLookback)
        output["network_hashrate_humanized"] = self.humanize_hashrate(output["network_hashrate"])
        output["network_hashrate"] = output["network_hashrate"]
        key = "%spredictions" %(self.symbol)
        self.cache.set(key, json.dumps(output))
        return output

    def get_cached_predictions(self):
        """
        Try to generate, if fails return from cache
        """
        key = "%spredictions" %(self.symbol)
        keydirty = "%sdirty" %(self.symbol)
        predictions = None
        cached = self.cache.get(key)
        if cached is not None:
            predictions = json.loads(cached)
        is_dirty = self.cache.get(keydirty) is None
        if is_dirty:
            self.cache.set("%sdirty" %(self.symbol), "1")
            self.cache.expire("%sdirty" %(self.symbol), self.nTargetSpacing)
            #Staler than 2 minutes
            try:
                predictions = self.get_predictions()
            except:
                print "%s prediction made err" %(self.symbol)
                pass
        predictions["market_price"] = self.fetch_btc_price()
        return predictions


    """
    def generate_chaindump(self):
        chaindump = {}
        chaindump["current_difficulty"] = self.get_current_difficulty()
        chaindump["height"] = self.getlastblock()
        chaindump["blocks"] = {}
        for i in range(chaindump["height"] - self.nAveragingInterval - 10, chaindump["height"] + 1):
            blk = self.getblock(i)
            chaindump["blocks"][i] = {
                "time": blk["time"],
                "difficulty": blk["difficulty"]
            }
        return chaindump
    """
