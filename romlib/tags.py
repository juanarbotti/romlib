import re
import csv
import importlib.resources
import os

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
        with importlib.resources.open_text("romlib.data", "gc_standard.csv") as f:
            self.GC_STANDARD = list(csv.DictReader(f))

        # Translation codes for T+ and T- tags
        with importlib.resources.open_text("romlib.data", "gc_translations.csv") as f:
            self.GC_TRANSLATIONS = list(csv.DictReader(f))

        # Translation codes for T+ and T- tags
        with importlib.resources.open_text("romlib.data", "gc_universal.csv") as f:
            self.GC_UNIVERSAL = list(csv.DictReader(f))

        # Standar country codes
        with importlib.resources.open_text("romlib.data", "gc_country.csv") as f:
            self.GC_COUNTRY = list(csv.DictReader(f))

        # Most common country code combinations tags
        with importlib.resources.open_text("romlib.data", "gc_country_combinations.csv") as f:
            self.GC_COUNTRY_COMBINATIONS = list(csv.DictReader(f))
        
        # Unoffical country codes tags
        with importlib.resources.open_text("romlib.data", "gc_country_unofficial.csv") as f:
            self.GC_COUNTRY_UNOFFICIAL = list(csv.DictReader(f))

        # Genesis/Megadrive specific codes
        with importlib.resources.open_text("romlib.data", "gc_gen.csv") as f:
            self.GC_GENESIS = list(csv.DictReader(f))
    
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
                            "country_spa": item["country_spa"]
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
                            "country_spa": item["country_spa"]
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
                            "preferred": eval(item["preferred"])
                        }
                    )

        # Sega Genesis/Megadrive codes
        if self._rom_type == "Mega Drive" or self._rom_type == None:
            for item in self.GC_GENESIS:
                if item["re_tag"]:
                    pattern_tag = re.findall(item["re_tag"], filename)
                    for item_tag in pattern_tag:
                        self._gc_genesis_list.append(
                            {
                                "tag": item["tag"],
                                "short_desc": item["short_desc"],
                                "short_desc_spa": item["short_desc_spa"]
                            }
                        )

    def _clear(self):
        self._gc_standard_list = []
        self._gc_translations_list = []
        self._gc_universal_list = []
        self._gc_country_list = []
        self._gc_country_combinations_list = []
        self._gc_country_unofficial_list = []
        self._gc_genesis_list = []

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

        self._recognize_gc(base_name, rom_type=rom_type)

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
    def gc_universal(self):
        """
        List universal tags and their short descriptions.

        Returns:
            list[dict]: A list of dictionaries containing a tag and its short description, if available.

        """
        return self._gc_universal_list

    @property
    def gc_country(self):
        """
        List all country standard tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_country_list + self._gc_country_combinations_list
    
    @property
    def gc_country_unofficial(self):
        """
        List all country unofficial tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_country_unofficial_list
    
    @property
    def gc_genesis(self):
        """
        List all Sega Genesis/Megadrive tags and its short description.

        Returns:
            list[dict]: A list of dictionaries containing tag and its short description, if available.

        """
        return self._gc_genesis_list

    @property
    def gc_all(self):
        """
        List all tags found with its corresponding information.

        Returns:
            list[dict]: A list of dictionaries containing a tag and its short description, if available.

        """
        return self._gc_standard_list + self._gc_country_list + self._gc_country_combinations_list + self._gc_genesis_list
    
    @property
    def full_filename(self):
        return self._full_filename
    
    @property
    def file_name(self):
        return os.path.basename(self._full_filename)

    @property
    def file_extension(self):
        """
        Returns the file extension, if exists in original filename.

        Returns:
            str: Filename extension.
        """
        _, extension = os.path.splitext(self._full_filename)
        return extension
    
    @property
    def rom_name(self):
        """
        Returns clean ROM name.

        Returns:
            str: ROM name without tags or extension.
        """
        

        filename, _ = os.path.splitext(self._full_filename)
        filename = os.path.basename(filename)
        clean_name = re.sub(r'\s*[(\[].*?[)\]]', '', filename).strip()

        return clean_name
        
