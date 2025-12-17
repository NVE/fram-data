# Data Validation
This section explains how the framdata package performs validations of the dataset which is read by the system. For validation of the attribute tables we use the pandera Python package (https://pandera.readthedocs.io/en/stable/). Validation of time vector data is implemented in the NVETimeVectorLoader class and is optionally performed once while reading all data in a file.


### Attribute Tables Validation
In the database_names folder in each {object name}Names file (concerned With creating objects from attribute tables) there is defined the {object name}Schema and an {object name}MetadataSchema classes. See for example the DemandNames module. These classes are responsible for table validation according to panderas DataFrame Models (https://pandera.readthedocs.io/en/stable/dataframe_models.html).

With these Schemas one can use built in pandera checks or define your own if what you need is not covered.

- To use built in checks, define a column with the pandera Field function under the table Schema. Available checks can be passed as arguments to the function. See for example:

- For specialized checks, a class method must be defined in the Schema class. This method takes either a single column (as a Series) or the Whole dataframe as arguments. The specialized validation is then implemented here. Return value should be a Series of bools representing values which have failed or passed. NB! If the input is a Series the names of the columns to check with this method must be listed in the pandera check decorator. If input is a DataFrame, the pandera dataframe_check decorator is used instead.

Error message description and formatting:

- The validation_functions.py module in database_names contains commonly used checks for attribute tables and their metadata. Here one can also add user friendly descriptions of why a check fails using the STANDARD_CHECK_DESCRIPTION global variable. Keep in mind that it is the names of the validation methods defined in the schemas which must be defined here for the descriptions to show up during runtime. An alternative is to add descriptions in to the return dictionary of {Object ame}Names._get_unique_check_descriptions. This is meant for unique checks only defined and used by a single Schema.

- Validation methods which take a DataFrame as input need special formatting. Its purpose is to increase readability by converting the error dataframe from one message per error per column checked into one message per row where errors occured. This is performed by the {object name}Names._format_unique_checks method. As the columns are unique to each table, this method is necessarily specialized to the particular validation method. Therefore if a unique check of this sort is implemented, the formatting should be implemented along with it.


### Time Vector Validation
In the NVETimeVectorLoader class there is defined a method _validate_vector in which is implemented all checks to perform on every time vector in the Loader. This method takes as argument the ID of a vector defined in the Loader. From this ID, the vector values and index is retrieved and validated. New checks can be added here.

