# CosmosDB Mongo Vector Search with Python

This sample script creates a Mongo Cosmos collection and vector index

It then embeds sample text and stores the text along with its embedding vector

Finally a new sample text is embedded and that vector is used to query Mongo returning results along with similarity score

## Prerequisites

Cosmos Mongo Database + connection string - currently lowest tier of Azure Cosmos DB for MongoDB (vCore) supported is M30

AzureOpenAi instance with an embedding model
