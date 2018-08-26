import sys

import numpy as np
import pandas as pd

# Read data from stdin
flight_data = pd.read_csv(sys.stdin)

# Convert arrival and departure to datetime
flight_data["arrival"] = pd.to_datetime(flight_data["arrival"])
flight_data["departure"] = pd.to_datetime(flight_data["departure"])

# Precompute an array with all connections between flights
possible_connections = pd.DataFrame(np.zeros([len(flight_data), len(flight_data)]))

for flight_id in flight_data.index:
    flight = flight_data.iloc[flight_id]
    possible_connections[flight_id] = ((flight_data["source"] == flight.destination) &
                                       (flight_data["departure"] >= flight.arrival + pd.offsets.Hour(1)) &
                                       (flight_data["departure"] <= flight.arrival + pd.offsets.Hour(4)))


# Function looks in the connections array and adds all possible connections, recursively
def add_connections(flight_ids):
    out = [flight_ids]

    # look at all the possible connections from the last destination of the flight
    for possible_connection in possible_connections[flight_ids[-1]].loc[possible_connections[flight_ids[-1]]].index:
        new_connection = flight_ids + [possible_connection]

        # check if flying from a destination more than once, i.e. visiting a destination twice. Arriving at a
        # destination twice and not leaving is fine as that is the case of returning to the original destination,
        # which is allowed.
        if max(flight_data.loc[new_connection].source.value_counts()) > 1:
            continue

        # save the connection and recursively check for more connections
        out += [new_connection]
        out += add_connections(new_connection)

    return out


# find all possible connections for each flight
all_connections = []
for i in flight_data.index:
    all_connections += add_connections([i])

# check the maximum number of bags for each flight
max_bags = []
for connection in all_connections:
    max_bags += [min(flight_data.iloc[connection].loc[:, "bags_allowed"])]

all_connections = pd.DataFrame(data={"connections": all_connections, "bags_allowed": max_bags})

# Print out all solutions
for num_bags in range(3):
    print("Options for ", num_bags, "bags.")
    print("source, stops(s)('direct' if no stop), destination, departure, arrival, total_price_incl_bags, flight_ids")
    for connection in all_connections.loc[all_connections["bags_allowed"] >= num_bags, "connections"].values:
        result = [flight_data.iloc[connection[0]].source]
        if len(connection) < 2:
            result += ["direct"]
        else:
            result += [flight_data.iloc[connection[1:]].source.values.tolist()]
        result += [flight_data.iloc[connection[-1]].destination]
        result += [flight_data.iloc[connection[0]].departure]
        result += [flight_data.iloc[connection[-1]].arrival]
        result += [sum(flight_data.iloc[connection].loc[:, "price"]) +
                   sum(flight_data.iloc[connection].loc[:, "bag_price"]) * num_bags]

        result += [connection]

        print(result)
