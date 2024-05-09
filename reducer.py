import os
import json
import grpc
import kmeans_pb2_grpc
import kmeans_pb2
from concurrent import futures

DATA_DIR = "Data/"
REDUCER_DIR = "Data/Reducers/"
MAPPER_DIR = "Data/Mappers/"
PARAMETERS_FILE = os.path.join(DATA_DIR, "parameters.json")

class ReducerServicer(kmeans_pb2_grpc.ReducerServicer):
    def __init__(self, reducer_id):
        self.reducer_id = reducer_id
        self.centroid_id = 0
        self.data_points = []

    def shuffle_and_sort(self):
        intermediate_data = []

        # Read intermediate key-value pairs from mappers' output files
        for mapper_folder in os.listdir(MAPPER_DIR):
            mapper_path = os.path.join(MAPPER_DIR, mapper_folder)
            partition_file = os.path.join(mapper_path, f"partition_{self.centroid_id}.txt")

            # Check if partition file exists for the current reducer ID
            if os.path.exists(partition_file):
                with open(partition_file, "r") as file:
                    # Read data from partition file
                    for line in file:
                        data_point = line.strip().strip('[]').split(", ")
                        # Convert values to integers
                        data_point = [int(float(value)) for value in data_point]
                        intermediate_data.append(data_point)

        return intermediate_data


    def create_clean_reducer_file(self):
        reducer_file = f"reducer_{self.reducer_id}.txt"
        reducer_file_path = os.path.join(REDUCER_DIR, reducer_file)

        # Check if reducer file exists
        if os.path.exists(reducer_file_path):
            # If file exists, delete it
            os.remove(reducer_file_path)
            print(f"Deleted existing reducer file: {reducer_file}")
        # Create a new empty reducer file
        with open(reducer_file_path, "w"):
            pass
        print(f"Created new reducer file: {reducer_file}")

    def Reduce(self, request, context):

        print(f"Reducer {self.reducer_id} running..")

        if not request.centroid_id+1:
            return kmeans_pb2.ReduceResponse(success=True, centroid_id = self.centroid_id, updated_centroid = None)
        

        self.create_clean_reducer_file()
        self.centroid_id = request.centroid_id
        self.data_points = self.shuffle_and_sort()

        # Calculate updated centroid by averaging data points
        updated_centroid = self.calculate_updated_centroid(self.data_points)

        # Write updated centroid to output file
        output_file = os.path.join(REDUCER_DIR, f"reducer_{self.reducer_id}.txt")
        with open(output_file, "w") as file:
            file.write(f"Centroid Id: {self.centroid_id}, Updated Centroid: {updated_centroid}\n")
        
        return kmeans_pb2.ReduceResponse(success=True, centroid_id = self.centroid_id, updated_centroid = updated_centroid)
    
    def load_parameters(self):
        with open(PARAMETERS_FILE, "r") as file:
            params = json.load(file)
            self.num_mappers = params["n_of_mappers"]
            self.num_reducers = params["n_of_reducers"]
            self.num_iterations = params["n_of_iterations"]
            self.num_centroids = params["n_of_centriods"]
            self.mapper_addresses = params["mapper_addresses"]

    def calculate_updated_centroid(self, data_points):
        if not data_points:
            return "No data points"

        dimensionality = len(data_points[0])  # Assuming all data points have the same dimensionality
        num_points = len(data_points)
        sum_points = [0] * dimensionality

        # Calculate sum of data points for each dimension
        for point in data_points:
            for i in range(dimensionality):
                sum_points[i] += point[i]

        # Calculate average for each dimension
        updated_centroid = [sum_val / num_points for sum_val in sum_points]
        return updated_centroid
    
def serve_reducer(reducer_id, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_ReducerServicer_to_server(ReducerServicer(reducer_id), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Reducer {reducer_id} server started successfully at port {port}.")
    server.wait_for_termination()

def main():
    # Read parameters file
    with open(PARAMETERS_FILE, "r") as file:
        params = json.load(file)
        reducer_addresses = params["reducer_addresses"]

    #Clean all the exisiting 

    # Initialize reducer servers
    with futures.ThreadPoolExecutor() as executor:
        # Submit tasks for starting reducer servers
        future_to_reducer_id = {executor.submit(serve_reducer, reducer_id, int(port)): reducer_id for reducer_id, port in reducer_addresses.items()}

        # Iterate over completed futures
        for future in futures.as_completed(future_to_reducer_id):
            reducer_id = future_to_reducer_id[future]
            try:
                # Get result of the completed future
                future.result()
                print("Reducers successfully started!")
            except Exception as e:
                print(f"Failed to start server for reducer {reducer_id}: {e}")


if __name__ == "__main__":
    main()
