import json
import matplotlib

class FuelWizard(object):
    def __init__(self):
        self.big_dict = {}

    def saveStuff(self):
        with open('testTrips.json', 'w+') as f:
            json.dump(self.big_dict, f, indent=4)

    def openStuff(self):
        with open('testTrips.json', 'r') as f:
            self.big_dict = json.load(f)

    def fillStuff(self):
        for airportID, leg in self.big_dict.items():
            leg['amountWaiveLB'] = leg['amountWaiveGal'] * 6.7
            leg['costToWaive'] = leg['fuelPrice'] * leg['amountWaiveGal']
            leg['maxBeforeWaive'] = round((leg['costToWaive'] - leg['fee']) / leg['fuelPrice'], 2)

    def bigDumbIdiot(self):
        currentIdiotTank = 0
        totalCost = 0
        for airportID, leg in self.big_dict.items():
            burn = leg['legBurn']
            fuelTake = max(burn - currentIdiotTank, 0)
            if fuelTake >= leg['maxBeforeWaive'] * 6.7:
                fuelTake = leg['amountWaiveLB']
            legCost = fuelTake / 6.7 * leg['fuelPrice']
            totalCost += legCost
            currentIdiotTank += fuelTake
            currentIdiotTank -= leg['legBurn']
            print(f'total cost so far: ${round(totalCost, 2)}\t - Fuel purchased here: {fuelTake}')


if __name__ == '__main__':
    fw = FuelWizard()
    '''fw.big_dict = {
        'MMU': {'fuelPrice': 5.44, 'fee': 625, 'amountWaiveGal': 520, 'legBurn': 781},
        'HPN': {'fuelPrice': 4.16, 'fee': 796, 'amountWaiveGal': 420, 'legBurn': 1860},
        'LEW': {'fuelPrice': 5.39, 'fee': 500, 'amountWaiveGal': 400, 'legBurn': 3583},
    }'''
    fw.openStuff()
    fw.fillStuff()
    '''
    for k, v in fw.big_dict.items():
        print(k, v)'''

    fw.bigDumbIdiot()



'''
bigList = []
legDict = {
    'airportID':None,
    'fuelPrice':None,
    'fee':None,
    'amountWaiveGal':None,
    'amountWaiveLb':None,
    'costToWaive':None,
    'maxBeforeWaive':None,
    'fuelTakingGal':None,
    'fuelTakingLb':None,
    'legCost':None,
    'fuelStart':None,
    'fuelEnd':None,
    'legBurn':None
}'''