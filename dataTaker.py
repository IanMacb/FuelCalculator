import json


def asker():
    leg = input("Please enter the Airport identifiers: ")
    fuel_price = float(input("Fuel price at departure: "))
    parking_fee = float(input("Parking fee: "))
    fee_waive_amount = int(input("Amount to waive fee: "))
    leg_burn = int(input("Leg burn: "))
    max_takeoff = input("Max takeoff weight: ")
    if max_takeoff == 'd': max_takeoff = 35650
    else: max_takeoff = int(max_takeoff)
    max_landing = input("Max landing weight: ")
    if max_landing == 'd': max_landing = 30000
    else: max_landing = int(max_landing)
    zero_fuel_weight = int(input("Zero fuel weight: "))

    legDict = {'fuel_price': fuel_price, 'parking_fee': parking_fee, 'fee_waive_amount': fee_waive_amount,
                 'leg_burn': leg_burn, "max_takeoff": max_takeoff, 'max_landing': max_landing,
                 'zero_fuel_weight': zero_fuel_weight}

    legAdd = {leg: legDict}
    return legAdd

def politeAsker():
    inputInfo = {}
    inputInfo.update(asker())
    while input("Add another leg? (y/n): ") == "y":
        inputInfo.update(asker())
    return inputInfo


def main():
    data = politeAsker()
    with open("tripData.json", "w") as jsonFile:
        json.dump(data, jsonFile)
        jsonFile.close()

if __name__ == '__main__':
    main()