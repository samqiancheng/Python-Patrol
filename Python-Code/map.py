
import osmnx as ox
import networkx as nx 
import numpy as np
import random as rn 
from intersection import Intersection
from road import Road 
from car import Car

class Map:
	def __init__(self, center_lat=47.608013, center_long=-122.335167, \
		dist=500, num_cars=10):
		center_pt = (center_lat, center_long)
		G = ox.graph_from_point(center_pt, network_type='drive', distance=dist)

		edge_dict = {}
		id = 0
		for e in G.edges(data=True):
			start = e[0]
			destination = e[1]
			tmp = e[2]['maxspeed']
			max_speed = tmp.split(" ")[0]
			num_lanes = e[2]['lanes'] 
			length = e[2]['length'] 
			#edge_to_insert = Road(id, start, destination, max_speed, num_lanes, length)
			#edge_list.append = edge_to_insert
			id+=1
		self.edge_map = edge_dict

		node_dict = {}
		for n in G.nodes(data=True):
			name = n[1]['osmid']
			x = n[1]['x']
			y = n[1]['y']
			outgoing_edges = [] #edges leaving this current node
			incoming_edges = [] #edges arriving to this current node
			incoming_lanes = 0  
			accsessible_nodes = [] #nodes that can be accessesed from this node
			 
			for e in edge_list:
				if e.u == name:
					outgoing_edges.append(e.id)
					accsessible_nodes.append(e.v)
				if e.v == name:
					incoming_edges.append(e.id)
					incoming_lanes += e.num_lanes
			#node_to_insert = TNode()
			#node_dict[n['osmid']] = node_to_insert
		self.node_map = node_dict

		start = rn.choice(node_dict.keys())
		destination = rn.choice(node_dict.keys())
		path = nx.dijkstra_path(G,start,destination)
		car_list = []
		for c in range(num_cars):
			"""
			if rand node is full:
			Option A 
			init car on a diff node 
			option B
			init car on on next t-frame
			option C
			init car on nearest road obj where start node
			would be either null or the closest edge
			choosing option B 
			"""
			#start = rn.choice(node_dict.keys())
			#destination = rn.choice(node_dict.keys())
			"""
			if destination == start:
				then what???
			"""
			#path = nx.dijkstra_path(G,start,destination)
			car_list.append(Car(start, destination, path))

		self.car_map = car_list

