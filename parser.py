import json
import math


class Parser:
    def __init__(self, step_meters=3.0):
        self.step_meters = step_meters

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def resample_coordinates(self, coords, step_meters=3.0):
        if not coords:
            return []

        resampled = [[coords[0][0], coords[0][1]]]
        dist_since_last_point = 0.0

        for i in range(1, len(coords)):
            p1 = coords[i - 1]
            p2 = coords[i]

            lon1, lat1 = p1[0], p1[1]
            lon2, lat2 = p2[0], p2[1]

            segment_length = self.haversine_distance(lat1, lon1, lat2, lon2)
            if segment_length == 0:
                continue

            dist_along_segment = 0.0

            while dist_since_last_point + (segment_length - dist_along_segment) >= step_meters:
                move_dist = step_meters - dist_since_last_point
                dist_along_segment += move_dist

                ratio = dist_along_segment / segment_length

                new_lon = lon1 + (lon2 - lon1) * ratio
                new_lat = lat1 + (lat2 - lat1) * ratio

                resampled.append([new_lon, new_lat])
                dist_since_last_point = 0.0

            dist_since_last_point += segment_length - dist_along_segment

        return resampled

    def process_track_file(self, input_filename, output_filename, step_meters=3.0):
        print(f"Читаем файл: {input_filename}...")

        with open(input_filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data.get("features", []):

            feature["properties"] = {}

            geom = feature.get("geometry", {})
            if geom.get("type") == "LineString":
                original_coords = geom.get("coordinates", [])
                original_count = len(original_coords)

                new_coords = self.resample_coordinates(original_coords, step_meters)

                geom["coordinates"] = new_coords

                print(f"Успешно! Было точек: {original_count} | Стало точек: {len(new_coords)}")

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Готово! Сохранено в файл: {output_filename}")


if __name__ == "__main__":
    INPUT_FILE = "track\\7524ТК68_Боронование_2_е_ГА_T01100200002_2.txt"
    OUTPUT_FILE = "TRACK.txt"

    Parser().process_track_file(INPUT_FILE, OUTPUT_FILE, step_meters=3.0)
