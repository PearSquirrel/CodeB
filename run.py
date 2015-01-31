import socket
import sys
import time
import operator

class Bot:
    def __init__(self):
        self.user = 'da_bes'
        self.password = 'scoober'
        self.HOST, self.PORT = "codebb.cloudapp.net", 17429
        self.database = {}
        self.numSeconds = 0
        self.sorted_earnings_factors = {}

        while True:
            self.updateModel()
            self.makeDecisions()
            time.sleep(1)
            self.numSeconds += 1
            for stock in self.getStocksToSell():
                self.sell(stock)
            for ticker in self.database:
                if self.numSeconds - self.database[ticker].get('bid_time', 0) > 10: # Sell a stock when we have held on to it for too long
                    print 'Held on to stock for too long'
                    self.sell(ticker)
                if self.database[ticker]['shares'] > 0:
                    print 'We own', self.database[ticker]['shares'], 'shares of', ticker

    def buy(self, ticker):
        bidPrice = self.getLowAsk(ticker) + 0.01
        shares = self.getNumSharesPurchasable(ticker, bidPrice)
        if shares != 0:
            print 'buying', str(shares), 'shares of', ticker, 'for $' + str(bidPrice)
            print self.placeBid(ticker, bidPrice, shares)
            self.database[ticker]['bid_time'] = self.numSeconds
