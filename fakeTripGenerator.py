import random as rand
import string
import json


class tripMaker(object):
    def __init__(self):
        self.big_dict = {}

    def genName(self):
        return ''.join(rand.choices(string.ascii_uppercase, k=3))

    def genFuelPrice(self):
        return rand.randint(300, 800) / 100

    def genFee(self):
        return rand.randint(0, 200) * 10

    def genWaiveAmnt(self):
        return rand.randint(0, 60) * 10

    def genLegBurn(self):
        return rand.randint(0, 10000)

    def saveStuff(self):
        with open('fakeTrips.json', 'w+') as f:
            json.dump(self.big_dict, f, indent=4)

    def openStuff(self):
        with open('fakeTrips.json', 'r') as f:
            self.big_dict = json.load(f)


if __name__ == '__main__':
    tM = tripMaker()
    tM.big_dict

