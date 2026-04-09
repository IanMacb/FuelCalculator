import json
import math
import sys
import configparser
from shelper import SHelper
from pathlib import Path
import easygui

FUEL_DENSITY_LBS_PER_GAL = 6.7

def fileOpen(file_name, include_path=False):
    if include_path:
        path = ""
    else:
        path = f"{Path(__file__).absolute().parents[0]}/"
    with open(f"{path}{file_name}", "r") as file:
        data = json.load(file)
    file.close()
    return data

def fileSave(file_name, data, include_path=False):
    if include_path:
        path = ""
    else:
        path = f"{Path(__file__).absolute().parents[0]}/"
    with open(f"{path}{file_name}", "w+") as file:
        json.dump(data, file, indent=4)
    file.close()

class FuelWizard(SHelper):
    def __init__(self):
        super(FuelWizard, self).__init__()

        self.options = configparser.ConfigParser()
        self.path = Path(__file__).absolute().parents[0]
        self.options.read_file(open(f"{self.path}/options.cfg"))
        self.fuel_start = self.options.getint("Aircraft", "FUEL_START")
        self.fuel_reserve = self.options.getint("Aircraft", "FUEL_RESERVE")
        self.fuel_capacity = self.options.getint("Aircraft", "FUEL_CAPACITY")
        self.granularity = self.options.getint("Calculator", "GRANULARITY")

        try:
            self.trip_data = fileOpen("tripData.json")
        except FileNotFoundError:
            self.trip_data = []
        self.total_legs = len(self.trip_data)

        # keep track of the best plan and cost (cost initialized to a wild fucking value)
        self.min_trip_cost = sys.float_info.max
        self.best_purchase_plan = None
        self.mainloop()

    def mainloop(self):
        while True:
            cmd = input(f"{__class__.__name__}> ")
            response = self.parse_command(cmd)
            print()

    def cmd_add(self):
        """Add a leg to the existing trip."""

        leg_id = input("Please enter the Airport identifiers: ").upper()
        fuel_price = float(input("Fuel price at departure: ") or 0.00)
        parking_fee = float(input("Parking fee: ") or 0.00)
        fee_waive_amount = float(input("Amount to waive fee: ") or 0.00)
        leg_burn = int(input("Leg burn: ") or 0)
        max_takeoff = int(input("Max takeoff weight (default:35650): ") or 35650)
        max_landing = int(input("Max landing weight (default:30000): ") or 30000)
        zero_fuel_weight = int(input("Zero fuel weight: ") or 19000)

        new_leg_data = {
            "leg_id": leg_id,
            "fuel_price": fuel_price,
            "parking_fee": parking_fee,
            "fee_waive_amount": fee_waive_amount,
            "leg_burn": leg_burn,
            "max_takeoff": max_takeoff,
            "max_landing": max_landing,
            "zero_fuel_weight": zero_fuel_weight,
        }
        self.trip_data.append(new_leg_data)

        self.trip_update()
        if input("Add another leg? (y/n): ").lower() in ["y", "yes"]:
            self.cmd_add()

    def cmd_edit(self):
        self.list_legs()
        inpt = int(input("Which leg to edit: ")) - 1
        selected_leg = self.trip_data[inpt]

        print(f"\n---{selected_leg["leg_id"]}---")

        fuel_price = float(input(f"Fuel price at departure ({selected_leg["fuel_price"]}): ") or selected_leg["fuel_price"])
        parking_fee = float(input("Parking fee: ") or selected_leg["parking_fee"])
        fee_waive_amount = float(input("Amount to waive fee: ") or selected_leg["fee_waive_amount"])
        leg_burn = int(input("Leg burn: ") or selected_leg["leg_burn"])
        max_takeoff = int(input("Max takeoff weight: ") or selected_leg["max_takeoff"])
        max_landing = int(input("Max landing weight: ") or selected_leg["max_landing"])
        zero_fuel_weight = int(input("Zero fuel weight: ") or selected_leg["zero_fuel_weight"])

        edit_leg_data = {
            "leg_id": selected_leg["leg_id"],
            "fuel_price": fuel_price,
            "parking_fee": parking_fee,
            "fee_waive_amount": fee_waive_amount,
            "leg_burn": leg_burn,
            "max_takeoff": max_takeoff,
            "max_landing": max_landing,
            "zero_fuel_weight": zero_fuel_weight,
        }
        self.trip_data[inpt] = edit_leg_data
        self.trip_update()

    def cmd_remove(self):
        self.list_legs()
        inpt = int(input("Which leg to remove: ")) - 1
        if 0 <= inpt <= self.total_legs:
            print(f"{self.trip_data[inpt]["leg_id"]} removed")
            self.trip_data.pop(inpt)
        else:
            print("Not in range")

    def cmd_new(self):
        self.trip_data = []
        self.fuel_start = input("Fuel start: ")
        self.options.set("Aircraft", "FUEL_START", self.fuel_start)
        self.cmd_add()

    def cmd_view(self):
        self.list_legs()

    def cmd_calculate(self):
        best_cost, best_plan = self.optimize_fuel_purchases(
            self.fuel_start - self.fuel_reserve
        )
        print(
            f"\n{'Plan:'}"
            f"{'Fuel start: ':>56}{self.fuel_start:>9}"
            f"{'Total Cost:':>55} {'$':>{9 - len(str(f'{round(best_cost, 2):.2f}'))}}{round(best_cost, 2):.2f}{'':20}"
        )
        for e in best_plan:
            print(
                f"{e['leg_id']} : "
                f"{e['purchase_gallons']:4} gal @ "
                f"{'$':>{9 - len(str(f'{e["purchase_cost"]:.2f}'))}}{e['purchase_cost']:.2f} & "
                f"{'$':>{9 - len(str(f'{e["parking_fee_paid"]:.2f}'))}}{e['parking_fee_paid']:.2f} fee | "
                f"Fuel start/end: {e['fuel_start']:5}/{e['fuel_end']:<4} | "
                f"Takeoff weight: {e['takeoff_weight']:5}/{e['max_takeoff']:5} | "
                f"Landing weight: {e['landing_weight']:5}/{e['max_landing']:5}"
            )

    def cmd_options(self):
        self.fuel_start = int(input(f"Fuel start ({self.fuel_start}): ") or self.fuel_start)
        self.options.set("Aircraft", "FUEL_START", str(self.fuel_start))

        self.fuel_reserve = int(input(f"Reserve ({self.fuel_reserve}): ") or self.fuel_reserve)
        self.options.set("Aircraft", "FUEL_RESERVE", str(self.fuel_reserve))

        self.fuel_capacity = int(input(f"Fuel tank maximum capacity ({self.fuel_capacity}): ") or self.fuel_capacity)
        self.options.set("Aircraft", "FUEL_CAPACITY", str(self.fuel_capacity))

        self.granularity = int(input(f"Granularity ({self.granularity}): ") or self.granularity)
        self.options.set("Calculator", "GRANULARITY", str(self.granularity))

        self.options.write(open("options.cfg", "w+"))

    def cmd_import(self):
        file_name = easygui.fileopenbox(default=f"{self.path}/")
        self.trip_data = fileOpen(file_name, True)
        self.trip_update()

    def cmd_export(self):
        file_name = easygui.filesavebox(default=f"{self.path}/newTrip.json")
        fileSave(f"{file_name}", self.trip_data, True)

    def cmd_quit(self):
        exit()

    def get_max_fuel_start_lbs(self, leg_index: int) -> int:
        """
        Calculates the absolute maximum safe fuel (in lbs) the plane can have
        at takeoff for the specified leg.
        """
        current_leg_data = self.trip_data[leg_index]

        # amount the plane weighs if it was empty
        min_fuel_weight = current_leg_data["zero_fuel_weight"] + self.fuel_reserve

        # max takeoff fuel at current airport
        max_takeoff_fuel = current_leg_data["max_takeoff"] - min_fuel_weight
        max_takeoff_fuel = min(max_takeoff_fuel, self.fuel_capacity)

        # leg burn
        leg_burn = current_leg_data["leg_burn"]

        max_landing_fuel = current_leg_data["max_landing"] - min_fuel_weight
        # takeoff limit by landing weight limit
        max_by_landing_wt = max_landing_fuel + leg_burn

        # gives most restrictive of takeoff or landing weight limit
        return min(max_takeoff_fuel, max_by_landing_wt)

    def find_min_cost(self,
                      leg_index: int,
                      current_fuel_remaining_lbs: int,
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
            return

        # current leg data and constraints
        this_leg = self.trip_data[leg_index]

        # 1. Minimum fuel (lbs) required at Takeoff
        min_fuel_start_lbs = this_leg["leg_burn"]

        # 2. max fuel (lbs) allowed at Takeoff
        max_fuel_start_lbs = self.get_max_fuel_start_lbs(leg_index)

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
            burn = self.trip_data[leg_index]["leg_burn"]
            min_purchase_lbs = min(max_purchase_lbs, burn)
            min_purchase_gal = min(
                min_purchase_lbs / FUEL_DENSITY_LBS_PER_GAL, max_purchase_gal
            )

        # check for immediate infeasibility (if you get this error and I didn't fuck up, you can't do this flight I think)
        if min_purchase_gal > max_purchase_gal:
            # if the minimum required purchase exceeds the max allowed, this path is impossible.
            print(
                f"Minimum purchase gal is greater than max purchase gal for {this_leg["leg_id"]}. Figure your shit out. Maybe data is bad."
            )
            return

        # iterate through all possible fuel purchases for this leg.
        # min/max gal inclusive. Step by granularity.
        for purchase_gal in range(
                min_purchase_gal, max_purchase_gal, self.granularity
        ):
            # calculate possible fuel states
            purchase_lbs = purchase_gal * FUEL_DENSITY_LBS_PER_GAL
            fuel_start_lbs = current_fuel_remaining_lbs + purchase_lbs
            next_fuel_remaining_lbs = fuel_start_lbs - this_leg["leg_burn"]
            takeoff_weight = (
                    this_leg["zero_fuel_weight"] + self.fuel_reserve + fuel_start_lbs
            )
            landing_weight = takeoff_weight - this_leg["leg_burn"]

            # 2. Calculate Cost
            purchase_cost = purchase_gal * this_leg["fuel_price"]

            fee_paid = this_leg["parking_fee"]
            if purchase_gal >= this_leg["fee_waive_amount"] > 0:
                fee_paid = 0

            new_total_cost = current_cost + purchase_cost + fee_paid

            # 3. Record the Purchase Action for this path
            action = {
                "leg_id": this_leg["leg_id"],
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
            self.find_min_cost(
                leg_index + 1, next_fuel_remaining_lbs, new_total_cost, new_plan
            )

    def optimize_fuel_purchases(self, initial_fuel_lbs: int) -> (float, list):
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
            self.find_min_cost(
                leg_index=0,
                current_fuel_remaining_lbs=initial_fuel_lbs,
                current_cost=0.0,
                current_plan=[],
            )

            if self.min_trip_cost == sys.float_info.max:
                print("No feasible route found based on the provided constraints.")
                return self.min_trip_cost, []

            return self.min_trip_cost, self.best_purchase_plan

    def list_legs(self):
        print()
        for n, legs in enumerate(self.trip_data):
            print(f"[{n + 1}]:\t{legs["leg_id"]}")

    def trip_update(self):
        self.total_legs = len(self.trip_data)
        fileSave("tripData.json", self.trip_data)

if __name__ == "__main__":
    fw = FuelWizard()