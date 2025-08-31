### K-means-using-Map-Reduce

## Project problem statement
Implementing K-Means using MapReduce from scratch

0. Learning Resources

For this part of this assignment, you would need to be familiar with

K-Means clustering algorithm: K-means Clustering: Algorithm, Applications, Evaluation Methods, and Drawbacks
MapReduce Model
K-Means algorithm using MapReduce Framework (Section: 3.1)
Setup:

For the sake of simplicity, we will deploy the entire MapReduce framework on one machine. But note that each mapper and each reducer, as well as the master, will be a SEPARATE PROCESS (having an IP address (localhost) and a distinct port no.) on the same machine. Additionally, each mapper and each reducer will store their intermediate/output data in a separate file directory in the local file system (format specified in the “Sample Input & Output” section).
Mapper persists intermediate data
Reducer persists final output data
The use of gRPC for RPCs is mandatory for this assignment.
You may use any programming language you wish to use. We recommend using Python.
Google Cloud is not required for this assignment.
The K-Means algorithm
The K-means algorithm is an iterative algorithm that partitions a dataset into K clusters. The algorithm proceeds as follows:

Randomly initialize K cluster centroids.
Assign each data point to the nearest cluster centroid.
Recompute the cluster centroids based on the mean of the data points assigned to each cluster.
Repeat steps 2 and 3 for a fixed number of iterations or until convergence (i.e., until the cluster centroids no longer change significantly).
Refer to Section 3.1 of this paper for an explanation of how the K-Means clustering algorithm can be performed in a distributed manner. Note that you must implement the k-means algorithm from scratch (without using any library providing K-means algorithm function).


Implementation Details:
Your implementation should include the following components:

Master: The master program/process is responsible for running and communicating with the other components in the system. When running the master program, the following parameters should be provided as input:
number of mappers (M)
number of reducers (R)
number of centroids (K)
number of iterations for K-Means (Note: program should stop if the algorithm converges before)
Other necessary information (This should be reasonable. Please check with us - if you are not sure!)
Input Split (invoked by master): You will need to write code to divide the input data (single file) into smaller chunks that can be processed in parallel by multiple mappers. Your code does not need to produce separate input files for each mapper, but each mapper should process a different chunk of the file input data.
For partitioning the input data across different mappers, there are two possibilities:
Scenario 1: Input data contains only one big file. Each mapper reads the entire input file and then processes only the indices allocated to it by the master.
Scenario 2: ⁠⁠Input data contains multiple files. Each mapper is responsible for a subset of these files (exact subset of files is allocated by Master).
In both the above scenarios, the master does not distribute the actual data to the mappers as that is going to be unnecessary network traffic.

For the purpose of this assignment, you are free to choose either one or both of the above scenarios.

Master should try to split the data equally (or almost equally) based on the number of mappers.

Map (invoked by mapper):
You will need to write code to apply the Map function to each input split to generate intermediate key-value pairs.
Mapper should read the input split by itself (based on the information provided by the master). Master should not send the input data points to the mapper.
Inputs to the Map function: 
Input split assigned by the master:
This split contains a list of data points
Range of Indices (Scenario 1) or List of file names (Scenario 2)
List of Centroids from the previous iteration
Other necessary information (This should be reasonable. Please check with us - if you are not sure!)
Output from the Map function: For each data point processed by the map function, the function outputs:
Key: index of the nearest centroid to which the data point belongs
Value: value of the data point itself.
The output of each Map function should be written to a file in the mapper’s directory on the local file system. (Look at the directory structure given below)
The output of each Map function should be passed to the partition function which will then write the output in a partition file inside the mapper’s directory on the local file system. (Look at the directory structure given below)
Note that each mapper needs to run as a separate process.
[Added on April 14th, 2024] Please ensure that mappers run in parallel, not sequentially. This is obvious but I have added it explicitly as some students seem to be running mappers sequentially using synchronous RPC calls in a loop.
Partition (invoked by mapper):
The output of the Map function (as mentioned in the mapper above) needs to be partitioned into a set of smaller partitions.
In this step, you will write a function that takes the list of key-value pairs generated by the Map function and partitions them into smaller partitions.
The partitioning function should ensure that
all key-value pairs belonging to the same key are sent to the same partition file.
distribute the different keys equally (or almost equally) among each of the partitions. This can be done using very simple and reasonable partition functions ( such as key % num_reducers)
Each partition file is picked up by a specific reducer during shuffling and sorting.
If there are M mappers and R reducers, each mapper should have R file partitions. This means that there will be M*R partitions in total.
This step is performed by the mapper.
Shuffle and sort (invoked by reducer): 
You must write code to sort the intermediate key-value pairs by key and group the values that belong to the same key.
This is typically done by sending the intermediate key-value pairs to the reducers based on the key.
This step is performed by the reducer.
Reduce (invoked by reducer): 
The reducer will receive the intermediate key-value pairs from the mapper, perform the shuffle & sort function as mentioned, and produce a set of final key-value pairs as output.
You will need to write code to apply the Reduce function to each group of values that belong to the same key to generate the final output.
Input to the reduce function:
Key: Centroid id
Value: List of all the data points which belong to this centroid id (this information is available after shuffle and sorting)
Other necessary information (This should be reasonable. Please check with us - if you are not sure!)
Output of the reduce function:
Key: Centroid Id
Value: Updated Centroid
The output of each Reduce function should be written to a file in the reducer’s directory on the local file system.
Note that each reducer needs to run as a separate process.
[Added on April 14th, 2024] Please ensure that once the mappers have finished, all the reducers run in parallel, not sequentially. This is obvious but I have added it explicitly as some students seem to be running reducers sequentially using synchronous RPC calls in a loop.
Centroid Compilation (invoked by master): The master needs to parse the output generated by all the reducers to compile the final list of (K) centroids and store them in a single file. This list of centroids is considered as input for the next iteration. Before the first iteration, the centroids should be randomly selected from the input data points.
Master must use gRPC calls to contact the Reducer for reading the output files (since in practice, master and reducer are not running on the same machines)
Alternatively, Reducer can send the output file data as part of the response of the initial RPC request sent by the master (for running the reduce task). If you do this, then the master does not need to do a separate RPC for reading the output files from reducers.
Important Notes:

