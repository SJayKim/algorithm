import matplotlib.pyplot as plt
from haversine import haversine, Unit

def find_shortest_path(place_data):
    # place_data에서 place_coords를 추출하여 points 리스트 생성
    points = [(place_id, (info['lat'], info['lng'])) for place_id, info in place_data.items()]
    if not points:
        print("No points to optimize")
        return {}, 0

    n = len(points)
    min_distance = float('inf')
    best_path = []

    for start_index in range(n):
        start_place_id, start_coords = points[start_index]
        current_point = start_coords
        visited = [False] * n
        visited[start_index] = True
        current_path = [start_place_id]
        total_distance = 0

        for _ in range(n - 1):
            nearest_point = None
            nearest_distance = float('inf')

            for i in range(n):
                if not visited[i]:
                    _, point_coords = points[i]
                    # print(current_point, point_coords, type(current_point), type(point_coords))
                    d = haversine(current_point, point_coords, unit=Unit.KILOMETERS)
                    if d < nearest_distance:
                        nearest_distance = d
                        nearest_point = i

            if nearest_point is not None:
                visited[nearest_point] = True
                nearest_place_id, nearest_coords = points[nearest_point]
                current_path.append(nearest_place_id)
                total_distance += nearest_distance
                current_point = nearest_coords

        # 최종 경로의 거리가 최소 거리인지 확인
        if total_distance < min_distance:
            min_distance = total_distance
            best_path = current_path
            
    return best_path

def plot_points(points):
    plt.figure(figsize=(10, 6))
    x_points, y_points = zip(*points)
    plt.scatter(x_points, y_points, c='blue')
    plt.title("Points Before Optimization")
    plt.xlabel("Latitude")
    plt.ylabel("Longitude")
    plt.grid(True)
    plt.show()

def plot_path(points, path):
    plt.figure(figsize=(10, 6))
    x_points, y_points = zip(*points)
    plt.scatter(x_points, y_points, c='blue')

    if path:
        path_x, path_y = zip(*path)
        plt.plot(path_x, path_y, c='red', linestyle='-', marker='o')

    plt.scatter([path[0][0]], [path[0][1]], c='green', marker='o', s=100, label='Start')
    plt.title("Optimized Path")
    plt.xlabel("Latitude")
    plt.ylabel("Longitude")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    # 예제 좌표 (위도, 경도)
    points = {
        "A": {"lat": 35.1796, 
              "lng": 129.0756},
        "B": {"lat": 35.1608, 
              "lng": 129.1636},
        "C": {"lat": 35.1796,
              "lng": 129.0756},
        "D": {"lat": 35.1608,
              "lng": 129.1636}
    }    
    # # 포인트를 먼저 시각화
    # plot_points(points)
    
    # 최단 경로를 찾고 시각화
    best_path = find_shortest_path(points)
    print(best_path)
    exit()
    
    shortest_path, min_distance = find_shortest_path(points)
    print("최단 경로:", shortest_path)
    print("최단 거리:", min_distance)

    plot_path(points, shortest_path)
