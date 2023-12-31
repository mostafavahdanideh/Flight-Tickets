import pandas as pd
import pytz

from haversine import Unit, haversine
from common_utils.utils import extract_value_from_json_obj
from utils import difference_drop

from jdatetime import datetime, timedelta
from random import randint

from sklearn.impute import KNNImputer


# TODO: we can add stops number of flight for connecting or direct flight.

# TODO: I have to added layover time for direct and connecting flight in estimate_flight_length().


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
    created_departure_date_YMD_formats = f"1402-{month_number_str}-{day_of_month}"
    departure_date_YMD_formats_col_field = data[y_col_name]

    return correct_field(departure_date_YMD_formats_col_field, created_departure_date_YMD_formats)


def update_dependent_col(main_df, func, x_col_name, y_col_name, your_dict):
    secondary_df = difference_drop(main_df, x_col_name, y_col_name)
    # secondary_df = main_df[main_df.columns.intersection([x_col_name, y_col_name])]

    main_df[y_col_name] = secondary_df.apply(
        func=func,
        args=(x_col_name, y_col_name, your_dict),
        axis=1)

    return main_df


def update_flight_number_col(x, airline_codes_dict):
    company_name = x["company_name"]
    flight_number = x["flight_number"]
    airline_code = airline_codes_dict[company_name]
    return f"{airline_code}-{flight_number}"


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
        col_df = col_df.astype(type_value)
    
    return col_df


def orthodromic_distance(row, airports_geometry_dict):
    departure_airport_code = row["national_departure_code"]
    arrival_airport_code = row["national_arrival_code"]

    departure_airport_coordinate = extract_value_from_json_obj(airports_geometry_dict, 
                                                               [departure_airport_code, 
                                                                "geometry"])
    
    arrival_airport_coordinate = extract_value_from_json_obj(airports_geometry_dict,
                                                             [arrival_airport_code, 
                                                              "geometry"])

    return round(haversine(departure_airport_coordinate,
                           arrival_airport_coordinate,
                           Unit.KILOMETERS,
                           normalize=True))


def estimate_flight_length(distance):
    v_km_per_min = randint(885, 965) / 60

    # per minutes
    taxi_time = randint(5, 10)
    attach_stairs_time = randint(5, 10)
    takeoff_clearance = randint(5, 10)
    takeoff_time = randint(10, 20)
    cruise_time = distance / v_km_per_min
    vectoring_time = 10
    busy_airplane_time = 10
    descent_time = randint(10, 15)
    landing_time = randint(10, 20)

    flight_length = descent_time + landing_time + takeoff_time + \
                    taxi_time + attach_stairs_time + takeoff_clearance + \
                    busy_airplane_time + vectoring_time + cruise_time

    return round(flight_length)


def estimate_arrival_time(row):
    arrival_time = row["local_arrival_time"]
    if pd.isnull(arrival_time):
        local_departure_timezone = pytz.timezone('Asia/Tehran')
        departure_time_hour, departure_time_minute = row["local_departure_time"].split(":")
        year, month, day = row["departure_date_YMD_format"].split("-")
        flight_length_hour = row["flight_length_min"] / 60
        hour_part = int(flight_length_hour)
        min_part = (flight_length_hour - hour_part) * 60

        departure_time_obj = datetime(
            year=int(year), month=int(month), day=int(day), hour=int(departure_time_hour),
            minute=int(departure_time_minute), tzinfo=local_departure_timezone)

        estimated_arrival_time = departure_time_obj + timedelta(hours=hour_part, minutes=min_part)
        return datetime.strftime(estimated_arrival_time, '%H:%M')
    return arrival_time


def change_company_name_specific_value(series_value):
    if 1 <= len(series_value) <= 3:
        series_value = series_value.upper()
    elif len(series_value) > 3:
        series_value = series_value.capitalize()
    
    if series_value == "فری برد":
        return "Freebird"
    elif series_value == "ماوی گوک":
        return "MaviGok"
    elif series_value == "G6":
        return "GlobalX"
    elif series_value == "CPN":
        return "Caspian"
    elif series_value == "IZG":
        return "Zagros"
    elif series_value == "3F":
        return "FlyOne"
    elif series_value == "VRH":
        return "Varesh"
    
    return series_value


def change_flight_class_type_specific_value(x):
    if "ایرباس" in x:
        return x.replace("ایرباس", "Airbus")
    elif "بوئینگ" in x:
        return x.replace("بوئینگ", "Boeing")
    elif "بویینگ" in x:
        return x.replace("بویینگ", "Boeing")
    return x


def extract_fare_class_code(x):
    """Fare classes are typically 'alphanumeric codes' that airlines use to categorize and 
    differentiate the various types of tickets they offer, otherwise
    fare classes are codes used by airlines to categorize and manage the pricing and conditions of tickets,
    they provide valuable information about the ticket's flexibility, conditions, and benefits"""

    # Note -> The site we scrapped did not have a specific format to easily extract the fare class.
    # Format -> [AircraftModel][-][RegistrationCode]AirlineClassCode[_D]
    if len(x) in (1, 2):
        # Y, B, L, K, C, J, F, P, RY, RP, RB, etc
        return x
    elif x == "A17":
        return x
    elif x == "MDY" or x == "BoeingMDY":
        # MDY or BoeingMDY
        return "Y"
    elif 'TOR' in x:
        # 'M83TOR', 'MD8TOR', etc
        return None
    elif x.find("_") != -1:
        # 'BAE-87Y_D', 'AB346-MMRC_D', etc
        return x.split("_")[0][-1]
    elif x.find("DEF") == -1 and x[-2].isalpha() and x[-2].isupper():
        # 73HFS, 'MD8RP', 'MD8RY', 'MD8RB', 'Boeing737QQ', Boeing737QQ, etc
        return x[-2:]
    elif x.count("Y") == 1:
        # A310Y33, BoeingMD-83Y, BoeingMD-Y, 'BoeingY', Boeing737Y, '320Y', 'AirbusY', 'Airbus320Y', 'AB6Y', '737Y', 'M80Y', 'DEFY', '100Y', 'B737-800Y', etc
        return x[x.index("Y"):]
    # 'AirbusA310W', 'MD8L', '320C', 'DEFJ', 'DEFB', 'AB6W', 'A300B4-203V', 'Boeing737X', 'Boeing737Q', etc
    return x[-1]


def update_flight_sale_type(x):
    if pd.notnull(x):
        if "سیستمی" in x:
            return "Scheduled"
        elif "چارتری" in x:
            return "Charter"


def fillna_capacity(capacity_col):
    knn_imputer = KNNImputer(n_neighbors=5)
    capacity_filled = knn_imputer.fit_transform(capacity_col)
    capacity_filled_df = pd.DataFrame(capacity_filled, columns=capacity_col.columns)
    return capacity_filled_df
