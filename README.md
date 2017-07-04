<<<<<<< HEAD
### Requirements:
=======
###Requirements:
>>>>>>> da9232b0121a860a844fa522b32d62842a5b9bda

Tested with Python 2.7.13

The following packages are required
* numpy
* os
* re
* sys
* time
* random
* colorama
* datetime
* pandas
* beautifulsoup4
* selenium
* lxml

<<<<<<< HEAD
### Approach:
=======
###Approach:
>>>>>>> da9232b0121a860a844fa522b32d62842a5b9bda

In order to get a list of companies we can putgether a url with the base url https://angel.co/companies? 
plus a number of filters a a string.

An example with stage, signal, markets and location filter looks like the following:

https://angel.co/companies?stage=Seed&signal\[min]=2.1&signal\[max]=5.7&markets[]=Consumer+Internet&locations[]=2071-New+York

At the time of writing, Angle.co limits number companies per query to be 400, 
therefor we can use many filters with specific conditions to create unique searches and 
hit more non-duplicate companies. For a given page, if the number of companies is more than 400, we would also
click several sorting button to get make more companies accessible.

The scraper is configured to have long waiting period per query so it scrapes slowly
 to avoid overloading the server.
 
Most of the source code is in [AngelScraper.py](code/AngelScraper.py) with most functionalities implemented
in class AngelScraper

### Run instructions

```python code/main.py``` to execute the scraper, a number of folders will be created

```python code/get_results.py``` to collect the results into one csv file at output/results_so_far_$datatime$.csv
