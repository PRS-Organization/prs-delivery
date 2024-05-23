import json
import matplotlib.pyplot as plt
import numpy as np
import copy


class RoomMap(object):

    def __init__(self):
        self.floor1 = None
        self.floor2 = None
        self.floor3 = None
        # F1, f2, f3 = -16.69344711303711, -5.217403411865234, -0.0499998964369297
        self.height_floor1 = -16.693447
        self.height_floor2 = -5.2174
        self.height_floor3 = -0.0499999
        self.floor1_x0, self.floor1_y0, self.floor1_z0 = None, None, None
        self.maps_info = [
            {'x0': None, 'y0': None, 'z0': None, 'scale': None, 'width': None, 'height': None, 'grid': None},
            {'x0': None, 'y0': None, 'z0': None, 'scale': None, 'width': None, 'height': None, 'grid': None},
            {'x0': None, 'y0': None, 'z0': None, 'scale': None, 'width': None, 'height': None, 'grid': None}
        ]
        self.floors = [self.height_floor1, self.height_floor2, self.height_floor3]

    def get_world_position(self, n, i, j):
        x0, y0 = self.maps_info[n]['x0'], self.maps_info[n]['z0']
        scale, width, height = self.maps_info[n]['scale'], self.maps_info[n]['width'], self.maps_info[n]['height']
        x, y = x0 + i * scale, y0 + j * scale
        return x, self.floors[n], y

    def get_grid_position(self, n, x, y):
        x0, y0 = self.maps_info[n]['x0'], self.maps_info[n]['z0']
        scale, width, height = self.maps_info[n]['scale'], self.maps_info[n]['width'], self.maps_info[n]['height']
        # x, y = x0 + i * scale, y0 + j * scale
        i, j = (x - x0) / scale, (y - y0) / scale
        return round(i), round(j)

    def get_point_info(self, point):
        try:
            x, y, z = point['x'], point['y'], point['z']
        except:
            x, y, z = point[0], point[1], point[2]

        ind, value = min(enumerate(self.floors), key=lambda lis: abs(y - lis[1]))
        point_i, point_j = self.get_grid_position(ind, x, z)
        try:
            return ind, point_i, point_j, self.maps_info[ind]['grid'][point_i][point_j]
        except:
            i_max, j_max = np.array(self.maps_info[ind]['grid']).shape[0], np.array(self.maps_info[ind]['grid']).shape[
                1]
            p_i, p_j = min(point_i, i_max - 1), min(point_j, j_max - 1)
            return ind, p_i, p_j, self.maps_info[ind]['grid'][p_i][p_j]

    def get_an_aligned_world_coordinate_randomly(self, floor, x, y, random=1):
        point_i, floor_layer, point_j = self.get_world_position(floor, x, y)
        accuracy = self.maps_info[floor]['scale']
        random_x_i = np.random.uniform(point_i, point_i + accuracy)
        random_y_j = np.random.uniform(point_j, point_j + accuracy)
        return random_x_i, random_y_j

    def get_an_accessible_area(self, x, y, z, radius_meter=1.5, mode=0, sort=1, inflation=0):
        # mode 0 represent the world position, 1 is the matrix map(x=floor_n, y=map_i, z=map_j)
        if not mode:
            floor, map_i, map_j, is_obstacle = self.get_point_info([x, y, z])
        else:
            floor, map_i, map_j = round(x), round(y), round(z)
            is_obstacle = self.maps_info[floor]['grid'][map_i][map_j]
        map_array = np.array(self.maps_info[floor]['grid'])
        radius = radius_meter / self.maps_info[floor]['scale']
        # Determine the scope of the query domain
        min_i, max_i = round(max(0, map_i - radius)), round(min(map_array.shape[0] - 1, map_i + radius))
        min_j, max_j = round(max(0, map_j - radius)), round(min(map_array.shape[1] - 1, map_j + radius))
        # Find feasible points within the specified radius
        valid_points = []
        # exclude points with a distance of 1 from obstacles
        valid_points = []
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                if map_array[i, j] != 0 and ((i - map_i) ** 2 + (j - map_j) ** 2) <= radius ** 2:
                    too_close_to_obstacle = False
                    if inflation:
                        for ii in range(max(0, i - 1), min(map_array.shape[0], i + 2)):
                            for jj in range(max(0, j - 1), min(map_array.shape[1], j + 2)):
                                if map_array[ii, jj] == 0:
                                    too_close_to_obstacle = True
                    if not too_close_to_obstacle:
                        valid_points.append((i, j))
        if sort:
            # Calculate the distance from each feasible point to a given point
            distances = [np.sqrt((i - map_i) ** 2 + (j - map_j) ** 2) for i, j in valid_points]
            # Sort feasible points in ascending order of distance
            sorted_valid_points = [point for _, point in sorted(zip(distances, valid_points))]
            # print('here: ', len(sorted_valid_points), ' in radius ', radius_meter, ', scale', self.maps_info[floor]['scale'])
            return floor, sorted_valid_points
        else:
            return floor, valid_points

    def add_room(self, json_data):
        # parsing map information
        map_id = json_data['mapId']
        floor = json_data['mapName']
        width = json_data['width']
        height = json_data['height']
        points = json_data['points']
        scale = json_data['accuracy']
        positions = json_data['minPoint']
        n_length = scale
        x, y = 0, 0
        # Create a 2D matrix map
        # Analyze points and add point information to the map matrix
        n = 0
        map_data = []
        xx, yy = [], []
        # json_m = {"mapId": 1, "mapName": "F3", "width": 51, "height": 68, "accuracy": 1.0, "points": []}
        po = eval(points)
        for point in points:
            # point_data = json.loads(point)
            map_data.append(1)
        matrix = [[0 for _ in range(height)] for _ in range(width)]
        navMapPoints = [[None for _ in range(height)] for _ in range(width)]
        for i in range(width):
            for j in range(height):
                index = i * height + j
                matrix[i][j] = map_data[index]
                navMapPoints[i][j] = {"x": x + i * n_length, "y": y + j * n_length, "data": map_data[index]}
        flag = None
        if floor == 'F1':
            self.floor1 = po
            flag = 0
        elif floor == 'F2':
            self.floor2 = po
            flag = 1
        elif floor == 'F3':
            self.floor3 = po
            flag = 2
        # plt.show()
        self.maps_info[flag]['scale'] = scale
        self.maps_info[flag]['width'] = width
        self.maps_info[flag]['height'] = height
        self.maps_info[flag]['grid'] = po
        self.maps_info[flag]['x0'] = positions['x']
        self.maps_info[flag]['y0'] = positions['z']
        self.maps_info[flag]['z0'] = positions['z']
        self.floors[flag] = positions['y']
        # matrix_map = np.array(map_data).reshape((width, height))
        # Convert all values uniformly to values greater than or equal to 0
        # Create and initialize matrix
        # matrix = [[0 for _ in range(max_y)] for _ in range(max_x)]

    def draw(self, i, n, j):
        if isinstance(n, int) and isinstance(i, int) and isinstance(j, int):
            pass
        else:
            n, i, j, is_obstacle = self.get_point_info((i, n, j))
        mat = copy.deepcopy(self.maps_info[n]['grid'])
        mat[i][j] = 5
        plt.imshow(mat, cmap='gray')
        plt.title('Floor{}'.format(n))
        plt.show()

    def plot_map(self):
        map = self.floor3
        plt.imshow(map, cmap='gray')
        plt.title('Room Map')
        plt.grid(False)
        plt.axis('off')
        plt.xticks([])
        plt.yticks([])
        plt.show()

'''
points:["{\"viability\":false,\"position\":{\"x\":-19.94000244140625,\"y\":-0.0499998964369297,\"z\":-59.400001525878909}}"]
points:[[0/1,x,y,z],[0/1,-19.94000,-0.04999,-59.4000],[0/1,x,y,z]]
'''

if __name__ == '__main__':
    # read Map.json
    file_name = "map/map4.json"
    with open(file_name, 'r') as file:
        json_data = json.load(file)
    map = RoomMap()
    map.add_room(json_data)