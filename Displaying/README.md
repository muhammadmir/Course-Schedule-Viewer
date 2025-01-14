# Introduction
Some schools utilize the services of Ellucian Company to allow students to do several Registrar-related things, including viewing and searching for courses. The software these schools are using is *probably* called [Ellucian Banner](https://www.ellucian.com/solutions/ellucian-banner), which has several functionalities. The functionality this project is concerned about is the interface utilized to display Course information like name, description, subject, etc.

The purpose of this part of the project is to provide an intuitive way to filter and search for Course information that is obtained from the [first](../Parsing/) part of the project. I used the DataTables library as it provided a relatively easy way of intuitively implementing the necessary functionality. *Please note that this project was tested on 3 different schools.*

The complete project has two parts:
1. [Parsing](../Parsing/) - The scraping and parsing of the Courses from Ellucian Banner API
2. [Displaying](../Displaying/) - Using DataTables to display results from Parsing

This project is licensed under the MIT license.

## Definitions
- **Calendar**: a term or semester where a set of Courses are offered
- **Course**: a college class offered during a particular Calendar (and its corresponding properties)

To view the interface live, please download everything in this this folder (Displaying) and open the main.html file.

# Overview and Functionality
This part of the project is not hosted on a server and hence requires the user to upload the output JSON file from the first part of the project. I made the choice of using the Bootstrap framework to build the frontend, along with DataTables for displaying the main table. Below, I will describe the functionality of the website.

## Course Loading
The JSON file must be a JSON-serialized output from the `get_courses` method of a `Parser` object from [Parser.py](../Parsing/Parser.py), which is a an array of Calendars. Since I allowed the support of uploading (and later, filtering) of multiple Calendars, the data from the JSON file is "de-normalized" so that the `Calendar Name` property of each Calendar becomes a property for each of its corresponding Courses. This is to just make implementing DataTables functionality easier. After the JSON file is loaded correctly, the Course View Panel appears.

## Course View Panel
The Course View Panel has 3 main features: Buttons, Search Panes, and Table. I will describe each more below.

### Buttons
There are two buttons at the top. The "Inter-Pane Logic" button is associated with the logic used across the Search Panes. By default, the logic is OR. Clicking the button will change it to AND, but the page will be refreshed and the user will be required to load the JSON file again. The "Download Filtered Results" button will download all the results that are currently filtered for via the Search Panes and the search feature of the Table.

**Note**: The results will be downloaded to file called `Filtered.json` and will be in the "de-normalized" format.

### Search Panes
There are 12 Search Panes that I have chosen to be displayed. By selecting an Option in one Pane, all other unavailable (or rather, impossible) corresponding Options across all other Panes. This is known as "cascading" and intra-Pane cascading (cascading of Options within a Pane) is *not* supported. Note that each Option (as Panes are cascaded) displays the number of available Courses meeting that criteria. Additionally, each Pane can be searched, filtered, and sorted as well.

Selecting multiple options within a Search Pane or across multiple is possible (refer to hint at the top of the page). The logic utilized when selecting across multiple Panes is the "Inter-Pane Logic," which is controlled by the button at the top of page.

**Note**: All the Search Panes can be collapsed, expanded, or cleared using the buttons at the right of the page.

### Table
By default, 10 Courses are displayed per page. The user can change pages at the bottom-left of the table as well as changing number of Courses per page at the top left of the table. The columns of the table allow allow sorting as well. For each Course, a drop-down on the left can be clicked to reveal additional information about the Course. Any information about a Course (from name and credits to description and requirements) can be searched for using the search bar located at the top right of the table.

# Usage
To use the project, the user should open up [index.html](./index.html) and load the JSON file. *It may some time for things to load, especially for a large number of Courses.*
