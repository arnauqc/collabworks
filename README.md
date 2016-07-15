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
* In Scopus, download it as CSV
* In WoS, download it as 'Tab-delimited (Win, UTF-8)' 

Afterwards, place all the txt/csv files into a 'data' folder contained in the execution directory.

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

