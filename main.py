from drafter import *
from dataclasses import dataclass
from random import randint

set_site_information(
    author="Danny Bosma",
    description="Tesla Driving Simulator",
    sources="ChatGPT",
    planning="Planning document",
    links=["https://github.com/danny37-cyber/Tesla-Driving-Simulator"]
)

@dataclass
class Car:
    name: str
    max_range: int
    efficiency: float
    miles_driven: int
    range_remaining: float
    price: int

@dataclass
class Location:
    name: str
    price_to_attend: int
    mile_marker: int

@dataclass
class State:
    car: Car
    location: Location
    total_money_spent: float
    money_spent_charging: float
    user_balance: float
    vehicles: list[Car]
    locations: list[Location]
    visited_locations: list[Location]
    current_mile_marker: float

GAS_PRICE_MULTIPLIER = 3
GAS_CAR_MPG = 30
CHARGING_PRICE = 0.20

VEHICLES = [Car("Model S", 380, 1.6, 0, 380, 75000),
            Car("Model 3", 330, 1.8, 0, 330, 35000),
            Car("Model X", 350, 1.4, 0, 350, 80000),
            Car("Model Y", 320, 1.6, 0, 320, 40000)]

LOCATIONS = [Location("The Car Dealer🚘", 0, 0),
             Location("The Beach⛱️", 20, 25),
             Location("The Store🛍️", 75, 50),
             Location("Charger⚡️", 0, 75),
             Location("Disney World🐭", 1000, 100),
             Location("The Restaurant🍔", 120, 125),
             Location("The Club🪩", 180, 175),
             Location("Home🏡", 0, 200)]

@route
def index(state: State) -> Page:
    """Ask the user to enter a starting budget."""
    return Page(state, ["Tesla Driving Simulator\n",
                        "Enter a numerical starting balance:",
                        TextBox("budget"), "\n", Button("Submit", "display_vehicle_options")])

@route
def display_vehicle_options(state: State, budget: str) -> Page:
    """Show the cars the user can afford."""
    if budget.isdigit():
        state.user_balance = int(budget)
    else:
        return index(state)
    cars_can_buy = []
    for vehicle in state.vehicles:
        if state.user_balance >= vehicle.price:
            cars_can_buy.append(vehicle.name)
    if len(cars_can_buy) == 0:
        return Page(state, ["You cannot afford a Tesla yet.", Button("Back", "index")])
    return Page(state, ["Select a Tesla to test:",
                        RadioButtonGroup("selected", cars_can_buy), "\n",
                        Button("Submit", "select_vehicle")])

@route
def select_vehicle(state: State, selected: str) -> Page:
    """Purchase the chosen car and open the map."""
    for vehicle in state.vehicles:
        if selected == vehicle.name and state.user_balance >= vehicle.price:
            # Make a new car so driving does not change the catalog car.
            state.car = Car(vehicle.name, vehicle.max_range, vehicle.efficiency,
                            0, vehicle.max_range, vehicle.price)
            state.user_balance -= vehicle.price
            state.total_money_spent += vehicle.price
            return update_map(state)
    return Page(state, ["Car not available.", Button("Back", "index")])

def gasoline_cost_avoided(state: State) -> float:
    """Estimate gas spending avoided using a 30 MPG gasoline car."""
    return state.car.miles_driven / GAS_CAR_MPG * GAS_PRICE_MULTIPLIER


def energy_savings_text(state: State) -> str:
    """Explain whether electricity cost less or more than gasoline."""
    difference = gasoline_cost_avoided(state) - state.money_spent_charging
    if difference >= 0:
        return "Net energy-cost savings: $" + str(round(difference, 2))
    else:
        return "Extra energy cost: $" + str(round(abs(difference), 2))


@route
def show_stats(state: State) -> Page:
    """Display the driving and spending statistics."""
    return Page(state, [
        "Total money spent (car, visits, upgrades, charging): $" +
        str(round(state.total_money_spent, 2)), "\n",
        "Gasoline cost avoided: $" + str(round(gasoline_cost_avoided(state), 2)), "\n",
        "Charging cost: $" + str(round(state.money_spent_charging, 2)), "\n",
        energy_savings_text(state), "\n",
        "Total miles driven: " + str(round(state.car.miles_driven, 2)), "\n",
        "Places visited: " + str(len(state.visited_locations)), "\n",
        Button("Close", "update_map")
    ])


