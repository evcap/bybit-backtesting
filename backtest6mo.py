import pandas as pd

# variables

startingBalance = 1000
standardPositionSizeUSDT = 10
slippage = 0
takerFee = 0.0006
makerFee = 0.0001

netBalanceUSDT = startingBalance
currentExposureUSDT = 0
currentExposureBTC = 0 
currentEntry = 0
currentTarget = 0
currentStop = 0
tradeCount = 0
tpCount = 0
weekNum = 1
position = "none"
lastTradeTime = 0
openCost = standardPositionSizeUSDT * 1.0001

openPosition = False

# set up 

# weeks = [pd.read_csv("week1.csv"), pd.read_csv("week2.csv"), pd.read_csv("week3.csv"), pd.read_csv("week4.csv"), pd.read_csv("week5.csv"), pd.read_csv("week6.csv"), pd.read_csv("week7.csv")]
logs = pd.DataFrame(columns=["time", "type", "subtype", "position", "price", "entry", "target", "stop", "tradeSizeBTC", "balanceBefore", "balanceAfter", "weekNum", "target", "stop", "close", "SMA3D", "SMA2D", "SMA1D", "SMA240", "SMA60", "SMA20", "SMA5", "TEMA5"])
report = pd.DataFrame(columns=["weekNum", "target", "stop", "tradeCount", "winRate", "finalBalance", "delay"])


# functions

def sizeAfterFeesUSDT(price, typeParam):
    if typeParam == "market":
        pSizeUSDT = standardPositionSizeUSDT * (1-takerFee)
    elif typeParam == "limit":
        pSizeUSDT = standardPositionSizeUSDT * (1-makerFee)
    return pSizeUSDT

def sizeAfterFeesBTC(price, typeParam):
    if typeParam == "market":
        pSizeBTC = (standardPositionSizeUSDT/price) * (1-takerFee)
    elif typeParam == "limit":
        pSizeBTC = (standardPositionSizeUSDT/price) * (1-makerFee)
    return pSizeBTC

def setTarget(entry, targetParam):
    global position
    if position == "long":
        target = entry * (1 + targetParam)  
    elif position == "short":
        target = entry * (1 - targetParam)  
    return target

def setStop(entry, stopParam):
    global position
    if position == "long":
        stop = entry * (1 - stopParam)
    elif position == "short":
        stop = entry * (1 + stopParam)
    return stop

def calcReturns(exit, size, typeParam):
    if typeParam == "market":
        returns = (size * exit) * (1 - takerFee)
        return returns
    elif typeParam == "limit":
        returns = (size * exit) * (1 - makerFee)
        return returns

def open_pos(price, typeParam, targetParam, stopParam, time, close, SMA3D, SMA2D, SMA1D, SMA240, SMA60, SMA20, SMA5, TEMA5):
    global netBalanceUSDT
    global openPosition
    global currentExposureBTC
    global currentExposureUSDT
    global currentStop
    global currentTarget
    global currentEntry
    global logs
    global tradeCount
    global position
    global openCost
    tradeCount += 1
    openPosition = True
    currentEntry = price
    currentTarget = setTarget(price, targetParam)
    currentStop = setStop(price, stopParam)
    currentExposureUSDT = sizeAfterFeesUSDT(price, typeParam)
    currentExposureBTC = sizeAfterFeesBTC(price, typeParam)
    balanceBefore = netBalanceUSDT
    netBalanceUSDT -= openCost
    # newLog = pd.DataFrame([[time, "open", "open", position, price, currentEntry, currentTarget, currentStop, currentExposureBTC, balanceBefore, netBalanceUSDT, weekNum, targetParam, stopParam, close, SMA3D, SMA2D, SMA1D, SMA240, SMA60, SMA20, SMA5, TEMA5]], columns=["time", "type", "subtype", "position", "price", "entry", "target", "stop", "tradeSizeBTC", "balanceBefore", "balanceAfter", "weekNum", "target", "stop", "close", "SMA3D", "SMA2D", "SMA1D", "SMA240", "SMA60", "SMA20", "SMA5", "TEMA5"])
    # logs = pd.concat([logs, newLog])

def close_pos(exit, size, typeParam, time, subType, targetParam, stopParam, open):
    global logs 
    global netBalanceUSDT
    global currentExposureBTC
    global currentExposureUSDT
    global currentEntry
    global currentTarget
    global currentStop
    global openPosition
    global position
    global lastTradeTime
    returns = calcReturns(exit, size, typeParam)
    balanceBefore = netBalanceUSDT
    netBalanceUSDT += returns
    # newLog = pd.DataFrame([[time, "close", subType, position, open, currentEntry, currentTarget, currentStop, currentExposureBTC, balanceBefore, netBalanceUSDT, weekNum, targetParam, stopParam, 0, 0, 0, 0, 0, 0, 0, 0, 0]], columns=["time", "type", "subtype", "position", "price", "entry", "target", "stop", "tradeSizeBTC", "balanceBefore", "balanceAfter", "weekNum", "target", "stop", "close", "SMA3D", "SMA2D", "SMA1D", "SMA240", "SMA60", "SMA20", "SMA5", "TEMA5"])
    currentExposureUSDT = 0
    currentExposureBTC = 0
    currentEntry = 0
    currentTarget = 0
    currentStop = 0
    openPosition = False
    # logs = pd.concat([logs, newLog])
    position = "none"
    lastTradeTime = time

