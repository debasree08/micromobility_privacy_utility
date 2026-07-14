import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

def build_bike_graph(
    origin_lat,
    origin_lon,
    radius=3000
):
    """
    Download bicycle network around origin.
    """

    G = ox.graph_from_point(
        (origin_lat, origin_lon),
        dist=radius,
        network_type="bike"
    )

    return G



def reconstruct_route(
    G,
    origin_lat,
    origin_lon,
    destination_lat,
    destination_lon
):
    """
    Compute plausible bicycle route.
    """

    source = ox.distance.nearest_nodes(
        G,
        X=origin_lon,
        Y=origin_lat
    )

    target = ox.distance.nearest_nodes(
        G,
        X=destination_lon,
        Y=destination_lat
    )

    route = nx.shortest_path(
        G,
        source,
        target,
        weight="length"
    )

    return route



def plot_route(
    G,
    route
):
    """
    Visualize reconstructed route.
    """

    fig, ax = ox.plot_graph_route(
        G,
        route,
        route_linewidth=4,
        node_size=0,
        show=False,
        close=False
    )

    plt.show(block=True)

def infer_plausible_route(
    origin_lat,
    origin_lon,
    destination_lat,
    destination_lon
):

    G = build_bike_graph(
        origin_lat,
        origin_lon
    )

    route = reconstruct_route(
        G,
        origin_lat,
        origin_lon,
        destination_lat,
        destination_lon
    )

    plot_route(
        G,
        route
    )

    return route



def reconstruct_from_csv(csv_file, index=0):

    df = pd.read_csv(csv_file)

    row = df.iloc[index]

    return infer_plausible_route(

        row.origin_lat,
        row.origin_lon,

        row.destination_lat,
        row.destination_lon

    )

import argparse

def main():

    csv_file = "trajectory_results.csv"

    trajectory_index = 0      # Change this to visualize another trajectory

    print("Loading trajectory...")

    reconstruct_from_csv(
        csv_file,
        trajectory_index
    )

    print("Done.")


if __name__ == "__main__":

    main()


