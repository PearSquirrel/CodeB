import socket
import sys
import time


class Bot:
    def __init__(self):
        self.user = 'dabes'
        self.password = 'scoober'
        self.HOST, self.PORT = "codebb.cloudapp.net", 17429
        self.run('MY_CASH')
        self.database = {}
        self.numSeconds = 0

        while True:
            self.updateModel()
            self.makeDecisions()
            time.sleep(1)
            self.numSeconds += 1

    def makeDecisions(self):
        if self.numSeconds >= 6:
            boughtTickers = [ticker for ticker in self.database.keys() if self.database[ticker]['shares'] != 0]
            for ticker in boughtTickers:
                if self.database[ticker]['trend'] <= 0:
                    self.placeAsk(ticker, self.getHighBid(ticker), self.database[ticker]['shares'])
            tickerToBuy = self.getHighestTrending()
            bidPrice = self.getLowAsk(tickerToBuy)
            numSharesToBuy = self.getNumSharesPurchasable(tickerToBuy)
            self.placeBid(tickerToBuy, bidPrice, numSharesToBuy)

    def updateModel(self):
        if self.numSeconds >= 5:
            self.updateMovingAverage()
        if self.numSeconds >= 6:
            self.updateTrend()
        self.updateSecurities()

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
            self.database[ticker]['shares'] = float(shares[index])

        print self.database

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

        print self.database

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

    def getHighestTrending(self):
        tickers = self.database.keys()
        trends = [self.database[ticker]['trend'][-1] for ticker in self.database.keys()]
        sorteditems = sorted(zip(trends, tickers), reverse=True)
        sortedTickers = [ticker for trend, ticker in sorteditems]
        return sortedTickers[0]

    def run(self, *commands):

        data = self.user + " " + self.password + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"

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
        bidAsks = self.ask('ORDERS ' + ticker).split(' ')[1:]
        for i in range(0,len(bidAsks),4):
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

    def getNumSharesPurchasable(self, ticker):
        cash = self.getCash()
        ask = self.getLowAsk(ticker)
        return int(cash / ask)

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

    def trade(self):
        ticker = self.getLeastSpreadTicker()

        for i in range(5):
            price = self.getLowAsk(ticker)
            price += .0001
            shares = self.getNumSharesPurchasable(ticker)

            print "Found least spread ticker {}".format(ticker)
            print "Buying {} of {} for {} each".format(shares, ticker, price)
            print self.placeBid(ticker, price, shares)

            time.sleep(5)
            self.ask('CLEAR_BID ' + ticker)

        predictedSellPrice = self.getHighBid(ticker) - .0002
        lossPerShare = price - predictedSellPrice
        shares = self.getSharesOwned(ticker)
        predictedLoss = lossPerShare * shares

        print "Need to make back ${} (predicted)".format(predictedLoss)
        print self.ask('MY_SECURITIES')

        print "sleeping..."
        time.sleep(120)
        print "waking up"
        print self.ask('MY_SECURITIES')

        for i in range(5):
            price = self.getHighBid(ticker)
            price -= .0002
            shares = self.getSharesOwned(ticker)
            print "Selling {} of {} for {} each".format(shares, ticker, price)
            print self.placeAsk(ticker, price, shares)
            time.sleep(5)
            self.ask('CLEAR_ASK ' + ticker)

        print self.ask('MY_SECURITIES')



bot = Bot()