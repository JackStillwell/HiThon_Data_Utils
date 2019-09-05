import json
import os
from copy import deepcopy

from tqdm import tqdm

from typing import Dict, Union, List, Tuple, Any

GodMatchData = Dict[str, List[Dict[str, Any]]]


def load_from_directory(directory_path: str) -> GodMatchData:

    all_data = {}

    for file_path in tqdm(os.listdir(directory_path)):
        with open(os.path.join(directory_path, file_path), "r") as data:
            all_data[file_path[:-5]] = json.loads(data.read())

    return all_data


def save_to_directory(data: GodMatchData, directory_path: str):
    for god_id in tqdm(data.keys()):
        with open(os.path.join(directory_path, f'{god_id}.json'),
                  "w") as file_pointer:
            str_to_write = json.dumps(data[god_id])
            file_pointer.write(str_to_write)


def load_god_map(file_path: str) -> List[Tuple[int, str]]:
    with open(file_path, "r") as in_file:
        raw_data = json.loads(in_file.read())

    return [(entry["id"], entry["Name"]) for entry in raw_data]


def load_item_map(file_path: str) -> List[Tuple[int, str]]:
    with open(file_path, "r") as in_file:
        raw_data = json.loads(in_file.read())

    return [(entry["ItemId"], entry["DeviceName"]) for entry in raw_data]


def filter_by_field(data: GodMatchData, field_name: str,
                    accepted_values: List[Union[str, int, float]]
                    ) -> GodMatchData:
    return {
        key: [
            match_data for match_data in val
            if match_data[field_name] in accepted_values
        ]
        for key, val in data.items()
    }


def get_most_played(data: GodMatchData) -> List[Tuple[str, int]]:
    ret_obj = [(name, num_matches)
               for name, num_matches in [(key, len(val))
                                         for key, val in data.items()]]
    ret_obj.sort(key=lambda x: x[1], reverse=True)
    return ret_obj


def get_most_banned(data: GodMatchData) -> List[Tuple[str, int]]:
    ret_obj = {}
    for god in data.keys():
        for match in data[god]:
            for ban in match["BanIds"]:
                if ban in ret_obj:
                    ret_obj[ban] += 1
                else:
                    ret_obj[ban] = 1

    ret_obj = list(ret_obj.items())
    ret_obj.sort(key=lambda x: x[1], reverse=True)
    return ret_obj


def get_most_picked(data: GodMatchData) -> List[Tuple[str, int]]:
    most_played = dict(get_most_played(data))
    most_banned = dict(get_most_banned(data))

    keys = []
    keys.extend([x[0] for x in list(most_played.items())])
    keys.extend([x[0] for x in list(most_banned.items())])
    keys = set(keys)

    retobj = {}
    for key in keys:
        pick_count = most_played[key] if most_played.get(key, False) else 0
        pick_count += most_banned[key] if most_banned.get(key, False) else 0

        retobj[key] = pick_count

    retobj = list(retobj.items())
    retobj.sort(key=lambda x: x[1], reverse=True)
    return retobj


def get_id_name(id_or_name: Union[int, str],
                mapping: List[Tuple[int, str]]) -> Tuple[int, str]:
    return next(
        (entry for entry in mapping if str(id_or_name) == str(entry[0])
         or str(id_or_name) == str(entry[1])),
        (-1, "NOT FOUND"),
    )


def get_most_recent_match_id(data: GodMatchData) -> str:
    all_matches = []
    for v in data.values():
        all_matches.extend(v)

    all_matches.sort(key=lambda x: x["Match_Date_Timestamp"], reverse=True)
    return all_matches[0]["MatchId"]


def populate_opposing_and_allied_gods(directory_path: str):
    data = load_from_directory(directory_path)

    ret_gmd = {}

    all_data = [match for matches in data.values() for match in matches]
    all_ret_data = deepcopy(all_data)

    for ret_data in tqdm(all_ret_data):
        ret_data['Opposing_GodIds'] = []
        ret_data['Allied_GodIds'] = []
        for match_data in all_data:
            if ret_data['MatchId'] == match_data['MatchId']:
                if ret_data['TaskForce'] == match_data['TaskForce']:
                    ret_data['Allied_GodIds'].append(match_data['GodId'])
                else:
                    ret_data['Opposing_GodIds'].append(match_data['GodId'])

        if not ret_gmd.get(ret_data['GodId'], None):
            ret_gmd[ret_data['GodId']] = []

        ret_gmd[ret_data['GodId']].append(ret_data)

    save_to_directory(ret_gmd, directory_path)
