import math
import sys
import json

FUEL_DENSITY_LBS_PER_GAL = 6.7

"""FUEL_RESERVE = 2500
FUEL_START = 2500
FUEL_CAPACITY = 15020
PURCHASE_GRANULARITY_GAL = 10"""

MESSAGE = "What would you like to do: "
OPTIONS = {'h': 'help',
           'x': 'exit',
           'c': 'calculate',
           'n': 'new trip',
           'a': 'add leg',
           'e': 'edit',
           'r': 'remove leg',
           'v': 'view',
           'o': 'options'}


def fileOpen(file_name):
    with open(f"{file_name}", "r") as file:
        data = json.load(file)
    file.close()
    return data

def fileSave(file_name, data):
    with open(f"{file_name}", "w+") as file:
        json.dump(data, file, indent=4)
    file.close()

class FuelWizard:
    def __init__(self, leg_data: dict, options: dict):
        """
        :param leg_data: A dictionary of legs, keyed by leg name.
        """
        self.options = options
        self.fuel_start = self.options["FUEL_START"]
        self.fuel_reserve = self.options["FUEL_RESERVE"]
        self.fuel_capacity = self.options["FUEL_CAPACITY"]
        self.purchase_granularity_gal = self.options["PURCHASE_GRANULARITY_GAL"]

        self.leg_dict = leg_data
        self.leg_keys = list(leg_data.keys())
        self.total_legs = len(self.leg_keys)

        # keep track of the best plan and cost (cost initialized to a wild fucking value)
        self.min_trip_cost = sys.float_info.max
        self.best_purchase_plan = None

    def _get_max_fuel_start_lbs(self, leg_index: int) -> float:
        """
        Calculates the absolute maximum safe fuel (in lbs) the plane can have
        at takeoff for the specified leg.
        """
        leg_key = self.leg_keys[leg_index]
        current_leg_data = self.leg_dict[leg_key]

        # amount the plane weighs if it was empty
        min_fuel_weight = current_leg_data["zero_fuel_weight"] + self.fuel_reserve

        # max takeoff weight at current airport
        max_takeoff_fuel = current_leg_data["max_takeoff"] - min_fuel_weight
        max_takeoff_fuel = min(max_takeoff_fuel, self.fuel_capacity)

        # leg burn
        leg_burn = current_leg_data["leg_burn"]

        max_landing_fuel = current_leg_data["max_landing"] - min_fuel_weight
        # takeoff limit by landing weight limit
        max_by_landing_wt = max_landing_fuel + leg_burn

        # gives most restrictive of takeoff or landing weight limit
        return min(max_takeoff_fuel, max_by_landing_wt)

    def _find_min_cost(
            self,
            leg_index: int,
            current_fuel_remaining_lbs: float,
            current_cost: float,
            current_plan: list,
    ):
        """
        Recursive. Explores all valid purchase paths and find the minimum cost.

        :param leg_index: The index of the current leg (0 to total_legs - 1).
        :param current_fuel_remaining_lbs: Fuel remaining after landing at the current airport.
        :param current_cost: The total cost accumulated so far on the trip.
        :param current_plan: The list of purchase actions taken so far.
        """

        if current_cost >= self.min_trip_cost:
            # short-circuit this reality early if we're ever over the best min total cost
            return

        if leg_index == self.total_legs:
            # Final destination reached without short-circuiting means we found a cheaper solution.
            self.min_trip_cost = current_cost
            self.best_purchase_plan = current_plan
            #print(f"{round(self.min_trip_cost, 2)}")
            return

        # current leg data and constraints
        leg_key = self.leg_keys[leg_index]
        this_leg = self.leg_dict[leg_key]

        # 1. Minimum fuel (lbs) required at Takeoff
        min_fuel_start_lbs = this_leg["leg_burn"]

        # 2. max fuel (lbs) allowed at Takeoff
        max_fuel_start_lbs = self._get_max_fuel_start_lbs(leg_index)

        # 3. Required Purchase Bounds (GALLONS)
        # rounded to nearest ten (round -1 steps the decimal back one to the tens place)
        # Minimum purchase to reach min_fuel_start_lbs
        min_purchase_lbs = max(0, min_fuel_start_lbs - current_fuel_remaining_lbs)
        min_purchase_gal = round(
            math.ceil(min_purchase_lbs / FUEL_DENSITY_LBS_PER_GAL), -1
        )

        # Maximum purchase to stay within max_fuel_start_lbs
        max_purchase_lbs = max(0, max_fuel_start_lbs - current_fuel_remaining_lbs)
        max_purchase_gal = round(
            math.floor(max_purchase_lbs / FUEL_DENSITY_LBS_PER_GAL), -1
        )

        if leg_index == self.total_legs:
            lk = self.leg_keys[leg_index]
            l = self.leg_dict[lk]
            burn = l["leg_burn"]
            min_purchase_lbs = min(max_purchase_lbs, burn)
            min_purchase_gal = min(
                min_purchase_lbs / FUEL_DENSITY_LBS_PER_GAL, max_purchase_gal
            )

        # check for immediate infeasibility (if you get this error and I didn't fuck up, you can't do this flight I think)
        if min_purchase_gal > max_purchase_gal:
            # if the minimum required purchase exceeds the max allowed, this path is impossible.
            print(
                f"Minimum purchase gal is greater than max purchase gal for {leg_key}. Figure your shit out. Maybe data is bad."
            )
            return

        # iterate through all possible fuel purchases for this leg.
        # min/max gal inclusive. Step by granularity.
        for purchase_gal in range(
                min_purchase_gal, max_purchase_gal, self.purchase_granularity_gal
        ):
            # calculate possible fuel states
            purchase_lbs = purchase_gal * FUEL_DENSITY_LBS_PER_GAL
            fuel_start_lbs = current_fuel_remaining_lbs + purchase_lbs
            next_fuel_remaining_lbs = fuel_start_lbs - this_leg["leg_burn"]
            takeoff_weight = this_leg["zero_fuel_weight"] + self.fuel_reserve + fuel_start_lbs
            landing_weight = takeoff_weight - this_leg["leg_burn"]

            # 2. Calculate Cost
            purchase_cost = purchase_gal * this_leg["fuel_price"]

            fee_paid = this_leg["parking_fee"]
            if purchase_gal >= this_leg["fee_waive_amount"] and this_leg["fee_waive_amount"] > 0:
                fee_paid = 0

            new_total_cost = current_cost + purchase_cost + fee_paid

            # 3. Record the Purchase Action for this path
            action = {
                "leg": leg_key,
                "purchase_gallons": purchase_gal,
                "purchase_cost": round(purchase_cost, 2),
                "parking_fee_paid": fee_paid,
                "fuel_start": int(fuel_start_lbs) + self.fuel_reserve,
                "fuel_end": int(next_fuel_remaining_lbs) + self.fuel_reserve,
                "takeoff_weight": int(takeoff_weight),
                "max_takeoff": this_leg["max_takeoff"],
                "landing_weight": int(landing_weight),
                "max_landing": this_leg["max_landing"],
            }
            new_plan = current_plan + [action]

            # 4. Recursive Call to the next leg
            self._find_min_cost(
                leg_index + 1, next_fuel_remaining_lbs, new_total_cost, new_plan
            )

    def optimize_fuel_purchases(self, initial_fuel_lbs: float) -> (float, list):
        """
        The public method to start the optimization search.

        :param initial_fuel_lbs: The amount of fuel (in lbs) on board before the first leg.
        :return: A tuple of (minimum_cost, best_purchase_plan).
        """
        # Reset state for a new search
        self.min_trip_cost = sys.float_info.max
        self.best_purchase_plan = []

        # Start the recursive search from the first leg (index 0)
        # The 'fuel remaining' before leg 0 is the initial fuel carried.
        self._find_min_cost(
            leg_index=0,
            current_fuel_remaining_lbs=initial_fuel_lbs,
            current_cost=0.0,
            current_plan=[],
        )

        if self.min_trip_cost == sys.float_info.max:
            print("No feasible route found based on the provided constraints.")
            return (self.min_trip_cost, [])

        return (self.min_trip_cost, self.best_purchase_plan)

