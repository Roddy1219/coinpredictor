from terracoin import TerraPredictor
from zetacoin import ZetaPredictor
from bitcoin import BitcoinPredictor
from freicoin import FreiPredictor
import json, time, redis, sys, settings

def get_chains(symbols):
    chains = {
        "ZET": ZetaPredictor,
        "BTC": BitcoinPredictor,
        "FRC": FreiPredictor,
        "TRC":TerraPredictor
    }
    return [chains[symbol]() for symbol in symbols]


if __name__ == "__main__":
    #z = ZetaPredictor()
    #t = TerraPredictor()
    #b = BitcoinPredictor()
    #f = FreiPredictor()
    if len(sys.argv) > 1:
        toreset = sys.argv[1]
        print "Resetting %s" %(toreset)
        cache = redis.StrictRedis(host='localhost', port=6379, db=0)
        cache.delete("%sdirty" %(toreset))

    chains = get_chains(settings.CHAINS.keys())
    #print [i.get_cached_predictions() for i in chains]
    result = {
        "generated": time.time() * 1000,
        "results": [i.get_cached_predictions() for i in chains]
    }
    open(settings.OUTPUT, "w").write(json.dumps(result, indent=4))
