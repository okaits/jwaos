"""
This script can obtain warnings and alerts information from JMA.
See README.md for more information.
"""

import argparse
import urllib.request
import json
import os
import sys
import pandas as pd

with urllib.request.urlopen(url="https://www.jma.go.jp/bosai/common/const/area.json") as area:

    def _get_area_name(area_dict, class20s_code, offices_code):
        """ Get area name."""
        return area_dict["offices"][int(offices_code)]["name"] + \
            area_dict["class20s"][int(class20s_code)]["name"]

    def _get_weather_station_center_name(area_dict, centers_code):
        """ Get Weather station center's name. """
        return area_dict["centers"][int(centers_code)]["officeName"]

    def _get_warning_data(offices_code, class20s_code, json_output):
        """ Get warning and alerts data."""
        url = f'https://www.jma.go.jp/bosai/warning/data/warning/{offices_code}.json'
        print(url)
        with open("warnings.json", "r", encoding="utf-8") as warningnames,\
                urllib.request.urlopen(url=url) as warningdata:
            warningdata_dict = json.loads(warningdata.read())
            warningnames_dict = json.loads(warningnames.read())
            warning_codes = [warning["code"]
                for areainfo in warningdata_dict["areaTypes"][1]["areas"]
                if areainfo["code"] == str(class20s_code)
                for warning in areainfo["warnings"]
                if warning["status"] == "発表" or warning["status"] == "継続"]
            if json_output is True:
                return warning_codes
            warning_texts = [warningnames_dict["warningnames"][code] for code in warning_codes]
            if warning_texts == []:
                return False
            return warning_texts

    def _config(configfile_path, class20s_code, config_only):
        if os.path.exists(configfile_path):
            if config_only is True:
                print("Error 005: Config file already exists. "\
                    "Please remove it by --clear-config option.", file=sys.stderr)
                return 5
            if class20s_code is not None:
                print("Info: Config file exists, but found --mdcode. Not loading config...",
                    file=sys.stderr)
                return class20s_code
            print("Info: Config file exists. Loading config...", file=sys.stderr)
            with open(configfile_path, "r", encoding="utf-8") as configfile:
                try:
                    config = json.load(configfile)
                    class20s_code = config["location"]["class20s_code"]
                except KeyError:
                    print("Error 002: Config file is broken.", file=sys.stderr)
                    return 2
                except Exception: # pylint: disable=W0703
                    print("Error 003: Something went wrong while loading config file. "\
                        "Config file may be broken.", file=sys.stderr)
                    return 3
            return class20s_code
        elif not os.path.exists(configfile_path):
            if config_only is not True:
                print("Info: Config file not exists. Creating config file...")
            with open(configfile_path, "w", encoding="utf-8") as configfile:
                config = {}
                config["location"] = {}
                if class20s_code is None:
                    print("Error 001: --mdcode is required "\
                        "for creating config file.", file=sys.stderr)
                    return 1
                config["location"]["class20s_code"] = class20s_code
                json.dump(config, configfile, ensure_ascii=False, indent=4)
                return class20s_code



    def main():
        """ Main Function """
        # Get arguments
        parser = argparse.ArgumentParser(description='Obtain warnings and alerts from JMA.\n'\
            'Read README.md to know how to get Municipal district code.')
        parser.add_argument('-v', '--verbose', action='store_true', help="Verbose [default=False]")
        parser.add_argument('-j', '--json', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('-c', '--config', dest='configfile_path',
            action='store_true', help='Config file path. Needed by -C or first execute. '\
                '[default=config.json]', default="config.json")
        parser.add_argument('-C', '--config-only', dest="config_only", action="store_true",
            help="Create config file and exit.")
        parser.add_argument('--clear-config', action='store_true', help='Clear config file. '\
            'Requires --config', dest="clear_config")
        parser.add_argument('-m', '--mdcode', type=int, required=False,  dest="class20s_code",
            metavar="<Municipal district code>", help="Set municipal district code.")
        args = parser.parse_args()

        # Create area_json
        area_dict = pd.read_json(area).to_dict()

        # --clear-config option
        if args.clear_config is True:
            print("Removing config file...")
            os.remove(args.configfile_path)
            print("Done.")
            return

        # --only-config option
        if args.config_only is True:
            _config(args.configfile_path, args.class20s_code, True)
            return

        # Get class20s_code from config file
        class20s_code = str(_config(args.configfile_path, args.class20s_code)).zfill(7) #7

        if class20s_code == 1:
            os.remove(args.configfile_path)
            return False
        if class20s_code in (2, 3):
            return False

        # Convert class20s_code to other codes
        try:
            class15s_code = area_dict["class20s"][int(class20s_code)]["parent"].zfill(7)
        except KeyError:
            print("Error 004: Your municipal district code may be not correct.")
            return False

        class10s_code = area_dict["class15s"][int(class15s_code)]["parent"].zfill(7)
        offices_code = area_dict["class10s"][int(class10s_code)]["parent"].zfill(6)
        centers_code = area_dict["offices"][int(offices_code)]["parent"].zfill(7)

        # Main code
        if args.json is True:
            output = {}
            output["station"] = {"code": centers_code,
                "name": _get_weather_station_center_name(area_dict, centers_code)}
            output["location"] = {"class20s_code": class20s_code,
                "name": _get_area_name(area_dict, class20s_code, offices_code)}
            print(json.dumps(output, ensure_ascii=False))
            return

        if args.verbose is True:
            print(f"Weather station code: {centers_code}")
            print(f"Prefecture code: {offices_code}")
            print(f"Municipal district code: {class20s_code}")
            print(f"Area name: {_get_area_name(area_dict, class20s_code, offices_code)}")
            print("Weather Station name: "
                f"{_get_weather_station_center_name(area_dict, centers_code)}")
            data = _get_warning_data(offices_code, class20s_code)
            if data is False:
                print("No warnings and alerts.")
            else:
                print("Warnings and alerts:")
                print("- " + "\n- ".join(data))
        elif args.verbose is False:
            data = _get_warning_data(offices_code, class20s_code)
            if data is False:
                print("No warnings and alerts.")
            else:
                print(" ".join(data))

    if __name__ == '__main__':
        if main() is False:
            exit(1)
        else:
            exit(0)