def open_trigger_check(close, SMA3D, SMA2D, SMA1D, SMA240, SMA60, SMA20, SMA5, TEMA5, currentTEMASMADiff, previousTEMASMADiff):
    global position
    if ( # check for shorts
        (currentTEMASMADiff < 0 and previousTEMASMADiff > 0) and
        (TEMA5 > SMA20) and
        ((SMA60*1.005) < TEMA5) and
        ((SMA240*1.01) < TEMA5) and
        (TEMA5 > SMA2D)
    ):
        openTrigger = True
        position = "short"
    elif ( # check for longs
        (currentTEMASMADiff > 0 and previousTEMASMADiff < 0) and
        (TEMA5 < SMA20) and
        ((SMA60*0.995) > TEMA5) and
        ((SMA240*0.99) > TEMA5) and
        (TEMA5 < SMA2D)
    ):
        openTrigger = True
        position = "long"
    else:
        openTrigger = False
    return openTrigger

def tp_trigger_check(price, target, position):
    global tpCount
    if position == "long":
        if price > target:
            tpTrigger = True
            tpCount += 1
        else:
            tpTrigger = False
    elif position == "short":
        if price < target:
            tpTrigger = True
            tpCount += 1
        else:
            tpTrigger = False
    return tpTrigger

def stop_trigger_check(price, stop, position):
    if position == "long":
        if price < stop:
            stopTrigger = True
        else:
            stopTrigger = False
    elif position == "short":
        if price > stop:
            stopTrigger = True
        else:
            stopTrigger = False
    return stopTrigger

def ready(close, SMA3D, SMA2D, SMA1D, SMA240, SMA60, SMA20, SMA5, TEMA5, currentTEMASMADiff, previousTEMASMADiff, openTypeParam, targetParam, stopParam, time):
    openTrigger = open_trigger_check(close, SMA3D, SMA2D, SMA1D, SMA240, SMA60, SMA20, SMA5, TEMA5, currentTEMASMADiff, previousTEMASMADiff)
    if openTrigger == True:
        open_pos(close, openTypeParam, targetParam, stopParam, time, close, SMA3D, SMA2D, SMA1D, SMA240, SMA60, SMA20, SMA5, TEMA5)

def busy(open, target, stop, size, closeTypeParam, time, targetParam, stopParam, position):
    tpTrigger = tp_trigger_check(open, target, position)
    if tpTrigger == True:
        close_pos(target, size, closeTypeParam, time, "tp", targetParam, stopParam, open)
    elif tpTrigger == False:
        stopTrigger = stop_trigger_check(open, stop, position)
        if stopTrigger == True:
            close_pos(stop, size, closeTypeParam, time, "stop", targetParam, stopParam, open)

def backtest(week, openTypeParam, closeTypeParam, targetParam, stopParam, delayParam):
    global openPosition
    global netBalanceUSDT
    global currentExposureUSDT
    global currentExposureBTC
    global currentEntry
    global currentTarget
    global currentStop
    global tradeCount
    global tpCount
    global weekNum
    global startingBalance
    global report
    global position
    global lastTradeTime
    global openCost
    for minute in week.itertuples():
        if openPosition == False:
            if (minute[6] > (lastTradeTime + delayParam)):
                ready(minute[11], minute[12], minute[13], minute[14], minute[15], minute[16], minute[17], minute[18], minute[19], minute[20], minute[21], openTypeParam, targetParam, stopParam, minute[6])
        elif openPosition == True:
            busy(minute[8], currentTarget, currentStop, currentExposureBTC, closeTypeParam, minute[6], targetParam, stopParam, position)
    if openPosition == True:
        tradeCount -= 1
        netBalanceUSDT += openCost
    if tradeCount != 0:
        newReport = pd.DataFrame([[weekNum, target, stop, tradeCount, tpCount/tradeCount, netBalanceUSDT, delayParam]], columns=["weekNum", "target", "stop", "tradeCount", "winRate", "finalBalance", "delay"])
        report = pd.concat([report, newReport])
        # print("Report for week " + str(weekNum) + " | Target: " + str(targetParam) + " | Stop: " + str(stopParam) + " | Total trades: " + str(tradeCount) + " | Winrate: " + str(tpCount/tradeCount) + " | Final balance: " + str(netBalanceUSDT))
        print("Report generated for week: " + str(weekNum) + " | Target: " + str(target) + " | Stop: " + str(stop) + " | Delay: " + str(delay) + " | Trade count: " + str(tradeCount) + " | Win rate: " + str(tpCount/tradeCount) + " | Final balance: " + str(netBalanceUSDT))
    tradeCount = 0
    tpCount = 0
    netBalanceUSDT = startingBalance
    openPosition = False
    lastTradeTime = 0

#  parameters

# targets = [0.002, 0.0025, 0.003, 0.0035, 0.004, 0.0045, 0.005, 0.0055, 0.006, 0.0065, 0.007, 0.0075] 
targets = [0.006, 0.0065, 0.007, 0.0075, 0.008, 0.0085, 0.009, 0.0095, 0.01, 0.0105, 0.011, 0.0115, 0.012, 0.0125, 0.013, 0.0135, 0.014, 0.0145, 0.015]
stops = [0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01, 0.011, 0.012, 0.013, 0.014, 0.015]
# delays = [3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800] #, 32400, 36000, 39600, 43200, 46800, 50400, 54000, 57600, 61200, 64800, 68400, 72000]
delays = [14400]

# execution

weeks = [pd.read_csv("sep6mo.csv")]

for target in targets:
    for stop in stops:
        for delay in delays:
            for week in weeks:  
                backtest(week, "limit", "limit", target, stop, delay)
                weekNum += 1
            weekNum = 1



# for target in targets:
#     for stop in stops:
#         for delay in delays:
#                 backtest(weeks, "limit", "limit", target, stop, delay)


logs.to_csv('logs6mo.csv')
report.to_csv('report6mo.csv')

