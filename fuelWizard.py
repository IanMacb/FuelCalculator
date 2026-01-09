import math
import sys
import json

FULL_TANK_WEIGHT = 15020
FUEL_DENSITY_LBS_PER_GAL = 6.7
PURCHASE_GRANULARITY_GAL = 20
FUEL_RESERVE = 2500


#TODO:
# ask to add additional leg or overwrite
# GUI

class FuelWizard:
    def __init__(self, leg_data: dict):
        """
        :param leg_data: A dictionary of legs, keyed by leg name.
        """
        self.leg_dict = leg_data
        self.leg_keys = list(leg_data.keys())
        self.total_legs = len(self.leg_keys)

        # keep track of the best plan and cost (cost initialized to a wild fucking value)
        self.min_trip_cost = sys.float_info.max
        self.best_purchase_plan = None

    def asker(self):
        return

    def open_file(self):
        with open("tripData.json", "r") as fp:
            self.leg_dict = json.load(fp)

    def _get_max_fuel_start_lbs(self, leg_index: int) -> float:
        """
        Calculates the absolute maximum safe fuel (in lbs) the plane can have
        at takeoff for the specified leg.
        """
        leg_key = self.leg_keys[leg_index]
        current_leg_data = self.leg_dict[leg_key]

        # amount the plane weighs if it was empty
        zero_weight_here = current_leg_data["zero_fuel_weight"] + FUEL_RESERVE

        # max takeoff weight at current airport
        max_by_takeoff_wt = (
                current_leg_data["max_takeoff"] - zero_weight_here
        )

        max_by_takeoff_wt = min(max_by_takeoff_wt, FULL_TANK_WEIGHT)

        # leg burn
        leg_burn = current_leg_data["leg_burn"]

        max_landing_wt = current_leg_data["max_landing"] - zero_weight_here

        max_by_landing_wt = max_landing_wt + leg_burn

        return min(max_by_takeoff_wt, max_by_landing_wt)

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
                min_purchase_gal, max_purchase_gal, PURCHASE_GRANULARITY_GAL
        ):
            # calculate possible fuel states
            purchase_lbs = purchase_gal * FUEL_DENSITY_LBS_PER_GAL
            fuel_start_lbs = current_fuel_remaining_lbs + purchase_lbs
            next_fuel_remaining_lbs = fuel_start_lbs - this_leg["leg_burn"]

            # 2. Calculate Cost
            purchase_cost = purchase_gal * this_leg["fuel_price"]

            fee_paid = this_leg["parking_fee"]
            if purchase_gal >= this_leg["fee_waive_amount"]:
                fee_paid = 0

            new_total_cost = current_cost + purchase_cost + fee_paid

            # 3. Record the Purchase Action for this path
            action = {
                "leg": leg_key,
                "purchase_gallons": purchase_gal,
                "purchase_cost": round(purchase_cost, 2),
                "parking_fee_paid": fee_paid,
                "fuel_start_lbs": fuel_start_lbs,
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


if __name__ == "__main__":
    if(input("Would you like to enter new trip data? (y/n): ") == "y"):
        data = politeAsker()
        with open("tripData.json", "w+") as file:
            json.dump(data, file, inden=4)
    else:
        with open("tripData.json", "r") as file:
            data = json.load(file)
    file.close()

    fw = FuelWizard(data)
    best_cost, best_plan = fw.optimize_fuel_purchases(0)
    print(f"Total Cost: ${round(best_cost, 2)}")
    print(f"Plan: ")
    for each in best_plan:
        print(each)
