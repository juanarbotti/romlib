import re
import csv
import importlib.resources
import os
import json
import Levenshtein
import difflib
from collections import defaultdict

import pandas as pd
from rapidfuzz import fuzz

from .errors import FilesizeSmallerThanLenghts

class Tags:

    # File information
    _full_filename = None
    _rom_type = None
   
    # Standard codes
    GC_STANDARD = [] # Constant data
    _gc_standard_list = [] # Current tag stores

    # Translation codes
    GC_TRANSLATIONS = []
    _gc_translations_list = []

    # Universal codes
    GC_UNIVERSAL = []
    _gc_universal_list = []

    # Country standard codes
    GC_COUNTRY = []
    _gc_country_list = []

    # Country combinations
    GC_COUNTRY_COMBINATIONS = []
    _gc_country_combinations_list = []

    # Unofficial country codes
    GC_COUNTRY_UNOFFICIAL = []
    _gc_country_unofficial_list = []

    # Genesis/Megadrive specific codes
    GC_GENESIS = []
    _gc_genesis_list = []

    # Nintendo Entertainment System specific codes
    GC_NES = []
    _gc_nes_list = []

    # Super Nintendo Entertainment System specific codes
    GC_SNES = []
    _gc_snes_list = []

    # This is an auxilary value comparator for those tags holding values
    # list[touple(start_string,ending_string)]
    _AUXILIARY_UNIVERSAL_VALUES = [
        ("(Prototype",")"),
        ("(REV",")"),
        ("(V",")"),
        (None,"-in-1"),
        ("(Vol",")"),
        ("[h","C]"),
        ("(","Hack)"),
        ("(","MBit)"),
        ("(19", ")"),
        ("(20", ")"),
        ("[R-", "]"),
        ("(", "Cart)")
    ]

    def __init__(self, filename=None, rom_type=None):
        """
        It detects all GoodCodes as possible, grouped by its categories.

        Args:
            filename (str) : filename with tags to be recognized, with or without extension.
            rom_type : the ROM for applying specific detections. If None, it will try to use all code sets.
        """
        
        # Load codes
        self._load_codes()

        # If filename is specified, then use load method
        if filename != None:
            self.load(filename=filename, rom_type=rom_type)
            
    def _load_codes(self):
        """
        Will load constants from CSV files.
        """

        # Standard tags
        with importlib.resources.open_text("romlib.data", "gc_standard.csv", encoding='utf-8') as f:
            self.GC_STANDARD = list(csv.DictReader(f))

        # Translation codes for T+ and T- tags
        with importlib.resources.open_text("romlib.data", "gc_translations.csv", encoding='utf-8') as f:
            self.GC_TRANSLATIONS = list(csv.DictReader(f))

        # Translation codes for T+ and T- tags
        with importlib.resources.open_text("romlib.data", "gc_universal.csv", encoding='utf-8') as f:
            self.GC_UNIVERSAL = list(csv.DictReader(f))

        # Standar country codes
        with importlib.resources.open_text("romlib.data", "gc_country.csv", encoding='utf-8') as f:
            self.GC_COUNTRY = list(csv.DictReader(f))

        # Most common country code combinations tags
        with importlib.resources.open_text("romlib.data", "gc_country_combinations.csv", encoding='utf-8') as f:
            self.GC_COUNTRY_COMBINATIONS = list(csv.DictReader(f))
        
        # Unoffical country codes tags
        with importlib.resources.open_text("romlib.data", "gc_country_unofficial.csv", encoding='utf-8') as f:
            self.GC_COUNTRY_UNOFFICIAL = list(csv.DictReader(f))

        # Genesis/Megadrive specific codes
        with importlib.resources.open_text("romlib.data", "gc_gen.csv", encoding='utf-8') as f:
            self.GC_GENESIS = list(csv.DictReader(f))

        # NES specific codes
        with importlib.resources.open_text("romlib.data", "gc_nes.csv", encoding='utf-8') as f:
            self.GC_NES = list(csv.DictReader(f))
        
        # SNES specific codes
        with importlib.resources.open_text("romlib.data", "gc_snes.csv", encoding='utf-8') as f:
            self.GC_SNES = list(csv.DictReader(f))
    
    def _recognize_gc(self, filename):
        """
        Builds tags class information.
        """
        
        # Standard Codes
        for item in self.GC_STANDARD:
            if item["re_tag"]:
                pattern_tag = re.findall(item["re_tag"], filename)
                for item_tag in pattern_tag:            

                    # First, check if it is a translation
                    if item["tag"] in ["[T-]","[T+]"]:
                        for translation_tag in self.GC_TRANSLATIONS:
                            len_translation = len(translation_tag) -1
                            tag_comparator = item_tag[:len_translation].strip()
                            if tag_comparator == translation_tag["code"]:
                                value_tag = translation_tag["code"]
                                extra_data = item_tag.replace(value_tag, "")
                                extra_data = None if extra_data == "" else extra_data
                                self._gc_standard_list.append(
                                    {
                                        "tag": item["tag"],
                                        "value": value_tag,
                                        "short_desc": item["short_desc"],
                                        "short_desc_spa": item["short_desc_spa"],
                                        "extra_data": extra_data,
                                        "raw_detection": item_tag
                                    }
                                )
                        
                    # If no translation code, append as regular
                    else:
                        self._gc_standard_list.append(
                            {
                                "tag": item["tag"],
                                "value": item_tag if item["tag"] != item_tag else None,
                                "short_desc": item["short_desc"],
                                "short_desc_spa": item["short_desc_spa"],
                                "extra_data": None,
                                "raw_detection": item_tag,
                            }
                        )
        
        # Universal codes
        for item in self.GC_UNIVERSAL:
            if item["re_tag"]:
                pattern_tag = re.findall(item["re_tag"], filename)
                for item_tag in pattern_tag:

                    extra_data = None
                    value = item_tag if item["tag"] != item_tag else None
                    value = self._auxiliary_universal_value_retriver(item_tag)

                    self._gc_universal_list.append(
                        {
                            "tag": item["tag"],
                            "value": value,
                            "short_desc": item["short_desc"],
                            "short_desc_spa": item["short_desc_spa"],
                            "extra_data": None,
                            "raw_detection": item_tag
                        }
                    )

        # Standard Country Codes
        for item in self.GC_COUNTRY:
            if item["re_tag"]:
                pattern_tag = re.findall(item["re_tag"], filename)
                for item_tag in pattern_tag:
                    self._gc_country_list.append(
                        {
                            "tag": item["tag"],
                            "country": item["country"],
                            "country_spa": item["country_spa"],
                            "preferred": "not apply",
                            "raw_detection": item_tag
                        }
                    )

        # Most common country code combinations tags
        for item in self.GC_COUNTRY_COMBINATIONS:
            if item["re_tag"]:
                pattern_tag = re.findall(item["re_tag"], filename)
                for item_tag in pattern_tag:
                    self._gc_country_combinations_list.append(
                        {
                            "tag": item["tag"],
                            "country": item["country"],
                            "country_spa": item["country_spa"],
                            "preferred": "not apply",
                            "raw_detection": item_tag
                        }
                    )

        # Unoffical country codes
        for item in self.GC_COUNTRY_UNOFFICIAL:
            if item["re_tag"]:
                pattern_tag = re.findall(item["re_tag"], filename)
                for item_tag in pattern_tag:
                    self._gc_country_unofficial_list.append(
                        {
                            "tag": item["tag"],
                            "country": item["country"],
                            "country_spa": item["country_spa"],
                            "preferred": eval(item["preferred"]),
                            "raw_detection": item_tag
                        }
                    )

        # Sega Genesis/Megadrive codes
        if self._rom_type == "SMD" or self._rom_type == None:
            for item in self.GC_GENESIS:
                if item["re_tag"]:
                    pattern_tag = re.findall(item["re_tag"], filename)
                    for item_tag in pattern_tag:
                        self._gc_genesis_list.append(
                            {
                                "tag": item["tag"],
                                "value": None,
                                "short_desc": item["short_desc"],
                                "short_desc_spa": item["short_desc_spa"],
                                "extra_data": None,
                                "raw_detection": item_tag
                            }
                        )

        # Sega Genesis/Megadrive codes
        if self._rom_type == "NES" or self._rom_type == None:
            for item in self.GC_NES:
                if item["re_tag"]:
                    pattern_tag = re.findall(item["re_tag"], filename)
                    for item_tag in pattern_tag:
                        to_store = {
                            "tag": item["tag"],
                            "value": None,
                            "short_desc": item["short_desc"],
                            "short_desc_spa": item["short_desc_spa"],
                            "extra_data": None,
                            "raw_detection": item_tag
                        }
                        if item["tag"] == "SMB":
                            to_store["value"] = item_tag[3:]
                        elif item["tag"] == "[hMxx]":
                            to_store["value"] = item_tag[2:-1]
                        elif item["tag"] == "(Mapper)":
                            to_store["value"] = item_tag[7:-1]
                        else:
                            value = item_tag if item["tag"] != item_tag else None
                        self._gc_nes_list.append(to_store)

        # Sega Genesis/Megadrive codes
        if self._rom_type == "SNES" or self._rom_type == None:
            for item in self.GC_SNES:
                if item["re_tag"]:
                    pattern_tag = re.findall(item["re_tag"], filename)
                    for item_tag in pattern_tag:
                        to_store = {
                            "tag": item["tag"],
                            "value": None,
                            "short_desc": item["short_desc"],
                            "short_desc_spa": item["short_desc_spa"],
                            "extra_data": None,
                            "raw_detection": item_tag
                        }
                        self._gc_snes_list.append(to_store)

    def _clear(self):
        self._full_filename = None
        self._gc_standard_list = []
        self._gc_translations_list = []
        self._gc_universal_list = []
        self._gc_country_list = []
        self._gc_country_combinations_list = []
        self._gc_country_unofficial_list = []
        self._gc_genesis_list = []
        self._gc_nes_list = []
        self._gc_snes_list = []

    def load(self, filename, rom_type=None):
        """
        Performs a new file name or name recognition. IT will update all variables with new information.

        Args:
            filename (str): the rom or file name to load and analyze.
            rom_type : the ROM for applying specific detections. If None, it will try to use all code sets.

        Returns:
            None
        """
        self._clear()

        self._full_filename = filename
        self._rom_type = rom_type
        base_name = os.path.basename(filename)

        self._recognize_gc(base_name)

    def clear(self):
        """
        Clears all information stored in object.
        """
        self._clear()

    def _auxiliary_universal_value_retriver(self, item_tag):
        """
        This auxiliary method checks for stored data in universal codes and returns its value.
        
        Returns:
            str: value detected in tag
        """

        value = None
        for prefix, sufix in self._AUXILIARY_UNIVERSAL_VALUES:

            # Starts and ends with something
            if prefix is not None and sufix is not None:
                if item_tag.startswith(prefix) and item_tag.endswith(sufix):

                    # 'Prototype' is special, sometimes has a ' - ' separator from data
                    if prefix == "(Prototype":
                        # removes ' - ' at begining and ')' at the end
                        value = item_tag[len(prefix) + len(' - '):-len(sufix)]
                    # 'Cart' can sometimes has '-' between from data
                    elif sufix == "Cart)":
                        value = item_tag[len(prefix):-len(sufix)].replace("-","").strip()
                    else:
                        value = item_tag[len(prefix):-len(sufix)]

            # Ends with
            elif prefix is None:
                if item_tag.endswith(sufix):
                    value = item_tag[:-len(sufix)]

            # Starts with (not common)
            elif sufix is None:
                if item_tag.startswith(prefix):
                    value = item_tag[:len(prefix)]

        return value
        
    @property
    def gc_standard(self):
        """
        List standard tags and their short descriptions.

        Returns:
            list[dict]: A list of dictionaries containing a tag and its short description, if available.

        """
        return self._gc_standard_list
    
    @property
    def gc_standard_json(self):
        return json.dumps(self._gc_standard_list, indent=4)
    
    @property
    def gc_universal(self):
        """
        List universal tags and their short descriptions.

        Returns:
            list[dict]: A list of dictionaries containing a tag and its short description, if available.

        """
        return self._gc_universal_list
    
    @property
    def gc_universal_json(self):
        return json.dumps(self._gc_universal_list, indent=4)

    @property
    def gc_country(self):
        """
        List all country standard tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_country_list + self._gc_country_combinations_list
    
    @property
    def gc_country_json(self):
        return json.dumps(self._gc_country_list + self._gc_country_combinations_list, indent=4)
    
    @property
    def gc_country_unofficial(self):
        """
        List all country unofficial tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_country_unofficial_list
    
    @property
    def gc_country_unoficial_json(self):
        return json.dumps(self._gc_country_unofficial_list, indent=4)
    
    @property
    def gc_genesis(self):
        """
        List all Sega Genesis/Megadrive tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_genesis_list
    
    @property
    def gc_genesis_list_json(self):
        return json.dumps(self._gc_genesis_list, indent=4)

    @property
    def gc_nes(self):
        """
        List all Nintendo Entertainment System tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_nes_list
    
    @property
    def gc_nes_list_json(self):
        return json.dumps(self._gc_nes_list, indent=4)
    
    @property
    def gc_snes(self):
        """
        List all Super Nintendo Entertainment System tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_genesis_list
    
    @property
    def gc_snes_list_json(self):
        return json.dumps(self._gc_snes_list, indent=4)

    @property
    def gc_all(self):
        """
        List all tags found with its corresponding information.

        Returns:
            list[dict]: A list of dictionaries containing a tag and its short description, if available.

        """
        return self._gc_standard_list + self._gc_universal_list +\
              self._gc_country_list + self._gc_country_combinations_list +\
                  self._gc_country_unofficial_list + self._gc_genesis_list
    
    @property
    def gc_all_json(self):
        
        r_var = {
            "standard": self._gc_standard_list,
            "universal": self._gc_universal_list,
            "country": self._gc_country_list + self._gc_country_combinations_list,
            "country_unofficial": self._gc_country_unofficial_list,
        }

        if self._gc_genesis_list != []:
            r_var["genesis"] = self._gc_genesis_list
        if self._gc_nes_list != []:
            r_var["nes"] = self._gc_nes_list
        if self._gc_snes_list != []:
            r_var["snes"] = self._gc_snes_list

        return json.dumps(r_var, indent=4, ensure_ascii=False)
    
    @property
    def rom_type(self):
        """Returns ROM system type str (SMD, NES, SMS, SNES)"""
        return self._rom_type
    
    @property
    def tags_found(self):

        list_items = []

        for item in self.gc_all:
            tag = item.get("tag")
            list_items.append(tag)
        return list_items
        
    @property
    def filename(self):
        return self._full_filename
    
    @property
    def rom_name(self):
        """
        Returns clean ROM name.

        Returns:
            str: ROM name without tags or extension.
        """
        return Semantics.remove_tags(self._full_filename)
        

class Semantics:

    @staticmethod
    def remove_tags(rom_name):
        """
        Returns clean ROM name without tags
        Returns:
            str: ROM name without tags or extension.
        """
        filename, _ = os.path.splitext(rom_name)
        filename = os.path.basename(filename)
        clean_name = re.sub(r'\s*[(\[].*?[)\]]', '', filename).strip()
        return clean_name
    
    @staticmethod
    def rom_normalize(rom_name):
        """
        Returns the clean name without tags, lowercase and without underscores or multiple spaces.
        Args:
            rom_name (str): a ROM name.
        """
        # First, applies tags remover
        rom_name = Semantics.remove_tags(rom_name)

        # Removes -, _ and multiple spaces
        rom_name = re.sub(r'[_\-]+', ' ', rom_name).strip() 
        rom_name = re.sub(r'\s+', ' ', rom_name)
        
        # Lower and return
        return rom_name.lower()
        
    @staticmethod
    def generate_blueprint(rom_path, lengths=[64, 64,64,64]):
        """
        Evaluates a file and returns its bytes given from parts of the file as a string sequence. The result is a 'blueprint' like string of a file.
        
        Args:
            rom_path (str): file full path.
            lenghts[int]: at least 2 bytes chunks must be specified (begining and end of the file). More chunks will be taken from differnt and equidistant part of the file.

        Returns:
            (str): hex bytes in format "bbb-bbb-bbb..."
        """

        
        if len(lengths) < 2:
            raise ValueError("You must provide at least 2 lengths (start length and end lenght)")
        
        # get file size
        file_size = os.path.getsize(rom_path)
        
        if sum(lengths) > file_size:
            raise FilesizeSmallerThanLenghts("The filesize is smaller than the bytes needed to analyze it.") 

        # divide file size by 4 to get positions
        step = file_size // len(lengths)

        with open(rom_path, "rb") as f:
            fragments = []
            for i, length in enumerate(lengths):
                # goes to positions set in lenght. 
                position = min(step * i, file_size-length)
                f.seek(position)
                fragment = f.read(length).hex()
                fragments.append(fragment)

            return "-".join(fragments)
    
    @staticmethod
    def get_similarity_ratio(value_a: str, value_b: str) -> float:
        """
        Returns a similarity ratio between string A and string B.
        Actual method: Levenshtein corrected (fuzz)
        Args:
            value_a: first string to compare
            value_b: second string to compare
        Returns:
            (float) : similatrity ratio
        """

        ratio = fuzz.ratio(value_a, value_b) / 100
        return round(ratio,2)

    @staticmethod
    def file_compare_binary(rom_path_a: str, rom_path_b: str) -> float:
        """
        Compare 2 ROM files at byte level. Returns the rate of similarity calculated by this method.
        Args:
            rom_path_a = first ROM to compare
            rom_path_b = second ROM to compare
        
        Returns:
            (float): rate of similarity
        """

        file_1_str = Semantics.generate_blueprint(rom_path_a)
        file_2_str = Semantics.generate_blueprint(rom_path_b)

        return Semantics.get_similarity_ratio(file_1_str, file_2_str)


class Categories:
    
    @staticmethod
    def get_masters(rom_directory, with_full_path=True):
        """
        Selects the best ROMs among other ROMs probaly being same games. This is equal to get the unieque games.

        Args:
            rom_directory (str): path where ROMs are stored.
            with_full_path (bool): if the items contained in resulting list should be with its full path or just the filename.

        Returns:
            (list) : the master games.
        """
        rom_files = set(os.listdir(rom_directory))

        header_files = []

        for file in rom_files:
            if "[!]" in file:
                header_files.append(file)


        rom_files = rom_files - set(header_files)

        for file_a in rom_files:
            
            file_a_rtags = Semantics.remove_tags(file_a)

            store_equal = [file_a]

            # Get similar names for file_a
            for file_b in rom_files:
                file_b_rtags = Semantics.remove_tags(file_b)
                if file_a != file_b:
                    similar_name_rate = Semantics.get_similarity_ratio(file_a_rtags, file_b_rtags)
                    if similar_name_rate > 95:
                        store_equal.append(file_b)

            clsTags = Tags()
            selected = None
            min_tags = float("inf")  # Inicializamos con un valor alto
            min_length = float("inf")

            # Determinar el mejor candidato
            for item in store_equal:
                clsTags.load(item)
                num_tags = len(clsTags.gc_all)
                file_length = len(item)

                # Primero elegimos el que tenga menos tags
                if num_tags < min_tags:
                    min_tags = num_tags
                    min_length = file_length
                    selected = item

                # Si tienen la misma cantidad de tags, elegimos el nombre más corto
                elif num_tags == min_tags and file_length < min_length:
                    min_length = file_length
                    selected = item

            header_files.append(selected if not with_full_path else os.path.join(rom_directory, selected))
        
        return header_files

    @staticmethod
    def get_slaves(master_full_path, roms_full_path):

        # Get ROMs list
        roms_list = os.listdir(roms_full_path)
        
        # Calculate blueprint from master and get master base name 
        try:
            master_blueprint = Semantics.generate_blueprint(master_full_path)
        except:
            master_blueprint = None

        master = os.path.basename(master_full_path)

        # Storages
        slaves = []

        # Loop over rom list
        for slave in roms_list:

            # Get slave full path
            slave_full_path = os.path.join(roms_full_path, slave)
            
            # omit master itself
            if slave != master:

                # First, compare filename
                try:
                    ratio_filename = Semantics.get_similarity_ratio(master, slave)
                except:
                    ratio_filename = 0.0
                if ratio_filename > 0.9:
                    # stop program, files probably belongs to a collection
                    slaves.append(slave)
                else:

                    if master_blueprint == None:
                        continue

                    # File was not similar to any name in collection, so now it will look at byte level
                    try:
                        slave_blueprint = Semantics.generate_blueprint(slave_full_path)
                    except:
                        continue

                    ratio_blueprints = Semantics.get_similarity_ratio(master_blueprint, slave_blueprint)
                    if ratio_blueprints > 0.85 and ratio_filename > 0.75:
                        slaves.append(slave)

        return slaves

    @staticmethod
    def group_roms(rom_directory):

        # List files
        rom_files = os.listdir(rom_directory)

        # A list for blueprints ok
        blueprints_str = []
        # A list for orphans
        orphans = []

        # Generates blueprints
        for rom in rom_files:
            full_path_rom = os.path.join(rom_directory, rom)
            try:
                blueprints_str.append((rom, Semantics._generate_eval_string(full_path_rom,[64,64,64,64])))
            except FilesizeSmallerThanLenghts:
                orphans.append(rom)

        groups = {}
        for rom_file, blueprint in blueprints_str:

            data = None

            # remove tags from filneame
            clean_rom_file = Semantics.remove_tags(rom_file)
            
            # compares filename
            for key, items in groups.items():
                similar_name_rate = max([
                    fuzz.ratio(clean_rom_file, Semantics.remove_tags(rf))
                    for i, rf in enumerate(items["slaves"])
                    if items["sim_rate"][i][0] != "F"  # Exclude those introduced by blueprint, to avoid beeing greedy
                ])
                if similar_name_rate > 95:
                    data = ("N",round(similar_name_rate,2))
                    break
            
            # If no filename comparison was positive, then checks the file blueprint
            if data == None:
                # compares file blueprint
                for key, items in groups.items():
                    similar_file_rate = max([fuzz.ratio(bp, blueprint) for bp in items["blueprints"]])
                    if similar_file_rate > 85:
                        data = ("F",round(similar_file_rate,2))
                        break

            if data:
                items["slaves"].append(rom_file)
                items["blueprints"].append(blueprint)  # Guardar más de un blueprint para mejor comparación
                items["sim_rate"].append(data)
            else:
                groups[rom_file] = {"blueprints": [blueprint], "slaves": [rom_file], "sim_rate": [(1.0, "MASTER")]}
                        
        if orphans:
            groups["orphans"] = {"blueprints": None, "slaves": orphans, "sim_rate": ()}

        return groups

        
# Available elements to be imported
__all__ = ["Tags", "Semantics", "Categories"]

# Only show available
def __dir__():
    return __all__

# Rasie an error if someone wants to import dependencies
def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"Module 'romlib.tags' has no attribute '{name}'")
    return globals()[name]