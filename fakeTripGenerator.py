import random as rand
import string
import json

RUN_TIMES = 4


def fileOpen(file_name):
    with open(f"{file_name}", "r") as file:
        data = json.load(file)
    file.close()
    return data


def fileSave(file_name, data):
    with open(f"{file_name}", "w+") as file:
        json.dump(data, file, indent=4)
    file.close()


class tripMaker():
    def __init__(self):
        self.data = {}

    def genName(self):
        trip_id = ''.join(rand.choices(string.ascii_uppercase, k=3)) + "-" + ''.join(rand.choices(string.ascii_uppercase, k=3))
        return trip_id

    def genFuelPrice(self):
        return rand.randint(300, 800) / 100

    def genFee(self):
        if rand.randint(0, 4) == 0:
            return 0
        else:
            return rand.randint(0, 200) * 10

    def genWaiveAmnt(self):
        if rand.randint(0, 1) == 0:
            return rand.randint(0, 60) * 10
        else:
            return 0

    def genLegBurn(self):
        return rand.randint(1000, 10000)

    def genMaxTakeoff(self):
        if rand.randint(0, 3) == 0:
            return rand.randint(32000, 35650)
        else:
            return 35650

    def genMaxLanding(self):
        if rand.randint(0, 5) == 0:
            return rand.randint(28000, 30000)
        else:
            return 30000

    def genZeroFuelWeight(self):
        return rand.randint(20000, 24000)

    def addLeg(self):
        add_leg = {
            self.genName(): {
                "fuel_price": self.genFuelPrice(),
                "parking_fee": self.genFee(),
                "fee_waive_amount": self.genWaiveAmnt(),
                "leg_burn": self.genLegBurn(),
                "max_takeoff": self.genMaxTakeoff(),
                "max_landing": self.genMaxLanding(),
                "zero_fuel_weight": self.genZeroFuelWeight()
            }
        }
        self.data.update(add_leg)


if __name__ == '__main__':
    tm = tripMaker()

    for i in range(RUN_TIMES):
        tm.addLeg()

    fileSave("tripData.json", tm.data)
