import matplotlib.pyplot as plt
import constants as c
from car import Car
from intersection import Intersection as Node
from road import Road
import numpy as np
import utility as util
import navigate as nv
import visualizer as vis 

if __name__ == '__main__':
    '''Note
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    !For now, ts on each road is set to be 10!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    '''
    
    #- CONSTANTS are in constants.py Feel free to change
    
    nodes_file_path = 'map/nodes.npy'
    edges_file_path = 'map/edges.npy'
    
    #nodes, edges = util.retreiveMap(place=(47.608013, -122.335167),distance=1500,savefile=True)
    #nodes, edges = util.retreiveMap(place=(37.7749, -122.4194),distance=1000,savefile=True)

    #- If files do not exist, un-comment the line above and comment 3 lines below
    
    nodes, edges = util.retreiveMap(fromfile=True,filename=(nodes_file_path,edges_file_path))
    
    #- nodes and edges in dictionary form
    edge_id_distributor=0
    car_id_distributor=0
    nodes = util.node_to_object(nodes)
    edges = util.edge_to_object(edges)

    #badnodes = ['418825595','53142970']
    #rm_list = ['531678155', '425811432', '33294637199', '428248112']


    del nodes['53221383']
    new_edges = {}
    for key,edge in edges.items():
        id = str(edge_id_distributor)
        edge_id_distributor+=1
        u = str(edge.u)
        v = str(edge.v)
        if u in nodes and v in nodes:
            #new_edges[id] = Road(id,nodes[u],nodes[v],edge.max_speed,edge.num_lanes,edge.length)
            new_edges[id] = Road(id,nodes[u],nodes[v],edge.max_speed,edge.num_lanes,edge.length)
            nodes[u].add_edge(new_edges[id])
            nodes[v].add_edge(new_edges[id])
            nodes[u].cap += 4
            nodes[v].cap += 4
    edges = new_edges
    
    

    node_key = list(nodes.keys())
    edge_key = list(edges.keys())
    
    #- initialize navigator
    nv.init(nodes,edges,node_key,edge_key)
    
    #-some pairs of start and end dont work, do not why    

    car_backup = []

    car_size = c.NUMBER_CARS
    
    #- pick random starts and ends
    cars_u = np.random.randint(len(node_key),size=car_size)
    cars_v = np.random.randint(len(node_key),size=car_size)

    cars = []

    def initialize_car(i):
        st = nodes[node_key[cars_u[i]]]
        end = nodes[node_key[cars_v[i]]]
        paths = nv.dk(st.id,end.id,weight_on_length=1.0,parallel=True)
        while type(paths) is bool or len(paths) <=1 or st.isFull():
            #print('Re-routing')
            r_v = np.random.randint(len(nodes),size=2)
            while node_key[r_v[0]] == node_key[r_v[1]]:
                r_v = np.random.randint(len(nodes),size=2)
            st = nodes[node_key[r_v[0]]]
            end = nodes[node_key[r_v[1]]]
            #print(str(st),str(end))
            paths = nv.dk(st.id,end.id,weight_on_length=1.0,parallel=True)

        #car = Car(st,end,modified=True)
        #car.set_path(paths[1:])
        #car.id=i
        return str(st),str(end),paths
    from joblib import Parallel, delayed
    import time
    print('initializing cars...')
    ts = time.time()
    results = Parallel(n_jobs=8)(delayed(initialize_car)(i) for i in range(car_size))
    for i in range(len(results)):
        st = results[i][0]
        ed = results[i][1]
        path = results[i][2]
        car = Car(nodes[st],nodes[ed])
        car.set_path(list(path)[1:])
        car.id=i
        if nodes[st].add():
            cars.append(car)
    te = time.time()
    print('# of cars',len(cars),'time takes',te-ts)
    ccc = 0
    for k,v in nodes.items():
        ccc+=v.q_size
    print(ccc,'cars')
    #quit()

    # text=False to avoid edge id in plot
    visual = False
    if visual:
        vis.init_graph(nodes,edges,cars,text=False)

    total_time = 0
    compute=0
    skip=0
    #f = open('arrival-origin.txt','w')
    def dk_parallel(i):
        car=cars[i]
        nxt_move = str(car.paths[0])

        if nxt_move in edges:
            tmp_path = nv.dk(str(car.current_position),str(car.dest),weight_on_length=1.0,parallel=True)
            if type(tmp_path) != bool:
                nxt_move=tmp_path[1]
                if not edges[nxt_move].add():
                    return None
                return tmp_path #- tuple
    #from multiprocessing import Pool

    #P = pool(processes=8)

    while len(cars) > 0:
        car_indeces_re_rout = []
        rm_list = []
        for i in range(len(cars)):
            try:
                arrived = cars[i].current_position.id == cars[i].dest.id
            except IndexError:
                print(i,len(cars))
            if arrived:
                nodes[cars[i].current_position.id].remove()
                statement = '{1},{0} to {3},{2} time {4} {5}'.format(cars[i].start.x,cars[i].start.y,cars[i].dest.x,cars[i].dest.y,cars[i].total_ts,cars[i].id)
                #print('{1},{0} to {3},{2}'.format(car.start.x,car.start.y,car.dest.x,car.dest.y),car.total_ts)
                print(statement,len(cars))
                #print(statement,file=f)
                rm_list.append(i)
                #cars.remove(cars[i])
                continue
            else:
                total_time+=1
                cars[i].total_ts+=1
                nxt_move = str(cars[i].paths[0])
                #print(type(cars[i].current_position),cars[i].ts_on_current_position,cars[i].paths[0] in nodes, cars[i].paths[0] in edges)
                cur_pos = str(cars[i].current_position)
                #print('car position', cur_pos, type(car.current_position))
                if type(cars[i].current_position) == Road:
                    if cars[i].ts_on_current_position < edges[cur_pos].time_steps:
                        cars[i].ts_on_current_position += 1
                        continue
                else:
                    if cars[i].ts_on_current_position < nodes[cur_pos].time_steps:
                        cars[i].ts_on_current_position += 1
                        continue

                if nxt_move in edges:
                    car_indeces_re_rout.append(i)
                    #tmp_path = nv.dk(str(cars[i].current_position),str(cars[i].dest),weight_on_length=1.0)
                    #if type(tmp_path) != bool:
                    #    new_path = tmp_path
                    #    cars[i].set_path([str(new_path[1])])
                    #    next_move = cars[i].paths[0]
                    #if not edges[nxt_move].add():
                    #    #print('on hold edge',edges[nxt_move])
                    #    continue
                    #cars[i].current_position = edges[nxt_move]
                    #nodes[cur_pos].remove()
                    #cars[i].ts_on_current_position = 0
                elif nxt_move in nodes:
                    if not nodes[nxt_move].add():
                        #print('on hold node',nodes[nxt_move])
                        continue
                    cars[i].current_position = nodes[nxt_move]
                    edges[cur_pos].remove()
                    cars[i].ts_on_current_position = 0
                    cars[i].paths.pop(0)
        results = Parallel(n_jobs=8)(delayed(dk_parallel)(i) for i in car_indeces_re_rout)
        #print('car1',cars[0].current_position,cars[0].current_position.id)
        #print('car2',cars[1].current_position,cars[1].current_position.id)
        #print(results,[cars[i].id for i in car_indeces_re_rout])
        #input()
        for i in range(len(results)):
            path = results[i]
            indice = car_indeces_re_rout[i]
            #print(type(cars[indice].current_position),cars[indice].ts_on_current_position)
            #_rm = []
            if path is not None:
                cur_pos=str(cars[indice].current_position)
                cars[indice].set_path(list(path)[1:])
                nxt_move = cars[indice].paths[0]
                if edges[nxt_move].add():
                    nodes[cur_pos].remove()
                    cars[indice].current_position = edges[nxt_move]
                    cars[indice].ts_on_current_position=0
                    cars[indice].paths.pop(0)
        for r in rm_list:
            cars.pop(r)
        #pop path
        if visual:
            vis.update(cars)
    #f.close()
    if visual:
        plt.ion()
        plt.show()
    quit()

    #quit()
    cars=[]
    car_id_distributor=0
    for st, end in car_backup:
        car = Car(nodes[st],nodes[end],modified=True)
        paths = nv.dk(st,end,weight_on_length=0.5)
        car.set_path(paths[1:])
        car.id=car_id_distributor
        car_id_distributor+=1
        cars.append(car)
        nodes[st].add()
        total_time = 0
    compute=0
    skip=0
    #f = open('arrival-modified.txt','w')
    while len(cars) > 1:
        for car in cars:
            if car.current_position.id == car.dest.id:
                nodes[car.current_position.id].remove()
                statement = '{1},{0} to {3},{2} time {4} {5}'.format(car.start.x,car.start.y,car.dest.x,car.dest.y,car.total_ts,car.id)
                #print('{1},{0} to {3},{2}'.format(car.start.x,car.start.y,car.dest.x,car.dest.y),car.total_ts)

                print(statement)
                #print(statement,file=f)
                cars.remove(car)
            else:
                total_time+=1
                car.total_ts+=1
                nxt_move = str(car.paths[0].id)
                cur_pos = str(car.current_position.id)
                #print('car position', cur_pos, type(car.current_position))
                if type(car.current_position) == Road:
                    if car.ts_on_current_position < edges[cur_pos].time_steps:
                        car.ts_on_current_position += 1
                        continue
                else:
                    if car.ts_on_current_position < nodes[cur_pos].time_steps:
                        car.ts_on_current_position += 1
                        continue
                if nxt_move in edges:
                    #print(str(car.current_position),str(car.dest))
                    '''
                    Change True to modified
                    '''
                    if car.modified:
                        tmp_path = nv.dk(str(car.current_position),str(car.dest),weight_on_length=0.5)
                        if type(tmp_path) != bool:
                            new_path = tmp_path
                            car.set_path(new_path[1:])
                            nxt_move = new_path[1].id
                            compute+=1
                        else:
                            skip+=1
                        #print('re-calculated',compute,'skipped',skip)
                    if not edges[nxt_move].add():
                        #print('on hold edge',edges[nxt_move])
                        continue
                    car.current_position = edges[nxt_move]
                    nodes[cur_pos].remove()
                    car.ts_on_current_position = 0
                elif nxt_move in nodes:
                    if not nodes[nxt_move].add():
                        #print('on hold node',nodes[nxt_move])
                        continue
                    car.current_position = nodes[nxt_move]
                    edges[cur_pos].remove()
                    car.ts_on_current_position = 0
                car.paths.pop(0)
