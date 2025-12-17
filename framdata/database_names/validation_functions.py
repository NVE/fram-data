"""Module containing registered custom check functions used by Pandera schema classes."""

from typing import Any

import pandas as pd
from pandera import extensions
from pandera.typing import Series

from framdata.database_names._attribute_metadata_names import _AttributeMetadataNames


@extensions.register_check_method()
def dtype_str_int_float(series: Series[Any]) -> Series[bool]:
    """
    Check if the series contains only str, int or float values.

    Args:
        series (Series[Any]): Series to check.

    Returns:
        Series[bool]: Series of boolean values detonating if each element has passed the check.

    """
    return series.apply(lambda value: isinstance(value, str | int | float))


@extensions.register_check_method()
def dtype_str_int_float_none(series: Series[Any]) -> Series[bool]:
    """
    Check if the series contains only str, int, float or None values.

    Args:
        series (Series[Any]): Series to check.

    Returns:
        Series[bool]: Series of boolean values detonating if each element has passed the check.

    """
    return series.apply(lambda value: isinstance(value, str | int | float | type(None)))


@extensions.register_check_method()
def numeric_values_greater_than_or_equal_to(series: Series[Any], min_value: int | float) -> Series[bool]:
    """
    Check if values are greater than or equal to min_value if they are of type int or float.

    Args:
        series (Series[Any]): Series to check.
        min_value (int | float): Value that the elements in the series should be greater than or equal.

    Returns:
        Series[bool]: Series of boolean values detonating if each element has passed the check.

    """
    if not isinstance(min_value, (int | float)):
        message = "min_value must be of type int or float."
        raise ValueError(message)
    return series.apply(lambda x: x >= min_value if isinstance(x, (int | float)) else True)


@extensions.register_check_method()
def numeric_values_greater_than(series: Series[Any], min_value: int | float) -> Series[bool]:
    """
    Check if values are greater than or equal to min_value if they are of type int or float.

    Args:
        series (Series[Any]): Series to check.
        min_value (int | float): Value that the elements in the series should be greater than or equal.

    Returns:
        Series[bool]: Series of boolean values detonating if each element has passed the check.

    """
    if not isinstance(min_value, (int | float)):
        message = "min_value must be of type int or float."
        raise ValueError(message)
    return series.apply(lambda x: x > min_value if isinstance(x, (int | float)) else True)


@extensions.register_check_method()
def numeric_values_less_than_or_equal_to(series: Series[Any], max_value: int | float) -> Series[bool]:
    """
    Check if values are less than or equal to max_value if they are of type int or float.

    Args:
        series (Series[Any]): Series to check.
        max_value (int | float): Value that the elements in the series should be greater than or equal.

    Returns:
        Series[bool]: Series of boolean values detonating if each element has passed the check.

    """
    if not isinstance(max_value, (int | float)):
        message = "max_value must be of type int or float."
        raise ValueError(message)
    return series.apply(lambda x: x <= max_value if isinstance(x, (int | float)) else True)


@extensions.register_check_method()
def numeric_values_are_between_or_equal_to(
    series: Series[Any],
    min_value: int | float,
    max_value: int | float,
) -> Series[bool]:
    """
    Check if values are between or equal to a min and max value if they are of type int or float.

    Args:
        series (Series[Any]): Series to check.
        min_value (int | float): Value that the elements in the series should be greater than or equal.
        max_value (int | float): Value that the elements in the series should be less than or equal.

    Returns:
        Series[bool]: Series of boolean values detonating if each element has passed the check.

    """
    if not isinstance(min_value, (int | float)) and not isinstance(max_value, (int | float)):
        message = "min and max value must be of type int or float."
        raise ValueError(message)
    return series.apply(lambda x: min_value <= x <= max_value if isinstance(x, (int | float)) else True)


@extensions.register_check_method()
def check_unit_is_str_for_attributes(df: pd.DataFrame, attribute_names: list[str]) -> Series[bool]:
    """
    Check if 'Unit' column values are strings for the rows where the 'Attribute' column matches specific attributes.

    This function checks whether the values in the 'Unit' column are strings for rows where the 'Attribute' column
    matches any of the specified attribute names. Rows that do not match the specified attributes are considered valid
    by default. This function is commonly used by subclasses of 'AttributeMetadataSchema' to validate that a unit is
    given for certain attributes in the metadata belonging to a Component.

    Args:
        df (pd.DataFrame): The DataFrame containing the columns to validate.
        attribute_names (list[str]): A list with the names of the attributes to check in the 'Attribute' column.

    Returns:
        Series[bool]: A boolean Series indicating whether each row passes the validation. Rows where the 'Attribute'
        column does not match the specified attribute are automatically marked as valid.

    Example:
        Given the following DataFrame:

        | attribute   | unit       |
        |-------------|------------|
        | Volume      | MWh        |
        | Temperature | None       |
        | Capacity    | None       |

        And `attribute_names = ["Volume", "Capacity"]`, the method will validate that the 'Unit' column contains strings
        for rows where 'attribute' is "Volume" and "Capacity". The resulting Series will be:

        | validation_result |
        |-------------------|
        | True              |
        | True              |
        | False             |

    """
    is_attribute_rows = df[_AttributeMetadataNames.attribute].isin(attribute_names)
    unit_is_str = df[_AttributeMetadataNames.unit].apply(lambda x: isinstance(x, str))
    return ~is_attribute_rows | unit_is_str


"""
Standard descriptions for validation checks that are commonly used in Pandera DataFrameModel schemas.

The dictionary must adhere to the following structure:
    - Key (str): The name of the validation check method. The name must be unique and match the name of a check method.
    - Values (tuple[str, bool]):
        - The first element (str) provides a concise and user-friendly description of the check. E.g. what
            caused the validation error or what is required for the check to pass.
        - The second element (bool) indicates whether the check is a warning (True) or an error (False).

"""
STANDARD_CHECK_DESCRIPTION = {
    # Built-in pandera checks
    "dtype('str')": ("Value must be of type str.", False),
    "dtype('int')": ("Value must be of type int.", False),
    "dtype('float')": ("Value must be of type float.", False),
    "dtype('bool')": ("Value must be of type bool.", False),
    "not_nullable": ("Missing values are not allowed.", False),
    "field_uniqueness": ("Column values must be unique. Found duplicates.", False),
    # Custom checks that are commonly used. NB! Function names in the Schema classes in database_names (not the generic ones defined in this module) must match
    # keys in this dictionary for descriptions to show up.
    dtype_str_int_float.__name__: ("Value must be of type str, int or float.", False),
    dtype_str_int_float_none.__name__: ("Value must be of type str, int, float or None.", False),
    check_unit_is_str_for_attributes.__name__: ("Value must be of type str. Unit is required.", False),
    numeric_values_greater_than_or_equal_to.__name__ + "_0": ("Value should be greater than or equal to 0.", True),
    numeric_values_greater_than.__name__ + "_0": ("Value should be greater than 0.", True),
    numeric_values_less_than_or_equal_to.__name__ + "_0": ("Value should be less than or equal to 0.", True),
    numeric_values_are_between_or_equal_to.__name__ + "_0_and_1": ("Value should be between 0 and 1 or equal to 0 or 1.", True),
}
