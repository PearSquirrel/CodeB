import socket
import sys
import time
import operator

class Bot:

    def __init__(self):
        self.user = 'dabes'
        self.password = 'scoober'
        self.HOST, self.PORT = "codebb.cloudapp.net", 17429
        self.run('MY_CASH')
        self.database = {}
        self.numSeconds = 1
        self.sorted_earnings_factors = {}
        while True:
##            if numSeconds > 5:
##                self.updateMovingAverage()
##                print self.database['AAPL']['moving_average']
            if self.numSeconds > 2:
                print "The best stocks are"
                print self.getBestStocks()
            self.updateSecurities()
            time.sleep(1)
            self.numSeconds += 1

    def updateMovingAverage(self):
        for ticker in self.database:
            if 'moving_average' not in self.database[ticker]:
                self.database[ticker]['moving_average'] = []
            lastFive = self.database[ticker]['net_worth'][-2:]
            moving_average = sum(lastFive)/float(len(lastFive))
            self.database[ticker]['moving_average'].append(moving_average)

    def updateMySecurities(self):
        securities = self.ask('MY_SECURITIES').split(' ')[1:]
        tickers = securities[0::3]
        shares = securities[1::3]
        dividend_ratio = securities[2::3]

        for index, ticker in enumerate(tickers):
            if ticker not in self.database:
                self.database[ticker] = {}
            if 'shares' not in self.database[ticker]:
                self.database[ticker]['shares'] = []
            if 'dividend_ratio' not in self.database[ticker]:
                self.database[ticker]['dividend_ratio'] = []
            self.database[ticker]['shares'].append(shares[index])
            self.database[ticker]['dividend_ratio'].append(dividend_ratio[index])

        print self.database

    def getBestStocks(self):
        bestStocks = []
        for i in range(0, len(self.sorted_earnings_factors)):
            if self.sorted_earnings_factors[i][1] > 1:
##                print self.sorted_earnings_factors[i]
                bestStocks.append(self.sorted_earnings_factors[i][0])
        return bestStocks
                

    def getVolatility(self):
        if self.numSeconds == 1:
            for ticker in self.database:
                self.database[ticker]['earnings_factor_average'] = 1
        else:
            for ticker in self.database:
                earningsFactor = float(self.database[ticker]['net_worth'][-1]) / float(self.database[ticker]['net_worth'][-2])
##                v = (float(self.database[ticker]['net_worth'][-2]) / float(self.database[ticker]['net_worth'][-1])) - 1
##                self.database[ticker]['volatility_score'] += v
                self.database[ticker]['earnings_factor_average'] = (self.database[ticker]['earnings_factor_average'] * (self.numSeconds - 1)  + earningsFactor) / self.numSeconds
                
##                print ticker + '  ' + str(self.database[ticker]['earnings_factor_average'])
            sorted_earnings_factors = {}
            for ticker in self.database:
                sorted_earnings_factors[ticker] = self.database[ticker]['earnings_factor_average']
            self.sorted_earnings_factors = sorted(sorted_earnings_factors.items(), key=operator.itemgetter(1), reverse=True)
            for i in range(0, len(self.sorted_earnings_factors)):
                print self.sorted_earnings_factors[i]

    def updateSecurities(self):
        securities = self.ask('SECURITIES').split(' ')[1:]
        tickers = securities[0::4]
        net_worth = securities[1::4]
        dividend_ratio = securities[2::4]
        volatility = securities[3::4]

        for index, ticker in enumerate(tickers):
            if ticker not in self.database:
                self.database[ticker] = {}
            if 'tickers' not in self.database[ticker]:
                self.database[ticker]['shares'] = []
            if 'net_worth' not in self.database[ticker]:
                self.database[ticker]['net_worth'] = []
            if 'dividend_ratio' not in self.database[ticker]:
                self.database[ticker]['dividend_ratio'] = []
            if 'volatility' not in self.database[ticker]:
                self.database[ticker]['volatility'] = []
            self.database[ticker]['net_worth'].append(net_worth[index])
            self.database[ticker]['dividend_ratio'].append(dividend_ratio[index])
            self.database[ticker]['volatility'].append(volatility[index])

        self.getVolatility()
        print net_worth

    
    def ask(self, *commands):
        to_return = ""

        data=self.user + " " + self.password + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"

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

    def run(self, *commands):

        data=self.user + " " + self.password + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"

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

        data=self.user + " " + self.password + "\nSUBSCRIBE\n"

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

bot = Bot()
