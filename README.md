## Great NEWS ##
Now **GraphDBLP** has been provided by a wonderful Web GUI interface. Build your own following instructions at [Backend with autocomplete service](https://github.com/andreascrivanti/GraphDBLP-backend) and [Frontend](https://github.com/andreascrivanti/GraphDBLP-frontend)
Have a look to the [ECML-PKDD 2019 demo video](https://www.youtube.com/watch?v=eoDX-782Z8M&feature=youtu.be)

## What is GraphDBLP?

**GraphDBLP** is a tool that models the [DBLP bibliography](http://dblp.uni-trier.de/) as a graph database for performing graph-based queries and social network analyses.

**GraphDBLP** also enriches the DBLP data through semantic keyword similarities computed via [word-embedding](https://arxiv.org/pdf/1411.2738.pdf). **GraphDBLP** provides to users three meaningful queries for exploring the DBLP community:
1. investigate author profiles by analysing their publication records;
2. identify the most prolific authors on a given topic;
3. perform social network analyses over the whole community;
4. perform shortest-paths over DBLP (e.g., the shortest-path between authors, the analysis of co-author networks, etc.) 

## GraphDBLP Stats
To date, GraphDBLP contains 5+ million nodes and 24+ million relationships, enabling users to explore the DBLP data by referencing more than 3.3 million publications, 1.7 million authors, and more than 5 thousand publication venues. Through the use of word-embedding, more than 7.5 thousand keywords and related similarity values were collected

## GraphDBLP Data Model

![Image of GraphDBLP Data Model](https://github.com/fabiomercorio/GraphDBLP/blob/master/images/graphdblp_data_model_logo.jpg)

# Quick Start
You can install GraphDBLP in 5 steps as follows.

## Step1: Download Neo4j
First, download [Neo4j graph-database](https://neo4j.com/download/). Notice that GraphDBLP has been tested on Neo4j Community Edition 3.2.5. We suggest to download Neo4j Desktop and then to deploy a new GraphDB instance using the Neo4j Community Edition 3.2.5.
## Step2: Download GraphDBLP database dump 
Download the [dump file](https://goo.gl/Cy1AH1) that contains the whole GraphDBLP database in a local folder (e.g., Download). The procedures that transform DBLP into a graph-database are time consuming and discussed in [the paper](https://link.springer.com/article/10.1007/s11042-017-5503-2). Here, for your convencience, we recommend to import the GraphDBLP database instance into your local Graph-database instance as follows.
## Step3: Build the Graph instance
Open the Neo4j Desktop app. Here press "Manage" and then "Terminal". Move to bin directory with `cd bin` then type `./neo4j-admin load --from=path_to_your_donwload_folder/graph.db.dump --force`. This operation may take a while. Please do not close the window while running.
## Step4: Tune GraphDBLP settings to improve performances [optional]
As some GraphDBLP queries are time and memory consuming, we suggest to increase the memory available to Neo4j. This can be easily done through Neo4j Desktop App-->Manage-->Settings. Here just modify the rows `dbms.memory.heap.initial_size=512m` and `dbms.memory.heap.max_size=1G` with the desired settings. The higher, the better. Remember to restart the sever in case of changes.
## Step5: Run GraphDBLP server
Just press the Start button to run GraphDB instance through the Neo4j Desktop app. Notice that the first run may take a while.

# Usage through Python Shell 
GraphDBLP provides a shell-interface with 4 pre-defined queries, as specified in the paper. This would make easier the realisation of some standard queries over DBLP. Clearly, we assume you have a Python > 2.x shell installed on your machine.
## Requested Packages
The following Python packages are required to run `GraphDBLP.py`:
- matplotlib, py2neo, pandas, tabulate, statistics. You can easily install all these packages with `pip` typing  `pip install matplotlib  py2neo pandas tabulate statistics` from the shell.

## Running `GraphDBLP.py`
Open a terminal and go to the GraphDBLP folder you downloaded (or cloned). Then type `python ./GraphDBLP.py ` and select one of the following arguments:
### Keywords Discovery
![Q1: Keywords Discovery](https://github.com/fabiomercorio/GraphDBLP/blob/master/images/graphdblp_q1.jpeg)
Use `-q1 keyword limit` to the query number 1 for **KEYWORDS DISCOVERY**. This allows users to identify the most prolific authors in the DBLP community for a given keyword. This requires to specify also the keyword to be used and the limit value for results. Example: `-q1 'multimedia' 10` will perform query 1 using multimedia as keyword and collecting top 10 results. The meaning of 'relevance', 'score' and 'prolificness' are discussed in the paper. A list of current keywords stored in GraphDBLP (inheridted from FacetedDBLP project!) can be found [here](https://github.com/fabiomercorio/GraphDBLP/blob/master/keywords.csv)
### Author Publication Records Comparison
![Q2: Author Publication Records Comparison](https://github.com/fabiomercorio/GraphDBLP/blob/master/images/graphdblp_q2.jpeg)
Use `-q2 author-name-surname limit similarity-threshold` to run query number 2 for **AUTHOR PUBLICATION RECORDS COMPARISON**. This query starts from the keywords describing an author’s research activities i.e., the keywords connected through the `has_research_topic` relationship. For each keyword, the most proficient author in the field is identified, and the related data are retrieved: (prolific) author name, score, relevance, and related keywords. This requires to specify also the keyword to be used, the max number of researchers to be considered for each keyword and the similarity threshold value for similar keywords. Example: `-q2 'John von Neumann' 3 0.4` will perform query #2 profiling the publication record of John von Neumann and retrieving up to 3 top researchers for each keyword appearing the in profile of John von Neumann. In addition, for each keyword, only keywords with a similarity value grater than 0.4 will be returned
### Local Clustering Coefficient (SNA)
![Q3: Author Publication Records Comparison](https://github.com/fabiomercorio/GraphDBLP/blob/master/images/graphdblp_q3.jpeg)
Use `-q3 venue-name similarity-threshold` to rum query #3 for **COMPUTING LOCAL CLUSTERING COEFFICIENT ON RESEARCH COMMUNITIES**. This requires to specify the venue name and a threshold value for computing the similarity. Example: `-q3 'ijcai' 10` percent will perform query 3 computing the community starting from ijcai and considering venue with a similarity value with at least 10 percent.
### Shortest Paths
Use `-q4 author1-name-surname author2-name-surname rel-to-be-navigated limit` to execute query #4 for **SHORTEST PATHS BETWEEN RESEARCHERS**. This requires to specify the name of two researchers to be connected, the relationships that can be navigated separated by a pipe `|` and the max number of paths to be returned. Example: `-q4 'John von Neumann' 'Moshe Y. Vardi' 'authored|contains' 1`. We suggest to run this query directly on the Neo4j Browser (available on your local machine at [http://localhost:7474/browser/](http://localhost:7474/browser/)) as this would allow you obtaining a graphical representation of the returned paths, as shown in the figure below. The Cypher code to compute shortest paths might have the following structure: `match p=AllshortestPaths((n:author)-[:authored|contains*]-(n2:author)) where lower(n.name) = lower('fistname lastname author 1') and lower(n2.name) = lower('fistname lastname author 2') return p limit 1`. Notice that, in the example below only relations  labelled as `contains` or `authored` are allowed to be navigated. This results in a path with size 4 whilst a shortest one might be found by enabling the navigation of the relation `has_research_topic`.   

![Q2: Author Publication Records Comparison](https://github.com/fabiomercorio/GraphDBLP/blob/master/images/graphdblp_q4.jpeg)

# Usage through Neo4j Shell

**GraphDBLP** is built on top of Neo4j. This means you can perform any query using the [Cypher query language](https://neo4j.com/developer/cypher-query-language/). Once the Neo4j instance is running, open your browser at [localhost:7474/browser/](localhost:7474/browser/ ) 

# Paper on GraphDBLP

Please cite GraphDBLP as: Mezzanzanica, M., Mercorio, F., Cesarini, M., Moscato, V., Picariello, GraphDBLP: a system for analysing networks of computer scientists through graph databases. Multimed Tools Appl (2018). https://doi.org/10.1007/s11042-017-5503-2

```
@Article{Graphdblp2018,
author="Mezzanzanica, Mario
and Mercorio, Fabio
and Cesarini, Mirko
and Moscato, Vincenzo
and Picariello, Antonio",
title="GraphDBLP: a system for analysing networks of computer scientists through graph databases",
journal="Multimedia Tools and Applications",
year="2018",
issn="1573-7721",
doi="10.1007/s11042-017-5503-2",
url="https://doi.org/10.1007/s11042-017-5503-2"
}
```



# Disclaimer and Credits

GraphDBLP is an experimental tool developed as a proof of concepts to empirically verify how a graph-based analysis can be performed over the well known DBLP computer science bibliography.  
This means there could be bugs, or queries that need for better optimisation, refinement or improvement. The aim behind this project is to show that computer science bibliography can be queried as a graph. If you aim at joining this project please contact us!

**GraphDBLP** makes use of:
1. DBLP updated at December 2016;
1. Neo4j as graph-database for querying the knowledge base;
2. The keywords here included have been identified by the [FacetedDBLP](http://dblp.l3s.de/dblp++.php) project.

A special thank to Thanks to [Andrea Scrivanti](https://github.com/andreascrivanti) and [Ettore Colombo](https://github.com/hrecol) for thri crucial contribution on this project.

