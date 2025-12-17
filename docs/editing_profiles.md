# Editing Profiles
Profiles and other large time series (or time vectors) data with fine resolution are stored in HDF5/h5 files in the FRAM dataset to utilize the formats high reading performance. These are less straigth forward to open and change than the attribute files which are currently excel files. This section is therefore meant as a guide on how to create and edit HDF5 profiles in FRAM.

## File Structure
The first thing to know about the HDF5 format is that these files are structured in a system of so called groups and datasets. One can think of these as comparable to a hierarchichal file system of, respectively, folders and files. Groups reference other groups or datasets, while datasets contain the actual data. **Tip for vscode users:** the [H5Web](https://marketplace.visualstudio.com/items?itemName=h5web.vscode-h5web) extension lets you open and view h5 files in a GUI in the vscode app.

In the FRAM dataset, h5 files containing time vectors utilize groups and dataset in a specific way. There are mainly four different types of groups/datasets encountered at the first hierarchical level of the time vector files:

- index (Group): Used to define indexes for vectors where each index is supposed to only apply to a particular vector.
- common_index (Dataset): Contains one numpy array. This is a fallback index for vectors which have not defined their own index in the index group. Can also be used on purpose if many or all vectors have the same index.
- metadata (Group): Used to connect a specific set of metadata to a particular vector. This group can contain multiple groups which themselves contain datasets representing metadata fields.
- common_metadata (Group): Contains one set of metadata fields (stored as datasets) for all vectors without their own special metadata. Used in a similar way as common_index.
- vectors (Group): Contains datasets of numpy arrays with vector values connected to a unique ID. The same ID is used to connect the vector to a specific index or metadata.

## Editing h5 using FRAM-data API
Within the FRAM system's data package is the [NVEH5TimeVectorEditor](reference.md/#framdata.file_editors.NVEH5TimeVectorEditor), offering methods for reading and editing h5 files.

```py
from framdata.file_editors import NVEH5TimeVectorEditor

# Read a h5 file into memory. To create a new file from scratch one can set source=None.
file_editor = NVEH5TimeVectorEditor(source="path/to/file.h5")

# You can for example scale your vector.
vector_1 = file_editor.get_vector("v1")
file_editor.set_vector("v1", vector_1*0.8)

# Set unit field in common metadata.
file_editor.set_common_metadata_by_key("Unit", "EUR/MWh")

# You can save to a new h5 file or overwrite the existing one.
file_editor.save_to_h5("path/to/file_2.h5")

```

You can in principle set vectors as whatever numpy arrays you wish, ***but you should make sure they are the same length as their index***, whether that is the common_index or a specific one. Otherwise the system will fail later when reading the file. 


Another method of editing the h5 files is to use the [h5py](https://docs.h5py.org/en/) package instead of the aforementioned API. You will in that case have to make extra care your files follow the defined [file structure](#file-structure). Keep in mind that FRAM stores the index arrays and metadata in h5 files as type bytes (dtype of elements are bytes in case of index arrays) to avoid incompatible types with the h5 format. It is recommended that users follow this either by using the [FRAM-data API](#editing-h5-using-fram-data-api) or by explicitly converting types before saving with [h5py](https://docs.h5py.org/en/). When loaded by FRAM, index arrays are cast as datetime objects and metadata keys as strings. Metadata values types can be read more about in [Metadata](./metadata.md#time-vector-metadata).


## Parquet files
FRAM also supports time vectors in parquet files. The formatting here is a little different. It is stored as a table with one column called "DatetimeIndex" which represents the index, and every other column representing a time vector. This means all vectors must have the same index within one file. Another restriction is that metadata must be the same for all vectors.

[NVEParquetTimeVectorEditor](reference.md/#framdata.file_editors.NVEParquetTimeVectorEditor) can be used to create and edit parquet time vectors. Alternatively the [pyarrow](https://arrow.apache.org/docs/python/) and [pandas](https://pandas.pydata.org/docs/user_guide/) python packages can be used to read parquet files. Keep in mind that to edit metadata, pyarrow must be used to access the tables binary metadata:

```py
import pyarrow.parquet as pq
import pandas as pd
from framdata.database_names.TimeVectorMetadataNames import TimeVectorMetadataNames as TvMn

# accessing metadata
metadata = pq.ParquetFile("path/to/file.parquet").schema_arrow.metadata

# saving with metadata
table_df = pd.read_parquet("path/to/file.parquet")

table = pa.Table.from_pandas(table_df)

# add metadata to table schema, and ensure same encoding as FRAM uses.
schema_with_meta = table.schema.with_metadata({str(k).encode(TvMn.ENCODING): str(v).encode(TvMn.ENCODING) for k, v in metadata.items()})
table = pa.Table.from_pandas(table_df, schema=schema_with_meta)

pq.write_table(table, "path/to/file.parquet")
```