Reducers should not read their input key-value pairs from the generated intermediate files; instead, they should perform gRPC calls to the mappers to get the input. (Mapper however should read the input data points from the input files itself).
Fault Tolerance: Your implementation should take care of any failures associated with mapper or reducer. If a mapper or reducer fails, then the master should re-run that task to ensure that the computations finish. We will test two failure scenarios:
Scenario 1: Mapper/reducer may encounter an error due to which it is not able to complete the allocated task. In that case, it will return "unsuccessful or failed" message to master.
This is very easy to test. You can add a “probabilistic” flag just before return to the master. The flag can be randomly set to false or true (probability for false can be 0.5 or higher so that some failure happens for sure). If the flag is false, return fail. else, return success. This is very easy to implement and test how the master deals with failures.
Scenario 2: We may force stop a mapper or reducer process. [This seems difficult to test if you spawn mappers and reducers from the master itself. But if they are spawned from a separate terminal, then it is easy to test as we can just kill the mapper process. You may have to add a sleep statement in mapper code to ensure you get sufficient time to kill the mapper.]
[Added on April 17th, 2024] If you are running mappers and reducers from the master itself, then for your own testing, you can add sleep statements and kill the mapper/reducer using pid from command line.
In both cases, master should ensure the failed task gets reassigned to the same or different mapper/reducer.

gRPC communication:

The gRPC communication between the three processes for each iteration looks something like this:

Master ⇔ Mapper (master sends necessary parameters to mapper, mapper performs map & partition)
Master ⇔ Reducer (after all mappers have returned to master successfully, master invokes reducers with the necessary parameters)
Reducer ⇔ Mapper (after invocation, reducers communicates with the mapper to get the input before the shuffle, sort, and reduce step)
Master ⇔ Reducer (after all reducers have returned to master successfully, master contacts the reducers to read the output datafiles)
Alternatively, Reducer can send the output file data as part of the response of the RPC request in point 2 above. If you do this, then the master does not need to do a separate RPC for reading the output files from reducers.
Sample input and output files:
We will provide sample input and output files for each application to have uniformity in evaluation. You should ensure that your code runs successfully in the provided format of sample input files and generates the final output files in the same format as the sample output files.


Data/

├─ Input/

│  ├─ points.txt (initial points)

├─ Mappers/

│  ├─ M1/

│  │  ├─ partition_1.txt

│  │  ├─ partition_2.txt

...

│  │  ├─ partition_R.txt (R based on the number of reducers)

│  ├─ M2/ ...

│  ├─ M3/ ...

...

├─ Reducers/

│  ├─ R1.txt

│  ├─ R2.txt

├─ centroids.txt (final list of centroids)


Please have a look at two more test cases for your reference here.

Print Statements:
Please log/print everything in a dump.txt file (just like we did in assignment 2) for easy debugging/monitoring.


Print/Display the following data while executing the master program for each iteration:

Iteration number
Execution of gRPC calls to Mappers or Reducers
gRPC responses for each Mapper and Reducer function (SUCCESS/FAILURE)
Centroids generated after each iteration (including the randomly initialized centroids)
Deliverables
Submit a zipped file containing the entire code with the given directory structure.
Evaluation
Your assignment will be evaluated on the following criteria:

You must test the master with different numbers of mappers, reducers, centroids, and iterations.
You can either set up the mapper and reducer processes before running the master process, or you can allow the master process to spawn the mapper and reducer processes as and when required.
The outputs of
Mappers
Reducers
will be verified for different configurations.






