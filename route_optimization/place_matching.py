from haversine import haversine, Unit
from collections import defaultdict
from pprint import pprint

def find_places_by_distance(reference_points, target_points, distance=5):
    spots_with_nearby_places = defaultdict(lambda: {'restaurants': [], 'cafes': []})

    for spot_id, spot_name, spot_lat, spot_lng in tourist_spots:
        for res_id, res_lat, res_lng, cat in restaurants:
            res_coords = (res_lat, res_lng)
            spot_coords = (spot_lat, spot_lng)
            dist = haversine(spot_coords, res_coords, unit=Unit.KILOMETERS)
            
            print(f"Distance between {spot_name} and {res_id}: {dist}")
            if dist <= distance:
                if cat in ["디저트 & 커피", "카페&베이커리"]:
                    spots_with_nearby_places[spot_name]['cafes'].append(res_id)
                else:
                    spots_with_nearby_places[spot_name]['restaurants'].append(res_id)

    return spots_with_nearby_places

# 예시 데이터
if __name__ == "__main__":
    tourist_spots = [
        (421, "Namsan Tower", 37.5512, 126.9882), 
        (422, "Gyeongbokgung Palace", 37.5796, 126.9770), 
        (423, "Myeongdong Shopping Street", 37.5600, 126.9858)]
    
    restaurants = [
        ("Rest1", 37.5541, 126.9886, "Korean Food"),       # Namsan Tower 근처
        ("Rest2", 37.5585, 126.9783, "Italian Food"),      # Gyeongbokgung Palace 근처
        ("Rest3", 37.5701, 126.9774, "디저트 & 커피"),      # Gyeongbokgung Palace 근처
        ("Rest4", 37.5610, 126.9838, "카페&베이커리"),      # Myeongdong Shopping Street 근처
        ("Rest5", 37.5621, 126.9842, "Japanese Food"),     # Myeongdong Shopping Street 근처
        ("Rest6", 37.5000, 127.0000, "Korean Food"),       # 조건에 안 걸리는 위치
        ("Rest7", 37.6000, 126.9000, "Italian Food"),      # 조건에 안 걸리는 위치
        ("Rest8", 37.5300, 127.0200, "디저트 & 커피"),      # 조건에 안 걸리는 위치
        ("Rest9", 37.5400, 126.9700, "카페&베이커리"),      # 조건에 안 걸리는 위치
        ("Rest10", 37.5900, 126.9500, "Japanese Food")     # 조건에 안 걸리는 위치
    ]

    result = find_places_by_distance(tourist_spots, restaurants, distance=5)
    pprint(result)
