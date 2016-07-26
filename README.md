# collabworks
Build collaboration networks beetwen scientist based on the references of WoS/Scopus databases. 

## Requisites
The script is developed in Python 3.

The following Python packages are needed:
* Pandas
* NetworkX
* Numpy
* Unidecode

## Usage

** Obtain the data **
First of all download all the data you want to visualize. 
*** Web of Science ***
Make a search of the articles from which you desire to study its publications structure.
Obtain afterwards the data selecting *Save to Tab-delimited (Windows, UTF-8)* and gathering the desired number of articles. No abstract is needed.
Download the bunch of files keeping in mind that WoS allows at most 500 articles for each txt file.
Place finally all the txt files into the 'data' folder contained in the execution directory.

*** Scopus ***
Proceed in the same way as for the Web of Science. No abstract is needed.
Place finally all the csv files into the 'data' folder contained in the execution directory.

** Arguments and execution **
Run the program using Python 3.

	python3 collabworks.py *args

Depending on your environment the arguments may be,

* -w: All data is downloaded from WoS (default)
* -s: All data is downloaded from Scopus

The size of the nodes will be proportional to,

* -a: The number of articles per author
* -c: The number of citacions per author (default)

In order to drop non relevant authors a 'publication_threshold' has been defined, which may be understood as the number of publications
that some author must have so as to appear in the network. If some author has a number of articles lower than the one defined by the threshold, it will be automatically
dropped from the database. Thus,

* publication_threshold (integer): Integer defining the publication_threshold (default: 1)

** Results **
The script export an GraphML file which can be visualized using [Gephi](https://gephi.org/).

** Example **
One example is presented for completeness. Supose we one to charcaterize the collaboration of structure of the first scientist doing research on the field of Quantum mechanics. More concretely, we wish to know which were the collaboration communities which were talking about *quantum*s. What we did is search fopr the topic *quantum* in the Web of Science. We downloaded the 840 articles which appeared as search results. Placing them in the */data* folder and executing the program with the following arguments,

* python3 collabworks.py -c -w 5

Which means that the size of nodes will account for the number of citations per author (**-c**), that only WoS results are placed in the data folder and our the publication threshold is set to 5, meaning that only scientists with 5 or more articles will appear in the graph. Pressing *enter* the program automatically generated a file called *Graph [WoS - Threshold 5 - # Citations].graphml*, which can be opened in Gephi. With some basic knwoledge of this visualization tool, our graph will look like,