def takeData(should_i_ask_for_trip_id = True, trip_id = None):
    if should_i_ask_for_trip_id:
        trip_id = input("Please enter the Airport identifiers: ").upper()
    fuel_price = float(input("Fuel price at departure: ") or 0.00)
    parking_fee = float(input("Parking fee: ") or 0.00)
    fee_waive_amount = int(input("Amount to waive fee: ") or 0.00)
    leg_burn = int(input("Leg burn: ") or 0)
    max_takeoff = int(input("Max takeoff weight (default:35650): ") or 35650)
    max_landing = int(input("Max landing weight (default:30000): ") or 30000)
    zero_fuel_weight = int(input("Zero fuel weight: ") or 19000)

    leg_dict = {'fuel_price': fuel_price,
                'parking_fee': parking_fee,
                'fee_waive_amount': fee_waive_amount,
                'leg_burn': leg_burn,
                'max_takeoff': max_takeoff,
                'max_landing': max_landing,
                'zero_fuel_weight': zero_fuel_weight}

    leg_add = {trip_id: leg_dict}
    return leg_add

def asker():
    input_info = takeData()
    while input("Add another leg? (y/n): ") == "y":
        print()
        input_info.update(takeData())
    print()
    return input_info

def interface():
    inpt = str
    while inpt != "x":
        inpt = input(MESSAGE)
        if inpt not in OPTIONS.keys():
            print("Sorry command not recognized.")
        elif inpt == "h":
            helpMe()
        elif inpt == "x":
            exit()
        elif inpt == "c":
            calculate()
        elif inpt == "n":
            newTrip()
        elif inpt == "a":
            addLeg()
        elif inpt == "e":
            editLeg()
        elif inpt == "r":
            removeLeg()
        elif inpt == "v":
            viewLegs()
        elif inpt == "o":
            options()

