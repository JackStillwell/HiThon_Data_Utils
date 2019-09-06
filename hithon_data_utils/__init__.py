import json
import os
from collections import namedtuple

from tqdm import tqdm

from typing import Dict, Union, List, Tuple, Any

GodMatchData = Dict[str, List[Dict[str, Any]]]
Id_Name = namedtuple('Id_Name', ['id', 'name'])


def load_from_directory(directory_path: str) -> GodMatchData:

    all_data = {}

    for file_path in tqdm(os.listdir(directory_path)):
        with open(os.path.join(directory_path, file_path), "r") as data:
            all_data[file_path[:-5]] = json.loads(data.read())

    return all_data


def save_to_directory(data: GodMatchData, directory_path: str):
    for god_id in tqdm(data.keys()):
        with open(os.path.join(directory_path, f"{god_id}.json"),
                  "w") as file_pointer:
            str_to_write = json.dumps(data[god_id])
            file_pointer.write(str_to_write)


def load_god_map(file_path: str) -> List[Id_Name]:
    with open(file_path, "r") as in_file:
        raw_data = json.loads(in_file.read())

    return [Id_Name(entry["id"], entry["Name"]) for entry in raw_data]


def load_item_map(file_path: str) -> List[Id_Name]:
    with open(file_path, "r") as in_file:
        raw_data = json.loads(in_file.read())

    return [
        Id_Name(entry["ItemId"], entry["DeviceName"]) for entry in raw_data
    ]


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
                mapping: List[Id_Name]) -> Id_Name:
    return next(
        (entry for entry in mapping if str(id_or_name) == str(entry[0])
         or str(id_or_name) == str(entry[1])),
        Id_Name(-1, "NOT FOUND"),
    )


def get_most_recent_match_id(data: GodMatchData) -> str:
    all_matches = []
    for v in data.values():
        all_matches.extend(v)

    all_matches.sort(key=lambda x: x["Match_Date_Timestamp"], reverse=True)
    return all_matches[0]["MatchId"]


def migrate_records_in_directory(directory_path: str, ):
    data = load_from_directory(directory_path)
    all_data = [match for matches in data.values() for match in matches]

    # first build a dict of all gods in matches
    match_gods: Dict[int, Dict[int, List[int]]] = {}
    for match in tqdm(all_data):
        if not match_gods.get(match["MatchId"], None):
            match_gods[match["MatchId"]] = {1: [], 2: []}

        match_gods[match["MatchId"]][match["TaskForce"]].append(match["GodId"])

    for match in tqdm(all_data):
        opposing_taskforce = 1 if match["TaskForce"] == 2 else 2

        match["Allied_GodIds"] = [v for v in match_gods[match["MatchId"]][
            match["TaskForce"]] if v != match["GodId"]]
        match["Opposing_GodIds"] = match_gods[
            match["MatchId"]][opposing_taskforce]

    ret_gmd = {}
    # build the final dictionary
    for mod_data in all_data:
        if not ret_gmd.get(mod_data["GodId"], None):
            ret_gmd[mod_data["GodId"]] = []

        ret_gmd[mod_data["GodId"]].append(mod_data)

    save_to_directory(ret_gmd, directory_path)


def convert_keys_to_names(data: List[Tuple[str, Any]],
                          god_map: List[Id_Name]) -> List[Tuple[str, Any]]:
    return [(get_id_name(k, god_map).name, v) for k, v in data]


WinningData = namedtuple('WinningData', ['num_wins', 'perc_wins'])


def get_most_winning(data: GodMatchData) -> List[Tuple[str, WinningData]]:
    win_data = {
        key: WinningData(
            len([v for v in val if v['Win_Status'] == 'Winner']),
            len([v for v in val if v['Win_Status'] == 'Winner']) / len(val))
        for key, val in data.items()
    }

    ret_list = list(win_data.items())
    ret_list.sort(key=lambda x: x[1].num_wins, reverse=True)
    return ret_list


def get_most_winning_against(god_id: str, data: GodMatchData
                             ) -> List[Tuple[str, WinningData]]:
    win_data = {
        key: WinningData(
            len([
                v for v in val if v['Win_Status'] == 'Winner'
                and god_id in v['Opposing_GodIds']
            ]),
            len([
                v for v in val if v['Win_Status'] == 'Winner'
                and god_id in v['Opposing_GodIds']
            ]) / len(val))
        for key, val in data.items()
    }

    ret_list = list(win_data.items())
    ret_list.sort(key=lambda x: x[1].num_wins, reverse=True)
    return ret_list
