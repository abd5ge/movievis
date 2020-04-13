# Introduction

Movie Vis is a analytical approach to study hidden biases in film through the application of Power/Agency scoring, Bechdel Scoring and Character Network Mapping. Movie Vis studies these scoring methods through a gender and race lens.

Research on racial and gender bias in literature is impeded by limitations in acquiring traditional human ratings. Our project provides an analytic and visual aid to overcome these limitations and aid interdisciplinary research. Drawing from a collection of previously validated text analytics, and using large databases of film data, we will create an application that displays various metrics of racial and gender bias as they appear within the spoken lines of narrative characters within films. Recently, big data and NLP approaches have shown promise in aiding research on this topic, specifically by scraping films and book narratives from online sources.

# Files

The Movie Vis project is separated into four main components: data collecting, data processing, data analysis, and data visualization.

 - Data Processing: 
Data is collected through several sources. First, we scrape the movie script from The Internet Movie Script Database (IMSDb). Next we search for this script's metadata through the The Movie Database (TMDb) API. From TMDb we collect information such as the celebrities casted in the movie, the profile picture of each celebrity, the character that each celebrity played, the celebrities' gender, the year the movie was released, box office revenue, and so on. There are several celebrities in the TMDb database that are missing gender information, and the TMDb database does not collect race or ethnicity. To collect this we use modified version of the [deepface](https://github.com/serengil/deepface)  framework to predict the gender and race of the celebrity. After this step we then map the celebrity metadata to the characters parsed from the script pulled via IMSDb. Through this we are able to assume the gender and race of the characters played in a film as well as other crucial information. 
After we've collected the film metadata we begin to analyze and parse the film script itself. We extract important identifiers such as the characters, dialogue, and scene description. We then map the the characters found in the script to the celeb metadata collected via TMDb through a fuzzy match approach using pylcs (or py_common_subseq if the user is on MacOS).
Of course, this is not a perfect approach. For example, if the script being parsed is messy (as many scripts from IMSDb are) then there will be characters who are incorrectly mapped, or dialogue that is not recognized. Generally film writers follow a specific format, where character names follow the same level of indentation throughout the entire script. This also applies for dialogue, and other aspects of the script. Our script parsing and data collection relies on this. We've made every effort to circumvent issues were the script does not follow proper indentation. This can happen if the film script was originally a PDF that was converted to txt and uploaded to the IMSDb. 

- Data Processing: 
From the step above we were able to collect data on over 1200 films. Film scripts in this set that were poorly mapped to celebrity metadata were identified as a bad match. However, we included these films in our visualization to show the pitfalls of text analysis.

The data collected were stored as json objects with TSV counterparts. These TSV files were then inserted into a postgres RDS. Relationships were built based on the TMDb_Id as well as the Celeb_Id, where the Celeb_Id is unique to a celebrity _within_ a film. This [diagram](https://drive.google.com/open?id=17haS84qs4WqAg47oEHj6jlZRZQerQ7MQ) provides an idea of how to structure your dataset if using this project for your own analysis.

- Data Analysis: 
Our analysis were separated into three parts: Bechdel Scoring, Power/Agency Scoring, and Character Graph Mapping.
	1. Bechdel Scoring
	If two or more women in a film are conversing, and the conversation is not about a male then this film generally passes the Bechdel test.
	2. Power/Agency
	Power & Agency is calculated based on the lines spoken in the film. To determine this we employed the NLTK library Natural Language Toolkit ([NLTK](https://www.nltk.org/)).
	3. Character Network Mapping
	Characters are mapped in an undirected graph based on their appearance in certain scenes. As would be expected, weight is calculated as the number of scene occurrences for the source node.

- Visualization
We visualize the data and analysis collected through Tableau. We use Tableau public to publish our data and a frontend Angular.js app to compile our publications on to one site: movievis.com

## Installation

This project has been designed to allow end users to easily collect film data for their own analysis. We've provided the source files of our analysis here. However, installing and running this project will not provide any analyzed results. Running this project will collect data so that the user can implement their own analysis. Feel free to use our text analysis & network mapping as a part of your project, just remember to install the py packages for those scripts.

To use this project, download this repo to a local environment. Once you've downloaded, cd into the project space using a terminal or command line interface. 

    cd movievis/src/python/process_scripts/
    pip install requirements.txt

Please note, if you are using a virtual environment for this project you will need to install opencv-python in your local environment and copy this package from it's site package location over to the virtualenv. 

Also note, this project installs tensorflow and it's dependencies.

## How To Use

First, register for a [developer account](https://developers.themoviedb.org/3) with the TMDb. Save this key as we will use it in our API calls.

To use Movie Vis cd into the project space and run the wrapper py file. The following serves only as an example:

    cd movievis/src/python/process_scripts/
    mkdir output
    python wrapper.py --title <film_title> -o <output_directory> --tmdb_key <tmdb_key>

Example: 

    python wrapper.py --title '10 things i hate about you' -o output --tmdb_key 1234567891010987654321`

For more information use the --help argument to see a list of available options. 

    python wrapper.py --help

The data collected will be written to the folder you used in your -OUTPUT argument.

## Demo

We have created charts and visuals around the data collected for this project. The visualizations can be seen here: http://movievis.com