@route
def show_final_stats(state: State) -> Page:
    """Show the final statistics and a simple energy-cost recommendation."""
    savings = gasoline_cost_avoided(state) - state.money_spent_charging
    if state.car.miles_driven > 100 and savings > 20:
        recommendation = "Based on this simulation, the Tesla looks worthwhile."
    else:
        recommendation = "This simulation does not show enough savings to recommend buying."
    return Page(state, [
        "Total money spent (car, visits, upgrades, charging): $" +
        str(round(state.total_money_spent, 2)), "\n",
        "Gasoline cost avoided: $" + str(round(gasoline_cost_avoided(state), 2)), "\n",
        "Charging cost: $" + str(round(state.money_spent_charging, 2)), "\n",
        energy_savings_text(state), "\n",
        "Total miles driven: " + str(round(state.car.miles_driven, 2)), "\n",
        "FINAL RECOMMENDATION: " + recommendation, "\n",
        "This is a simplified comparison, not a full vehicle ownership cost analysis.", "\n",
        Button("Back", "update_map")
    ])


@route
def update_balance(state: State, added: str) -> Page:
    """Add money to the user's balance."""
    if added.isdigit():
        state.user_balance += int(added)
    else:
        return open_settings(state)
    return Page(state, ["Funds added!\n", "New balance: $" + str(round(state.user_balance, 2)), "\n",
                        Button("Close", "update_map")])

@route
def open_settings(state: State) -> Page:
    """Show the balance and a field for adding funds."""
    return Page(state, ["Current balance: $" + str(round(state.user_balance, 2)), "\n", "\n",
                        "Add funds: $", TextBox("added"), "\n",
                        Button("Confirm", "update_balance"),
                        Button("Cancel", "update_map")])

@route
def increase_efficiency(state: State, choice: str) -> Page:
    """Purchase a vehicle efficiency upgrade."""
    if choice == "tires":
        price = 800
        improvement = 0.3
    elif choice == "spoiler":
        price = 1000
        improvement = 0.4
    else:
        return display_upgrade_shop(state)
    if state.user_balance < price:
        return Page(state, ["Insufficient balance!\n", Button("Back", "display_upgrade_shop")])
    state.car.efficiency += improvement
    state.user_balance -= price
    state.total_money_spent += price
    return Page(state, ["Upgrade added!\n", "New efficiency: " + str(state.car.efficiency), "\n",
                        Button("Close", "update_map")])

@route
def display_upgrade_shop(state: State) -> Page:
    """Display the available car upgrades."""
    return Page(state, ["Vehicle efficiency: " + str(state.car.efficiency), "\n",
                        Button("Upgrade Tires ($800)", "increase_efficiency",
                               arguments={"choice": "tires"}),
                        Button("Upgrade Spoiler ($1000)", "increase_efficiency",
                               arguments={"choice": "spoiler"}),
                        Button("Back", "update_map")])

@route
def charging_station(state: State) -> Page:
    """Display the charging interface at the charging station."""
    if "Charger" not in state.location.name or state.current_mile_marker != state.location.mile_marker:
        return update_map(state)
    return Page(state, ["Tesla Charging Station\n",
                        "Current range: " + str(round(state.car.range_remaining, 2)), "\n",
                        "Maximum range: " + str(state.car.max_range), "\n",
                        "Price per rated-range mile: $" + str(CHARGING_PRICE), "\n",
                        "Current balance: $" + str(round(state.user_balance, 2)), "\n",
                        "Rated-range miles to add:", TextBox("miles"), "\n",
                        Button("Charge", "charge_car"), Button("Leave", "update_map")])

@route
def charge_car(state: State, miles: str) -> Page:
    """Purchase more range if the user has enough money."""
    if "Charger" not in state.location.name or state.current_mile_marker != state.location.mile_marker:
        return update_map(state)
    if not miles.isdigit():
        return charging_station(state)
    miles_to_add = int(miles)
    cost = miles_to_add * CHARGING_PRICE
    if miles_to_add <= 0:
        return charging_station(state)
    if state.car.range_remaining + miles_to_add > state.car.max_range:
        return Page(state, ["Cannot exceed maximum range!",
                            Button("Back", "charging_station")])
    if state.user_balance < cost:
        return Page(state, ["Not enough money!", Button("Back", "charging_station")])
    state.car.range_remaining += miles_to_add
    state.user_balance -= cost
    state.money_spent_charging += cost
    state.total_money_spent += cost
    return Page(state, ["Charging successful!\n",
                        "Range added: " + str(miles_to_add), "\n",
                        "Charging cost: $" + str(round(cost, 2)), "\n",
                        "New range: " + str(round(state.car.range_remaining, 2)), "\n",
                        Button("Continue", "update_map")])

