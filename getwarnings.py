"""
This script can obtain warnings and alerts information from JMA.
See README.md for more information.
"""

import argparse
import urllib.request
import json
import pandas as pd

with urllib.request.urlopen(url="https://www.jma.go.jp/bosai/common/const/area.json") as area:

    def _get_area_name(area_dict, class20s_code, offices_code):
        """ Get area name."""
        return area_dict["offices"][offices_code]["name"] + \
            area_dict["class20s"][class20s_code]["name"]

    def _get_weather_station_center_name(area_dict, centers_code):
        """ Get Weather station center's name. """
        return area_dict["centers"][centers_code]["officeName"]

    def _get_warning_data(areacode1, class20s_code):
        """ Get warning and alerts data."""
        url = f'https://www.jma.go.jp/bosai/warning/data/warning/{areacode1}.json'
        with open("warnings.json", "r", encoding="utf-8") as warningnames,\
                urllib.request.urlopen(url=url) as warningdata:
            warningdata_dict = json.loads(warningdata.read())
            warningnames_dict = json.loads(warningnames.read())
            warning_codes = [warning["code"]
                for areainfo in warningdata_dict["areaTypes"][1]["areas"]
                if areainfo["code"] == str(class20s_code)
                for warning in areainfo["warnings"]
                if warning["status"] == "発表" or warning["status"] == "継続"]
            warning_texts = [warningnames_dict["warningnames"][code] for code in warning_codes]
            if warning_texts == []:
                return False
            return warning_texts

    def main():
        """ Main Function """
        # Get arguments
        parser = argparse.ArgumentParser(description='Obtain warnings and alerts from JMA.\n'\
            'Read README.md to know how to get Municipal district code.')
        parser.add_argument('-v', '--verbose', action='store_true', help="Verbose")
        parser.add_argument('-j', '--json', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--location', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--station', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('class20s_code', type=int,
            metavar="<Municipal district code>",  help="Municipal district code")
        args = parser.parse_args()

        # Set area_json
        area_dict = pd.read_json(area).to_dict()

        # Convert class20s_code to other code
        class20s_code = args.class20s_code
        class15s_code = int(area_dict["class20s"][class20s_code]["parent"])
        class10s_code = int(area_dict["class15s"][class15s_code]["parent"])
        offices_code = int(area_dict["class10s"][class10s_code]["parent"])
        centers_code = int(area_dict["offices"][offices_code]["parent"])

        if args.json is True:
            if args.location is True:
                print(_get_area_name(area_dict, class20s_code, offices_code))
                return
            elif args.station is True:
                print(_get_weather_station_center_name(area_dict, centers_code))
                return
            print(_get_warning_data(offices_code, class20s_code))
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
                print("- " + "\n- ".join(data))

    if __name__ == '__main__':
        main()
