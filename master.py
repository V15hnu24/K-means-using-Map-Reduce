import grpc
import kmeans_pb2
import kmeans_pb2_grpc
from concurrent import futures
import os
import json
import random
import math
import time

DATA_DIR = "Data/"
INPUT_FILE = os.path.join(DATA_DIR, "Input", "points.txt")
MAPPER_DIR = os.path.join(DATA_DIR, "Mappers")
REDUCER_DIR = os.path.join(DATA_DIR, "Reducers")
CENTROIDS_FILE = os.path.join(DATA_DIR, "centroids.txt")
PARAMETERS_FILE = os.path.join(DATA_DIR, "parameters.json")

class KMeansServicer(kmeans_pb2_grpc.KMeansServicer):
    def __init__(self):
        self.num_mappers = 0
        self.num_reducers = 0
        self.num_centroids = 0
        self.num_iterations = 0
        self.mapper_addresses = {}
        self.input_data = []
        self.centroids = {}
        self.reducer_addresses = {}
        self.convergence_threshold = 0.000001
        self.iteration = 0
        self.chunks = []

    def RunKMeans(self, request, context):
        if not request.temp:
            return  kmeans_pb2.KMeansResponse(success=False)

        print(request.temp)

        print("Received Kmeans request on data from client")
        self.load_parameters()
        self.read_input_data()
        self.split_input_data()
        self.initialize_centroids()
        self.invoke_mappers()

        return kmeans_pb2.KMeansResponse(success=True)
        
    def load_parameters(self):
        with open(PARAMETERS_FILE, "r") as file:
            params = json.load(file)
            self.num_mappers = params["n_of_mappers"]
            self.num_reducers = params["n_of_reducers"]
            self.num_iterations = params["n_of_iterations"]
            self.num_centroids = params["n_of_centriods"]
            self.mapper_addresses = params["mapper_addresses"]
            self.reducer_addresses = params["reducer_addresses"]
        
    def read_input_data(self):
        with open(INPUT_FILE, "r") as file:
            self.input_data = [list(map(float, line.strip().split(','))) for line in file]

    def invoke_reducer(self):
        all_successful = True
        reducer_addresses = self.reducer_addresses
        centriods = {}

        # Iterate through reducer addresses in parallel
        with futures.ThreadPoolExecutor() as executor:
            future_to_reducer_id = {}
            for reducer_id, reducer_address in reducer_addresses.items():
                if int(reducer_id) > self.num_centroids:
                    break

                future = executor.submit(self.update_centroid_with_reducer, reducer_id, reducer_address)
                future_to_reducer_id[future] = reducer_id

            for future in futures.as_completed(future_to_reducer_id):
                reducer_id = future_to_reducer_id[future]
                try:
                    result = future.result()
                    if not result:
                        all_successful = False
                    print(result)
                    centriods.update({result[1]:result[2]})
                except Exception as e:
                    all_successful = False
                    print(f"Task for reducer {reducer_id} encountered an exception: {e}")

        if all_successful:
            print(centriods)
            self.compile_centroids_from_reducers(centriods)
            print("All reducers completed successfully.")
        else:
            print("Some reducers encountered errors.")

    def update_centroid_with_reducer(self, reducer_id, reducer_address):

        try:
            # Establish gRPC connection to reducer
            with grpc.insecure_channel(f'localhost:{reducer_address}') as channel:
                stub = kmeans_pb2_grpc.ReducerStub(channel)
                
                # Allocate centroid to reducer
                centroid_id = int(reducer_id)  # Assuming centroid ids start from 1 and match reducer ids
                request = kmeans_pb2.ReduceRequest(centroid_id=centroid_id)
                
                # Send gRPC request to update centroid
                response = stub.Reduce(request)
                if not response.success:
                    print(f"Re-running reducer {reducer_id}")
                    time.sleep(1)
                    self.update_centroid_with_reducer(reducer_id, reducer_address)

                print(f"Reducer {reducer_id}: centriod id - {response.centroid_id} Updated centroid - {response.updated_centroid}")

        except Exception as e:
            print(f"Exception occurred while communicating with reducer {reducer_id}: {str(e)}")
            print(f"Re-running reducer {reducer_id}")
            time.sleep(1)
            return self.update_centroid_with_reducer(reducer_id, reducer_address)

        return response.success, response.centroid_id, response.updated_centroid

    def split_input_data(self):
        chunk_size = len(self.input_data) // self.num_mappers
        remainder = len(self.input_data) % self.num_mappers
        
        chunks = []
        start_index = 0
        for i in range(self.num_mappers):
            chunk_end = start_index + chunk_size
            if i == self.num_mappers - 1:
                chunks.append((start_index, len(self.input_data)-1))
            else:
                chunks.append((start_index, chunk_end))
            start_index = chunk_end + 1
        
        self.chunks = chunks

    def send_input_to_mapper(self, mapper_id, data_chunk, mapper_address):
        try:
            centroids = []
            for centroid_id, value in self.centroids.items():
                centroid_message = kmeans_pb2.Centroid()
                centroid_message.centroid_id = centroid_id
                centroid_message.value.extend(value)
                centroids.append(centroid_message)

            print(f"Sending request to mapper {mapper_id}")
            channel = grpc.insecure_channel(f'localhost:{mapper_address}')
            print(f"Created channel for the mappeer {mapper_id}")
            stub = kmeans_pb2_grpc.MapperStub(channel)
            request = kmeans_pb2.MapRequest(mapper_id=mapper_id, start_index=data_chunk[0], end_index=data_chunk[1], centroids=centroids)
            response = stub.Map(request)
            channel.close()  # Close the channel after the RPC call

            print(f"{response.success} from mapper_id {mapper_id}")

            if not response.success:
                print(f"Re-running mapper {mapper_id}")
                time.sleep(1)
                self.send_input_to_mapper(mapper_id, data_chunk, mapper_address)

        except Exception as e:
            print(f"Exception occurred while communicating with mapper {mapper_id}: {str(e)}")
            print(f"Re-running mapper {mapper_id}")
            time.sleep(1)
            return self.send_input_to_mapper(mapper_id, data_chunk, mapper_address)

        return response.success

    def invoke_mappers(self):
        print("Invoked Mappers")

        chunks = self.chunks
        all_successful = True

        print(chunks)

        with futures.ThreadPoolExecutor(max_workers=self.num_mappers) as executor:
            future_to_mapper_id = {}
            for mapper_id, data_chunk in enumerate(chunks, start=1):
                print(f"mapper {mapper_id}  to data {data_chunk}")
                mapper_address = self.mapper_addresses.get(str(mapper_id))
                if mapper_address:
                    # data_point = kmeans_pb2.DataPoint(data_chunk[0], y=data_chunk[1])
                    print(f"Sent request to the mapper at {mapper_address}")
                    future = executor.submit(self.send_input_to_mapper, mapper_id, data_chunk, mapper_address)
                    future_to_mapper_id[future] = mapper_id
            
            for future in futures.as_completed(future_to_mapper_id):
                mapper_id = future_to_mapper_id[future]
                try:
                    result = future.result()
                    if not result:
                        all_successful = False
                except Exception as e:
                    all_successful = False
                    print(f"Task for mapper {mapper_id} encountered an exception: {e}")

        if all_successful:
            #Send calls to the reducers with the centriod ids.
            self.invoke_reducer()
            print("All mappers completed successfully.")
        else:
            print("Some mappers encountered errors.")

    def initialize_centroids(self):
        # Initialize centroids logic
        self.centroids = {i+1: random.choice(self.input_data) for i in range(self.num_centroids)}
        print("Initial centroids:", self.centroids)
    
    def compile_centroids_from_reducers(self, new_centroids):
        print(f"Iteration {self.iteration}")
        self.iteration += 1
        current_iteration = self.iteration
        prev_centroids = self.load_previous_centroids()
        max_iterations = self.num_iterations
        self.centroids = new_centroids
        print(self.centroids)

        # Check for convergence
        if self.is_converged(new_centroids, prev_centroids):
            print("K-Means algorithm converged.")
            self.write_centroids_to_file(new_centroids)  # Write centroids to centroids.txt
            return
        
        # Check if the maximum number of iterations is reached
        if current_iteration >= max_iterations:
            print(f"Maximum iterations ({max_iterations}) reached. Exiting.")
            self.write_centroids_to_file(new_centroids)  # Write centroids to centroids.txt
            return
        
        # If neither converged nor reached maximum iterations, continue iterations
        self.invoke_mappers()

    def write_centroids_to_file(self, centroids):
        with open(os.path.join(DATA_DIR, "centroids.txt"), "w") as file:
            for _, centroid in sorted(centroids.items()):
                file.write(','.join(map(str, centroid)) + '\n')

    def is_converged(self, new_centroids, prev_centroids):
        print("Checking Convergence..")
        # Check convergence by comparing the distance between old and new centroids

        if not prev_centroids:
            return False

        threshold = self.convergence_threshold
        for centroid_id,_ in new_centroids.items():
            if centroid_id not in prev_centroids:
            # If a centroid is not present in the previous centroids, consider it not converged
                return False

            # Calculate the Euclidean distance between the old and new centroids
            distance = self.euclidean_distance(prev_centroids[centroid_id], new_centroids[centroid_id])
        
            if distance > threshold:
                return False
        
        return True  # Converged

    def euclidean_distance(self, point1, point2):
        # Ensure both points have the same number of dimensions
        if len(point1) != len(point2):
            raise ValueError("Points must have the same number of dimensions")

        # Calculate the sum of squares of the differences of corresponding coordinates
        sum_of_squares = sum((coord1 - coord2) ** 2 for coord1, coord2 in zip(point1, point2))

        # Return the square root of the sum of squares
        return math.sqrt(sum_of_squares)

    def load_previous_centroids(self):
    # Load previous centroids from centroids_log.txt
        centroids_file = os.path.join('Data', 'centroids.txt')
        previous_centroids = {}

        if not os.path.exists(centroids_file) or os.path.getsize(centroids_file) == 0:
            return None  # Return None if the file is empty or doesn't exist

        with open(centroids_file, 'r') as f:
            for idx, line in enumerate(f, start=1):
                centroid = list(map(float, line.strip().split(',')))
                previous_centroids[idx] = centroid
        return previous_centroids

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_KMeansServicer_to_server(KMeansServicer(), server)
    server.add_insecure_port('[::]:50050')
    server.start()
    print("Master server started at 50050, waiting for the client direction to get the results...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