##            self.database[ticker]['bid_price'] = bidPrice
        
        
    def sell(self, ticker):
        askPrice = self.getHighBid(ticker) - 0.01
        if self.numSeconds - self.database[ticker]['bid_time'] > 10:
            askPrice - (self.numSeconds - self.database[ticker]['bid_time'] - 10)
            print 'askPrice of', ticker, 'is', askPrice
        shares = self.database[ticker]['shares']
        if shares != 0:
            print 'selling', str(shares), 'shares of', ticker, 'for $' + str(askPrice)
            print self.placeAsk(ticker, askPrice, shares)


    def makeDecisions(self):
        if self.numSeconds >= 6:
            boughtTickers = [ticker for ticker in self.database.keys() if self.database[ticker]['shares'] != 0]
            for ticker in boughtTickers:
                if self.database[ticker]['trend'] <= 0:
                    self.sell(ticker)
            tickerToBuy = self.getHighestTrending()
            self.buy(tickerToBuy)

    def updateModel(self):
        if self.numSeconds < 2:
            for ticker in self.database:
                self.database[ticker]['bid_time'] = 0
        if self.numSeconds >= 5:
            self.updateMovingAverage()
        if self.numSeconds >= 6:
            self.updateTrend()
        self.updateSecurities()
        self.updateMySecurities()
        self.getVolatility()

    def updateTrend(self):
        for ticker in self.database:
            if 'trend' not in self.database[ticker]:
                self.database[ticker]['trend'] = []
            lastTwo = self.database[ticker]['moving_average'][-2:]
            trend = lastTwo[1] - lastTwo[0]
            self.database[ticker]['trend'].append(trend)
            self.database[ticker]['trend'] = self.database[ticker]['trend'][-5:]

    def updateMovingAverage(self):
        for ticker in self.database:
            if 'moving_average' not in self.database[ticker]:
                self.database[ticker]['moving_average'] = []
            lastFive = self.database[ticker]['net_worth'][-5:]
            moving_average = sum(lastFive) / float(len(lastFive))
            self.database[ticker]['moving_average'].append(moving_average)
            self.database[ticker]['moving_average'] = self.database[ticker]['moving_average'][-5:]

    def updateMySecurities(self):
        securities = self.ask('MY_SECURITIES').split(' ')[1:]
        tickers = securities[0::3]
        shares = securities[1::3]

        for index, ticker in enumerate(tickers):
            if ticker not in self.database:
                self.database[ticker] = {}
            self.database[ticker]['shares'] = int(shares[index])

    def updateSecurities(self):
        securities = self.ask('SECURITIES').split(' ')[1:]
        tickers = securities[0::4]
        net_worth = securities[1::4]
        dividend_ratio = securities[2::4]
        volatility = securities[3::4]

        for index, ticker in enumerate(tickers):
            if ticker not in self.database:
                self.database[ticker] = {}
                self.database[ticker]['shares'] = 0

            if 'net_worth' not in self.database[ticker]:
                self.database[ticker]['net_worth'] = []

            self.database[ticker]['net_worth'].append(float(net_worth[index]))
            self.database[ticker]['net_worth'] = self.database[ticker]['net_worth'][-5:]
            self.database[ticker]['dividend_ratio'] = float(dividend_ratio[index])
            self.database[ticker]['volatility'] = float(volatility[index])

    def getHighestTrending(self):
        tickers = self.database.keys()
        trends = [self.database[ticker]['trend'][-1] for ticker in self.database.keys()]
        sorteditems = sorted(zip(trends, tickers), reverse=True)
        sortedTickers = [ticker for trend, ticker in sorteditems]
        return sortedTickers[0]

    def ask(self, *commands):
        to_return = ""

        data = self.user + " " + self.password + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            sock.connect((self.HOST, self.PORT))
            sock.sendall(data)
            sfile = sock.makefile()
            rline = sfile.readline()
            while rline:
                to_return += rline.strip() + "\n"
                rline = sfile.readline()
        finally:
            sock.close()
            return to_return

    def subscribe(self):
        self.HOST, self.PORT = "codebb.cloudapp.net", 17429

        data = self.user + " " + self.password + "\nSUBSCRIBE\n"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            sock.connect((self.HOST, self.PORT))
            sock.sendall(data)
            sfile = sock.makefile()
            rline = sfile.readline()
            while rline:
                print(rline.strip())
                rline = sfile.readline()
        finally:
            sock.close()

    def getStocksToSell(self):
        stocksToSell = []
        for ticker in self.database:
            if self.database[ticker]['shares'] != 0:
                dividend_ratio = self.database[ticker]['dividend_ratio']
                gains = self.database[ticker]['net_worth'][-1] * dividend_ratio / float(self.getTotalShares(ticker))
                print "{} is making me {} per share...".format(ticker, gains)
                if gains < 0.03:
                    print "so I will sell it"
                    stocksToSell.append(ticker)
                else:
                    print "so I will keep it"
        return stocksToSell

    def getTotalShares(self, ticker):
        s = self.ask('ORDERS ' + ticker).replace("\n","")
        n = 0
        for shares in s.split(' ')[1:][3::4]:
            n += int(shares)
        return n
            

    def getBestStocks(self):
        bestStocks = []
        for i in range(0, len(self.sorted_earnings_factors)):
            if self.sorted_earnings_factors[i][1] > 1:
                bestStocks.append(self.sorted_earnings_factors[i][0])
        return bestStocks
                

    def getVolatility(self):
        numSeconds = self.numSeconds + 1
        if numSeconds == 1:
            for ticker in self.database:
                self.database[ticker]['earnings_factor_average'] = 1
        else:
            for ticker in self.database:
                earningsFactor = float(self.database[ticker]['net_worth'][-1]) / float(self.database[ticker]['net_worth'][-2])
                self.database[ticker]['earnings_factor_average'] = (self.database[ticker]['earnings_factor_average'] * (numSeconds - 1)  + earningsFactor) / numSeconds
                
            sorted_earnings_factors = {}
            for ticker in self.database:
                sorted_earnings_factors[ticker] = self.database[ticker]['earnings_factor_average']
            self.sorted_earnings_factors = sorted(sorted_earnings_factors.items(), key=operator.itemgetter(1), reverse=True)

    # ====================================
    # ====================================
    # Adopting Sam's Code
    # ====================================
    # ====================================
    def getTickers(self):
        return self.database.keys()

    def getBidAskSpread(self, ticker):
        highBid = 0
        lowAsk = sys.maxint
        for ticker in self.database:
            if bidAsks[i] == 'BID':
                bid = float(bidAsks[i+2])
                if bid > highBid:
                    highBid = bid
            if bidAsks[i] == 'ASK':
                ask = float(bidAsks[i+2])
                if ask < lowAsk:
                    lowAsk = ask
        return lowAsk - highBid

    def getHighBid(self, ticker):
        highBid = 0
        bidAsks = self.ask('ORDERS ' + ticker).split(' ')[1:]
        for i in range(0,len(bidAsks),4):
            if bidAsks[i] == 'BID':
                bid = float(bidAsks[i+2])
                if bid > highBid:
                    highBid = bid
        return highBid

    def getLowBid(self, ticker):
        lowBid = 0
        bidAsks = self.ask('ORDERS ' + ticker).split(' ')[1:]
        for i in range(0,len(bidAsks),4):
            if bidAsks[i] == 'BID':
                bid = float(bidAsks[i+2])
                if bid < lowBid:
                    lowBid = bid
        return lowBid

    def getLowAsk(self, ticker):
        lowAsk = sys.maxint
        bidAsks = self.ask('ORDERS ' + ticker).split(' ')[1:]
        for i in range(0,len(bidAsks),4):
            if bidAsks[i] == 'ASK':
                ask = float(bidAsks[i+2])
                if ask < lowAsk:
                    lowAsk = ask
        return lowAsk

    def getLeastSpreadTicker(self):
        leastSpread = sys.maxint
        leastSpreadTicker = ''
        for ticker in self.getTickers():
            spread = self.getBidAskSpread(ticker)
            if spread < leastSpread:
                leastSpread = spread
                leastSpreadTicker = ticker
        return leastSpreadTicker

    def getCash(self):
        return float(self.ask('MY_CASH').split(' ')[1:][0])

    def getNumSharesPurchasable(self, ticker, bidPrice):
        cash = self.getCash()
        return int(cash / bidPrice)

    def placeBid(self, ticker, price, shares):
        return self.ask("BID {} {} {}".format(ticker, price, shares))

    def placeAsk(self, ticker, price, shares):
        return self.ask("ASK {} {} {}".format(ticker, price, shares))

    def getSharesOwned(self, ticker):
        securities = self.ask('MY_SECURITIES').split(' ')[1:]
        for i in range(0,len(securities),3):
            if securities[i] == ticker:
                return int(securities[i + 1])
        return -1 # something went wrong

bot = Bot()