def helpMe():
    for i in OPTIONS:
        print(f"{i} : {OPTIONS[i]}")

def calculate():
    data = fileOpen("tripData.json")
    opts = fileOpen("options.json")

    fw = FuelWizard(data, opts)
    best_cost, best_plan = fw.optimize_fuel_purchases(opts["FUEL_START"]-opts["FUEL_RESERVE"])
    print(f"\n{'Plan:'}"
          f"{'Fuel start: ':>56}{opts['FUEL_START']:>9}"
          f"{'Total Cost:':>55} {'$':>{9-len(str(f'{round(best_cost, 2):.2f}'))}}{round(best_cost, 2):.2f}{'':20}"
          )
    for e in best_plan:
        print(f"{e["leg"]} : "
              f"{e["purchase_gallons"]:4} gal @ "
              f"{'$':>{9-len(str(f'{e["purchase_cost"]:.2f}'))}}{e["purchase_cost"]:.2f} & "
              f"{'$':>{9-len(str(f'{e["parking_fee_paid"]:.2f}'))}}{e["parking_fee_paid"]:.2f} fee | "
              f"Fuel start/end: {e["fuel_start"]:5}/{e['fuel_end']:<4} | "
              f"Takeoff weight: {e["takeoff_weight"]:5}/{e["max_takeoff"]:5} | "
              f"Landing weight: {e["landing_weight"]:5}/{e['max_landing']:5}"
              )
    print()

def newTrip():
    opts = fileOpen("options.json")
    fuel_start = {"FUEL_START": int(input("Fuel start: "))}
    opts.update(fuel_start)
    fileSave("options.json", opts)

    data = asker()
    fileSave("tripData.json", data)
    return data

def addLeg():
    data = fileOpen("tripData.json")
    data.update(asker())
    fileSave("tripData.json", data)
    return data

def editLeg():
    data = viewLegs()
    key_list = data.keys()
    inpt = int(input("Which leg to edit: ")) - 1
    selected_leg = list(key_list)[inpt]

    print(f"\n---{selected_leg}---")
    selected_leg_dict = data.get(selected_leg)
    for i in selected_leg_dict:
        print(f"{i}: {selected_leg_dict[i]}")
    print()
    data.update(takeData(False, selected_leg))
    print()
    fileSave("tripData.json", data)
    return data

def removeLeg():
    data = viewLegs()
    key_list = data.keys()
    inpt = int(input("Which leg to remove: ")) - 1
    selected_leg = list(key_list)[inpt]

    print(f"{selected_leg} removed\n")
    data.pop(selected_leg)
    fileSave("tripData.json", data)
    return data

def viewLegs():
    data = fileOpen("tripData.json")
    for i, k in enumerate(data.keys()):
        print(str(i + 1) + " : " + str(k))
    print()
    return data

def options():
    opts = fileOpen("options.json")

    fuel_start = int(input(f"Fuel start: ({opts["FUEL_START"]}) ") or opts["FUEL_START"])
    fuel_reserve = int(input(f"Reserve: ({opts["FUEL_RESERVE"]}) ") or opts["FUEL_RESERVE"])
    fuel_capacity = int(input(f"Fuel tank maximum capacity: ({opts["FUEL_CAPACITY"]}) ") or opts["FUEL_CAPACITY"])
    calculation_granularity = int(input(f"Calculation granularity: ({opts["PURCHASE_GRANULARITY_GAL"]}) ") or opts["PURCHASE_GRANULARITY_GAL"])
    print()

    fw_options = {
        "FUEL_START": fuel_start,
        "FUEL_RESERVE": fuel_reserve,
        "FUEL_CAPACITY": fuel_capacity,
        "PURCHASE_GRANULARITY_GAL": calculation_granularity}

    opts.update(fw_options)
    fileSave("options.json", opts)

    return fw_options

if __name__ == "__main__":
    interface()
