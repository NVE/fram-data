# Metadata
Metadata in the FRAM-data package and database is used either for helping users or to describe how time vectors behave within the FRAM-core system. This section is aimed at explaining the metadata one can find within the system.

## Attribute Metadata
In each exel file containing attributes of components, there is a "Metadata" sheet displaying a table. The columns of this table can be arranged into two types according to their purpose. 

**User metadata:** Optional information meant to help the user interact with the attribute table in the Data sheet.

- Reference - If there are references to IDs of for example time vectors located in other files one can write the name of the file here.
- Description - Description of the attribute column.
- Dtype - Meant to signify which data types, usually string or float, can be currently founc within the column.

**Constant time vector metadata:** Metadata applied to float values written directly in columns instead if ID references. The system interprets this as a time vector with constant value.

- Attribute - The name of the column in the Attribute table (Data sheet) that the current row of metadata applies to.
- Unit - The unit to use for constant time vectors in this column.
- IsMaxLevel, IsZeroOneProfile, RefPeriodStartYear and RefPeriodNumberOfYears - Describing the constant time vector's level/profile status along with its reference period if it has one. Read more under [Time Vector Metadata](#time-vector-metadata)


## Time Vector Metadata
Metadata in files containing time vectors can be thougth of as a dictionary. Some of the fields/keys defined and used by FRAM are required. Asence of these will result in getting Exceptions when the file is read by an [NVETimeVectorLoader](reference.md/#framdata.loaders.NVETimeVectorLoader). Following is a list of the required and optional metadata fields for timevectors.

**Required fields:**

- IsMaxLevel (bool|None) - Must be defined as True or False (None for profiles) for timevectors representing levels. A level is either the maximum of a time series in a given period or an average over a reference period.
- IsZeroOneProfile (bool|None) - Must be defined as True or False for profiles. A profile represents either a percentage of a max level or deviation from the level average with reference period in a given time step (called a mean one profile, since the average over the reference period is 1).
- Is52WeekYears (bool) - True if the time vector contains yearly data standardized with 52 weeks.
- ExtrapolateFirstPoint (bool) - Apply extrapolation to first point backwards in time if True.
- ExtrapolateLastPoint (bool) - Apply extrapolation to last point forwards in time if True.
- RefPeriodStartYear (int|None) - Start year of a reference period used to calculate average levels and mean one profiles. Must be defined as an integer if either IsMaxLevel or IsZeroOneProfile is False.
- RefPeriodNumberOfYears (int|None) - Number of years the reference period spans. Must be defined as integer if RefPeriodStartYear is defined.
- TimeZone (tzinfo|None) - Must be defined but can be None. This is to enforce a concious choice.
- Unit (str|None) - Must be defined but can be None.

**Optional fields:**

- ID (str|None) - Only relevant for timevectors stored in excel in the horizontal format. Can be used to denote the name of the column containing vector IDs. If not defined or None, the column name "ID" is assumed.
- StartDateTime (datetime|None) - Start datetime in the index of the timevector.
- Frequency (timedelta|None) - The fixed frequency between datetimes the index. If defined it must be fixed, in other words the timedelta between a given point and its succeeding point must be the same for all points. 
- NumberOfPoints (int|None) - Total number of points/length of the vector and its index.

StartDateTime, Frequency and NumberOfPoints can be used as an optimization to represent the index more compactly. The system will find be able to find these values regardless by reading/calculating them if they are not defined in the metadata, but defining them here may improve performance when reading the data and setting up the Model.