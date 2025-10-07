import re

import pandas as pd
import pytest
from pandera.errors import SchemaError

from framdata.database_names._attribute_metadata_names import _AttributeMetadataSchema as AmnSchema


def test_attribute_meta_data_schema() -> None:
    valid_data = pd.DataFrame(
        [
            ["ConsumerID", None, None, None, "Unique consumer ID.", None, None, None, None],
            ["Capacity", "float", "Demand.Consumers.capacity", "MW", None, True, None, None, None],
        ],
        columns=[
            "Attribute",
            "Dtype",
            "Reference",
            "Unit",
            "Description",
            "IsMaxLevel",
            "IsZeroOneProfile",
            "RefPeriodStartYear",
            "RefPeriodNumberOfYears",
        ],
    )
    AmnSchema.validate(valid_data)


def test_attribute_meta_data_schema_unique_column_names() -> None:
    valid_data = pd.DataFrame(
        [
            ["ConsumerID", None, None, "Unique consumer ID.", None],
            ["Capacity", "Demand.Consumers.capacity", "MW", None, None],
        ],
        columns=["attribute", "reference", "unit", "description", "unit"],
    )
    with pytest.raises(SchemaError, match=re.escape("dataframe contains multiple columns with label(s): ['unit']")):
        AmnSchema.validate(valid_data)
