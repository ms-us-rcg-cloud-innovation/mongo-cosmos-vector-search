import os
from dotenv import load_dotenv
import requests
import json
import pymongo

load_dotenv(override=True)

# ----------------- Set Up Mongo -----------------

# connect to MongoDB
client = pymongo.MongoClient(os.environ.get("MONGO_DB_CONNECTION_STRING"), tlsAllowInvalidCertificates=True)
db = client.get_database("test")

# drop the collection if it exists
# if "vectors" in db.list_collection_names():
#     db.get_collection("vectors").drop()

# create a new collection if it doesnt exist
if "vectors" not in db.list_collection_names():
    db.create_collection("vectors")
    
    

collection = db.get_collection("vectors")

# test connection string
print(client.list_database_names())

# print all the collections in the database
print(db.list_collection_names())

collection = db.get_collection("vectors")

create_vector_index = {
    "createIndexes": "vectors",  # Replace 'vectors' with your actual collection name if different
    "indexes": [
        {
            "name": "vector_index",  # You can customize the index name
            "keys": {"vector_field": "cosmosSearch"},  # Replace 'vector_field' with your actual vector field
            "cosmosSearchOptions": {
                # "kind": "vector-ivf",
                "kind": "vector-hnsw",
                "efConstruction": 200,  # - ONLY FOR hnsw
                # 'numLists': 1, # - ONLY FOR ivf
                "similarity": "COS",  # Or "euclidean" based on your needs
                "dimensions": 1536  # Set the dimension of your vector
            }
        }
    ]
}

# delete vector index
# collection.drop_index("vectors")

# # Create the vector index if it doesn't exist
if "vector_index" not in collection.index_information():
    collection.create_indexes([pymongo.IndexModel(**create_vector_index['indexes'][0])])

# print all indexes
print(collection.index_information())

# ----------------- Embedding the Data -----------------

embedding_deployment_url = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_URL")
embedding_deployment_name = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

url = f"{embedding_deployment_url}/openai/deployments/{embedding_deployment_name}/embeddings?api-version=2024-02-01"

api_key = os.environ.get("AZURE_OPENAI_API_KEY")

# Set the headers
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

# Define the payload with the input text
payload = json.dumps({
    "input": "The food was delicious and the waiter was very friendly."
})

# Make the POST request
response = requests.post(url, headers=headers, data=payload)

embedding = response.json()["data"][0]["embedding"]

# ----------------- Store In Mongo -----------------

document = {"text": "The food was delicious and the waiter was very friendly.", "vector_field": embedding}
collection.insert_one(document)
print("Stored embedding in MongoDB ivf index")
print(collection.index_information())



# ----------------- Embedding the Query (user question that will be used to match with docs in Mongo) -----------------
payload2 = json.dumps({
    "input": "food was delicious"
})

# Make the POST request to get an embedding for the query
response2 = requests.post(url, headers=headers, data=payload2)
query_vector = response2.json()["data"][0]["embedding"]

# ----------------- Execute Query Against Mongo -----------------

pipeline = [
    {
        "$search": {
            "index": "vectors",  # Ensure this matches the name of your vector index
            "cosmosSearch": {
                "vector": query_vector,
                "path": "vector_field",  # The field where the vector is stored
                "k": 10, # Number of nearest neighbors to retrieve
                "similarity": "COS"  # Or "euclidean"
            }
        }
    },
    {
        "$project": {
            "_id": 0, 
            "text": 1,
            "score": {"$meta": "searchScore"} # return search score

        }
    }
]

# Execute the search
results = collection.aggregate(pipeline)

# Print results
for document in results:
    print(document)