@route
def go(state: State, destination: str) -> Page:
    """Drive to a location, with a random chance of crashing."""
    # This route uses randint, so test the possible results manually.
    traveling_to = None
    for location in state.locations:
        if str(location.mile_marker) == destination:
            traveling_to = location
            break
    if traveling_to == None:
        return Page(state, ["Destination not found.", Button("Back", "update_map")])
    range_needed = abs(traveling_to.mile_marker - state.current_mile_marker)
    # Efficiency scales road miles per unit of rated battery range.
    if state.car.efficiency <= 0:
        return Page(state, ["Vehicle needs repair.", Button("Back", "update_map")])
    battery_needed = range_needed / state.car.efficiency
    if state.user_balance < traveling_to.price_to_attend or state.car.range_remaining < battery_needed:
        return Page(state, ["Not enough money or driving range!", Button("Back", "update_map")])
    crash_decider = 1
    if range_needed > 0:
        crash_decider = randint(1, 10)
    if crash_decider == 10:
        # A crash happens halfway along the road.
        distance_driven = range_needed / 2
        if traveling_to.mile_marker > state.current_mile_marker:
            state.current_mile_marker += distance_driven
        else:
            state.current_mile_marker -= distance_driven
        state.car.range_remaining -= distance_driven / state.car.efficiency
        state.car.miles_driven += distance_driven
        state.car.efficiency -= 0.3
        if state.car.efficiency < 0.1:
            state.car.efficiency = 0.1
        return Page(state, ["You crashed!\n", "Miles traveled: " + str(distance_driven),
                            "New efficiency: " + str(state.car.efficiency),
                            Button("Close", "update_map"),
                            Button("Repair", "display_upgrade_shop")])
    state.car.range_remaining -= battery_needed
    state.car.miles_driven += range_needed
    state.user_balance -= traveling_to.price_to_attend
    state.total_money_spent += traveling_to.price_to_attend
    state.location = traveling_to
    state.current_mile_marker = traveling_to.mile_marker
    # The State list is meaningfully changed after visiting a new place.
    if traveling_to not in state.visited_locations:
        state.visited_locations.append(traveling_to)
    if "Charger" in traveling_to.name:
        return charging_station(state)
    return Page(state, ["You went to " + traveling_to.name + "\n",
                        "Miles traveled: " + str(range_needed), "\n",
                        "Range remaining: " + str(round(state.car.range_remaining, 2)), "\n",
                        "Money spent: $" + str(traveling_to.price_to_attend), "\n",
                        Button("Close", "update_map")])

@route
def update_map(state: State) -> Page:
    """Show destination buttons and the car's road position."""
    location_buttons = []
    for location in state.locations:
        if location.mile_marker == state.current_mile_marker:
            button_name = "🚗 " + location.name
        else:
            button_name = location.name
        location_buttons.append(Button(button_name, "go",
                                       arguments={"destination": str(location.mile_marker)}))
    page_contents = [Button("Simulation Stats", "show_stats"),
                     Button("Settings", "open_settings"),
                     Header("Choose a location to travel to.")] + location_buttons + ["\n"]
    if state.current_mile_marker != state.location.mile_marker:
        page_contents.append(Text("🚗 Car is between locations at mile " +
                                  str(state.current_mile_marker)))
    if "Charger" in state.location.name and state.current_mile_marker == state.location.mile_marker:
        page_contents.append(Button("Charge Vehicle", "charging_station"))
    page_contents.append(Button("UPGRADE SHOP", "display_upgrade_shop"))
    page_contents.append(Button("QUIT", "show_final_stats"))
    return Page(state, page_contents)

initial = State(None, LOCATIONS[0], 0, 0, 0, [Car("Model S", 380, 1.6, 0, 380, 75000),
            Car("Model 3", 330, 1.8, 0, 330, 35000),
            Car("Model X", 350, 1.4, 0, 350, 80000),
            Car("Model Y", 320, 1.6, 0, 320, 40000)], [Location("The Car Dealer🚘", 0, 0),
             Location("The Beach⛱️", 20, 25),
             Location("The Store🛍️", 75, 50),
             Location("Charger⚡️", 0, 75),
             Location("Disney World🐭", 1000, 100),
             Location("The Restaurant🍔", 120, 125),
             Location("The Club🪩", 180, 175),
             Location("Home🏡", 0, 200)], [], 0)
start_server(initial)