# Distributed K-Means Clustering using MapReduce with GRPC

This repository contains an implementation of a distributed K-Means clustering algorithm using gRPC for inter-process communication. The project is designed to distribute the workload of the K-Means clustering algorithm across multiple mapper and reducer nodes of MapReduce algorithm. 

## Table of Contents

- [Introduction](#introduction)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Proto Definitions](#proto-definitions)
- [Functions](#functions)
- [License](#license)

## Introduction

K-Means clustering is a popular unsupervised machine learning algorithm used to partition data into clusters based on similarity. This project leverages gRPC to distribute the computational workload across multiple nodes, making it suitable for large datasets.

## Architecture

The project is composed of three main components:

1. **Master Node**: Manages the overall execution of the K-Means algorithm, distributes tasks to mappers and reducers, and aggregates results.
2. **Mapper Nodes**: Receive data chunks and initial centroids, assign data points to the nearest centroids, and send the results to the reducers.
3. **Reducer Nodes**: Aggregate the results from mappers to compute new centroids and determine if the algorithm has converged.

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/distributed-kmeans.git
   cd distributed-kmeans
   ```

2. **Install dependencies**:
   Ensure you have Python 3.7+ and `pip` installed. Then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Compile the protobuf files**:
   ```bash
   python -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=. kmeans.proto
   ```

## Usage

1. **Start the Master Node**:
   ```bash
   python master.py
   ```

2. **Start the Mapper Nodes**:
   ```bash
   python mapper.py
   ```

3. **Start the Reducer Nodes**:
   ```bash
   python reducer.py
   ```

4. **Run the Client**:
   ```bash
   python client.py
   ```

## Project Structure

```
distributed-kmeans/
│
├── Data/
│   ├── Input/
│   │   └── points.txt           # Input data points
│   ├── Mappers/
│   ├── Reducers/
│   ├── centroids.txt            # Initial centroids
│   └── parameters.json          # Configuration parameters
│
├── kmeans.proto                 # Protobuf definitions
├── master.py                    # Master node implementation
├── mapper.py                    # Mapper node implementation
├── reducer.py                   # Reducer node implementation
├── client.py                    # Client to start the K-Means process
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## Proto Definitions

The `kmeans.proto` file defines the messages and services for the gRPC communication:

```proto
syntax = "proto3";

package kmeans;

service Master {
  rpc RunKMeans(KMeansRequest) returns (KMeansResponse);
}

service Mapper {
  rpc Map(MapRequest) returns (MapResponse);
}

service Reducer {
  rpc Reduce(ReducerRequest) returns (ReducerResponse);
}

message KMeansRequest {
  bool temp = 1;
}

message KMeansResponse {
  bool success = 1;
  map<int32, Centroid> centroids = 2;
}

message MapRequest {
  int32 mapper_id = 1;
  int32 start_index = 2;
  int32 end_index = 3;
  repeated Centroid centroids = 4;
}

message MapResponse {
  bool success = 1;
}

message ReducerRequest {
  int32 centroid_id = 1;
}

message ReducerResponse {
  bool success = 1;
  int32 centroid_id = 2;
  Centroid updated_centroid = 3;
}

message Centroid {
  int32 centroid_id = 1;
  repeated double coordinates = 2;
}
```

## Functions

### Master Node (`master.py`)

- **run_kmeans**: Starts the K-Means process by sending requests to mappers and reducers.
- **load_parameters**: Loads configuration parameters from a JSON file.
- **read_input_data**: Reads the input data points from a file.
- **split_input_data**: Splits the input data into chunks for the mappers.
- **initialize_centroids**: Initializes the centroids randomly from the input data.
- **invoke_mappers**: Sends data chunks and centroids to mappers.
- **invoke_reducer**: Sends results from mappers to reducers for aggregation.
- **is_converged**: Checks if the centroids have converged.
- **euclidean_distance**: Calculates the Euclidean distance between two points.
- **load_previous_centroids**: Loads the previous centroids from a file.
- **write_centroids_to_file**: Writes the current centroids to a file.

### Mapper Node (`mapper.py`)

- **Map**: Receives data chunks and centroids, assigns data points to the nearest centroids, and sends the results to the reducers.
- **read_input_data**: Reads the input data points from a file.
- **map_data_to_centroids**: Assigns data points to the nearest centroids.
- **partition_data**: Partitions the mapped data and writes it to files.

### Reducer Node (`reducer.py`)

- **Reduce**: Aggregates the results from mappers to compute new centroids.
- **read_partition_data**: Reads the partitioned data from mappers.
- **compute_new_centroid**: Computes the new centroid from the assigned data points.

---

This README provides an overview of the project structure, setup instructions, and a brief description of the main components and their functions. Ensure that you adjust file paths, parameters, and other project-specific details as needed.
