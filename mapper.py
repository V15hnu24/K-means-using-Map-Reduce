import grpc
import kmeans_pb2
import kmeans_pb2_grpc
from concurrent import futures
import os
import json
import math
from typing import Dict, List, Any

DATA_DIR = "Data/"
MAPPER_DIR = os.path.join(DATA_DIR, "Mappers")
PARAMETERS_FILE = os.path.join(DATA_DIR, "parameters.json")
INPUT_FILE = os.path.join(DATA_DIR, "Input", "points.txt")

class MapperServicer(kmeans_pb2_grpc.MapperServicer):
    def __init__(self, mapper_id):
        self.mapper_id: int = mapper_id
        self.centroids: Dict[int, List[float]] = {}
        self.input_data = []

    def read_input_data(self):
        with open(INPUT_FILE, "r") as file:
            self.input_data = [list(map(float, line.strip().split(','))) for line in file]

    def make_clean_folder(self):
        mapper_folder = os.path.join(MAPPER_DIR, f"M{self.mapper_id}")

        if not os.path.exists(mapper_folder):
            os.makedirs(mapper_folder)
        else:
            # If folder exists, delete existing partition files
            for filename in os.listdir(mapper_folder):
                file_path = os.path.join(mapper_folder, filename)
                if os.path.isfile(file_path) and filename.startswith("partition_"):
                    os.remove(file_path)

    def Map(self, request, context):
        # Process data and map to centroids

        print(f"Mapper {self.mapper_id} working..")
        if not request.centroids or not request.start_index+1 or not request.end_index:
            return kmeans_pb2.MapResponse(success=False)

        self.make_clean_folder()
        self.read_input_data()
        for centroid in request.centroids:
            centriod_id = centroid.centroid_id
            value = centroid.value
            self.centroids.update({centriod_id:value})

        print(self.centroids)

        print(f"Received indices {request.start_index} to {request.end_index} and centroids {self.centroids} at mapper_id {self.mapper_id}")    

        data = self.input_data[request.start_index:request.end_index]
        mapped_data = self.map_data_to_centroids(data)
        
        # Partition the data
        self.partition_data(mapped_data)
        return kmeans_pb2.MapResponse(success=True)

    def map_data_to_centroids(self, data):
        mapped_data: Dict[int, List[str]] = {centroid_id: [] for centroid_id in self.centroids}
        
        for point in data:
            nearest_centroid_id = self.find_nearest_centroid(point)
            mapped_data[nearest_centroid_id].append(point)
        
        return mapped_data

    def find_nearest_centroid(self, point):
        min_distance: float = float('inf')
        nearest_centroid: int = -1

        for centroid_id, centroid in self.centroids.items():
            distance = self.calculate_distance(point, centroid)
            if distance < min_distance:
                min_distance = distance
                nearest_centroid = centroid_id

        return nearest_centroid

    def calculate_distance(self, point, centroid):
        squared_distance = sum((x - y) ** 2 for x, y in zip(point, centroid))
        return squared_distance # Used Squared Euclidean distance as we just have to compare the distances.
    
    def partition_data(self, mapped_data):
        for centroid_id, points in mapped_data.items():
            partition_file = os.path.join(MAPPER_DIR, f"M{self.mapper_id}", f"partition_{centroid_id}.txt")
            with open(partition_file, "a") as file:
                for point in points:
                    file.write(f"{point}\n")

def serve(mapper_id, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_MapperServicer_to_server(MapperServicer(mapper_id), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"mapper {mapper_id} server started at port: {port}")
    server.wait_for_termination()

def main():
    with open(PARAMETERS_FILE, "r") as file:
        params = json.load(file)
        mapper_addresses = params["mapper_addresses"]

    # Start mapper servers concurrently
    with futures.ThreadPoolExecutor() as executor:
        # Submit tasks for starting mapper servers
        future_to_mapper_id = {executor.submit(serve, mapper_id, int(port)): mapper_id for mapper_id, port in mapper_addresses.items()}

        # Iterate over completed futures
        for future in futures.as_completed(future_to_mapper_id):
            mapper_id = future_to_mapper_id[future]
            try:
                # Get result of the completed future
                future.result()
                print(f"Mapper {mapper_id} server started successfully.")
            except Exception as e:
                print(f"Failed to start server for mapper {mapper_id}: {e}")

if __name__ == '__main__':
    main()
