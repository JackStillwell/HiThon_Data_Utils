import json
import os

from typing import Dict, Union, List, Tuple


GodMatchData = Dict[str, List[Dict[str, Union[str, int, float]]]]


def load_from_directory(directory_path: str) -> GodMatchData:

    all_data = {}

    for file_path in os.listdir(directory_path):
        with open(os.path.join(directory_path, file_path), "r") as data:
            all_data[file_path[:-5]] = json.loads(data.read())

    return all_data


def filter_by_field(
    data: GodMatchData, field_name: str, accepted_values: List[Union[str, int, float]]
) -> GodMatchData:
    return {
        key: [
            match_data
            for match_data in val
            if match_data[field_name] in accepted_values
        ]
        for key, val in data.items()
    }


def get_most_played(data: GodMatchData) -> List[Tuple[str, int]]:
    ret_obj = [
        (name, num_matches)
        for name, num_matches in [(key, len(val)) for key, val in data.items()]
    ]
    ret_obj.sort(key=lambda x: x[1])
    return ret_obj
