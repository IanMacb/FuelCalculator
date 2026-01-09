import math
import sys
import json


FUEL_DENSITY_LBS_PER_GAL = 6.7
PURCHASE_GRANULARITY_GAL = 20


# TODO: fuckin fix it
#   put the weights in the same thing


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

    def open_file(self):
        with open("realtrip.json", "r") as fp:
            self.leg_dict = json.load(fp)

    def _get_max_fuel_start_lbs(self, leg_index: int) -> float:
        """
        Calculates the absolute maximum safe fuel (in lbs) the plane can have
        at takeoff for the specified leg.
        """
        leg_key = self.leg_keys[leg_index]
        current_leg_data = self.leg_dict[leg_key]

        # max takeoff weight at current airport
        max_by_takeoff_wt = current_leg_data["fuel_weight_max_takeoff"]

        # leg burn
        leg_burn = current_leg_data["leg_burn"]

        # the fuel_weight_max_landing for the *next* airport is needed.
        #   THIS IS DIFFERENT NOW, RESTRUCTURE IT LATER YOU FUCKIN IDIOT
        if leg_index + 1 < self.total_legs:
            # For intermediate legs, use the next airport's landing max
            next_leg_key = self.leg_keys[leg_index + 1]
            max_landing_wt = current_leg_data["fuel_weight_max_landing"]
            # max_landing_wt = self.leg_dict[next_leg_key]["fuel_weight_max_landing"]
        else:
            # For the final leg, use the destination's landing max from the current leg data
            # NOTE: The pilot must input this correctly for the last leg's destination.
            max_landing_wt = current_leg_data["fuel_weight_max_landing"]

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
            print(f"{round(self.min_trip_cost, 2)}")
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


if __name__ == "__main__":
    with open("realtrip_forreal.json", "r") as fp:
        leg_dict = json.load(fp)
    # leg_dict = fake_trip_generator.create_bigdict()
    for k, v in leg_dict.items():
        print(k, v)
    fw = FuelWizard(leg_dict)
    best_cost, best_plan = fw.optimize_fuel_purchases(0)
    print(f"Total Cost: {round(best_cost, 2)}")
    print(f"Plan: ")
    for each in best_plan:
        print(each)
