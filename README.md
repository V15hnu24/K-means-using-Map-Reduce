### K-means-using-Map-Reduce


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
