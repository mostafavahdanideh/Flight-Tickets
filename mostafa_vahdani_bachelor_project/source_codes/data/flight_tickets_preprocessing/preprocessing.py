
from matplotlib import pyplot as plt
from common_utils.utils import extract_value_from_json_obj


def correct_field(main_col_field, secondary_col_field):
    if main_col_field != secondary_col_field:
        return secondary_col_field
    return main_col_field


def semi_space_correction(x, normalizer):
    return normalizer.normalize(x)


def update_city_persian_name_fields(data, x_col_name, y_col_name, city_codes_dict):
    national_code = data[x_col_name]
    city_name_persian_col_field = data[y_col_name]
    city_name_persian_dict_value = city_codes_dict[national_code]

    return correct_field(city_name_persian_col_field, city_name_persian_dict_value)


def update_departure_date_YMD_format_fields(data, x_col_name, y_col_name, months_dict):
    _, day_of_month, month = data[x_col_name].split()
    month_number_str = months_dict[month]
    created_departure_date_YMD_formats = f"1402/{month_number_str}/{day_of_month}"
    departure_date_YMD_formats_col_field = data[y_col_name]

    return correct_field(departure_date_YMD_formats_col_field, created_departure_date_YMD_formats)


def difference_drop(df, *args):
    """difference drop with column names that you will give on *args"""
    return df.drop(columns=df.columns.difference([*args]), axis=1)


def update_dependent_col(main_df, func, x_col_name, y_col_name, your_dict):
    secondary_df = difference_drop(main_df, x_col_name, y_col_name)
    # secondary_df = main_df[main_df.columns.intersection([x_col_name, y_col_name])]

    main_df[y_col_name] = secondary_df.apply(
        func=func,
        args=(x_col_name, y_col_name, your_dict),
        axis=1)

    return main_df


def change_city_names_to_en(x_field, airports_info_dict):
    return extract_value_from_json_obj(airports_info_dict, [x_field, "city_name"])


def get_city_airport_names(x_field, airports_info_dict):
    return extract_value_from_json_obj(airports_info_dict, [x_field, "airport_names"])[-1]


def move_columns(main_df, cols_dict):
    sorted_cols_dict = dict(sorted(cols_dict.items(), key=lambda item: item[1]))

    for col_name, next_position in sorted_cols_dict.items():
        column_to_move = main_df.pop(col_name)
        main_df.insert(next_position, col_name, column_to_move)
    return main_df


def replace_with(col_df, origin_value, replacement_value, type_value=None):
    col_df = col_df.replace(origin_value, replacement_value)

    if type_value:
        col_df = col_df.astype(float)
    
    return col_df


def check_col_distribution(col_df):
    col_df.hist()
    plt.show()
