import grpc
import kmeans_pb2
import kmeans_pb2_grpc

def run_kmeans():
    # Open a gRPC channel
    channel = grpc.insecure_channel('localhost:50050')
    # Create a stub for the KMeans service
    stub = kmeans_pb2_grpc.KMeansStub(channel)
    
    # Create a request object
    request = kmeans_pb2.KMeansRequest(temp=True)

    try:
        # Call the RunKMeans RPC method
        response = stub.RunKMeans(request)
        if response.success:
            print("KMeans algorithm successfully executed.")
        else:
            print("Failed to execute KMeans algorithm.")
    except grpc.RpcError as e:
        print(f"Error occurred: {e}")

if __name__ == '__main__':
    run_kmeans()
