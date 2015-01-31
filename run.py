import socket
import sys
import time
import operator

class Bot:
	def __init__(self):
		self.user = 'dabes'
		self.password = 'scoober'
		self.HOST, self.PORT = "codebb.cloudapp.net", 17429
		self.database = {}
		self.numSeconds = 0
		self.sorted_earnings_factors = {}

		while True:
			self.updateModel()
			#self.makeDecisions()
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
			self.database[ticker]['shares'] = float(shares[index])

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

#bot = Bot()
