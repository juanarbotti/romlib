
import os
import sqlite3
from sqlite3 import Error
from .errors import ElementNotFound, InvalidROMFile, UnsupportedROMError
from .tags import Semantics, Tags

from .roms import ROMDetector, ROM

class Database:

    _conn = None

    META_SMD_FIELDS = [
        ("system_type", "CHAR(32)"),
        ("copyright_release_date", "CHAR(32)"),
        ("title_domestic", "CHAR(96)"),
        ("title_overseas", "CHAR(96)"),
        ("serial_number_full", "CHAR(28)"),
        ("software_type", "CHAR(16)"),
        ("serial_number", "CHAR(16)"),
        ("revision", "CHAR(8)"),
        ("checksum", "CHAR(8)"),
        ("supported_devices", "CHAR(240)"),
        ("rom_size", "CHAR(16)"),
        ("ram_size", "CHAR(16)"),
        ("extra_memory_available", "CHAR(24)"),
        ("extra_memory_type", "CHAR(8)"),
        ("extra_memory_sram_type", "CHAR(8)"),
        ("extra_memory_sram_saves", "CHAR(8)"),
        ("extra_memory_size", "CHAR(8)"),
        ("modem_support", "CHAR(8)"),
        ("region", "CHAR(8)")
    ]

    META_SMS_FIELDS = [
        ("header_start_byte", "CHAR(6)"),
        ("sega_copyright", "CHAR(8)"),
        ("checksum", "CHAR(6)"),
        ("product_code", "CHAR(6)"),
        ("revision", "CHAR(2)"),
        ("region", "CHAR(16)"),
        ("size", "CHAR(16)")
    ]

    META_SMS_CODEMASTERS_FIELDS = [
        ("cm_n_banks", "CHAR(16)"),
        ("cm_compilation_date_time", "CHAR(16)"),
        ("cm_checksum", "CHAR(6)"),
        ("cm_inverse_checksum", "CHAR(6)")
    ]

    META_SNES_FIELDS = [
        ("title", "CHAR(46)"),
        ("map_mode", "CHAR(8)"),
        ("cpu_clock", "CHAR(8)"),
        ("cartridge_type","CHAR(16)"),
        ("coprocesor", "CHAR(16)"),
        ("rom_size", "CHAR(16)"),
        ("ram_size", "CHAR(16)"),
        ("destination_country_code","CHAR(16)"),
        ("developer_id_present", "CHAR(8)"),
        ("mask_rom_version","CHAR(8)"),
        ("checksum_complement","CHAR(8)"),
        ("checksum","CHAR(8)"),
        ("maker_code","CHAR(8)"),
        ("game_code","CHAR(8)"),
        ("expansion_ram_size","CHAR(116)"),
        ("special_version", "CHAR(8)"),
        ("cartridge_subnumber", "CHAR(8)")
    ]

    META_NES_FIELDS = [
        ("romfile_type", "CHAR(8)"),
        ("PRG_ROM_size", "CHAR(16)"),
        ("CHR_ROM_size", "CHAR(16)"),
        ("nametable_arrangement", "CHAR(32)"),
        ("persistent_memory", "CHAR(4)"),
        ("_512_byte_trainer", "CHAR(4)"),
        ("alternative_nametable", "CHAR(4)"),
        ("vs_unisystem", "CHAR(4)"),
        ("playchoice_10", "CHAR(4)"),
        ("tv_system", "CHAR(32)"),
        ("mapper_number", "CHAR(32)"),
        ("mapper", "CHAR(64)"),
        ("sub_mapper_number", "CHAR(32)"),
        ("console_type", "CHAR(8)"),
        ("PRG_RAM_size", "CHAR(16)"),
        ("PRG_NVRAM_size", "CHAR(16)"),
        ("CHR_RAM_size", "CHAR(16)"),
        ("CHR_NVRAM_size", "CHAR(16)"),
        ("VS_PPU_type", "CHAR(8)"),
        ("VS_hardware_type", "CHAR(8)"),
        ("extended_console_type", "CHAR(8)"),
        ("miscellaneus_roms", "CHAR(8)"),
        ("default_expansion_device", "CHAR(8)")
    ]
    
    def __init__(self, sqlite3_path):

        self._conn = sqlite3.connect(sqlite3_path)
        # Activar claves foráneas
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.row_factory = sqlite3.Row

        self.create_tables()

    def _executor_write(self, transaction, params):
        try:
            with self._conn:
                cursor= self._conn.cursor()
                cursor.execute(transaction, params)
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error inserting record: {str(e)}")
            
    def create_tables(self):

        sql_table_roms = """
            CREATE TABLE IF NOT EXISTS roms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                romfile TEXT NOT NULL UNIQUE,
                system CHAR(8) NOT NULL,
                clean_name TEXT NOT NULL,
                hash CHAR(64) NOT NULL
            );
        """

        #########################
        ########## SMS ##########
        #########################
         
        sql_table_meta_sms = f"""
            CREATE TABLE IF NOT EXISTS meta_sms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER UNIQUE NOT NULL,
                {",".join([f"{i[0]} {i[1]}" for i in self.META_SMS_FIELDS])},
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """
        sql_table_meta_sms_codemasters = f"""
            CREATE TABLE IF NOT EXISTS meta_sms_codemasters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meta_sms_id INTEGER UNIQUE NOT NULL,
                {",".join([f"{i[0]} {i[1]}" for i in self.META_SMS_CODEMASTERS_FIELDS])},
                FOREIGN KEY (meta_sms_id) REFERENCES meta_sms(id) ON DELETE CASCADE
            );
        """

        #########################
        ########## SMD ##########
        #########################

        sql_table_meta_smd = f"""
            CREATE TABLE IF NOT EXISTS meta_smd (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER UNIQUE NOT NULL,
                {",".join([f"{i[0]} {i[1]}" for i in self.META_SMD_FIELDS])},
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """
        #########################
        ########## NES ##########
        #########################
        
        sql_table_meta_nes = f"""
            CREATE TABLE IF NOT EXISTS meta_nes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER UNIQUE NOT NULL,
                {",".join([f"{i[0]} {i[1]}" for i in self.META_NES_FIELDS])},
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """

        #########################
        ########## SNES #########
        #########################

        sql_table_meta_snes = f"""
            CREATE TABLE IF NOT EXISTS meta_snes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER UNIQUE NOT NULL,
                {",".join([f"{i[0]} {i[1]}" for i in self.META_SNES_FIELDS])},
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """
     
        ############
        ### TAGS ###
        ############

        # Standard
        sql_table_tags_standard = f"""
            CREATE TABLE IF NOT EXISTS tags_standard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER NOT NULL,
                tag CHAR(64),
                value CHAR(64),
                short_desc CHAR(128),
                short_desc_spa CHAR(128),
                extra_data CHAR(128),
                raw_detection CHAR(128),
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """

        # Universal
        sql_table_tags_universal = f"""
            CREATE TABLE IF NOT EXISTS tags_universal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER NOT NULL,
                tag CHAR(64),
                value CHAR(64),
                short_desc CHAR(128),
                short_desc_spa CHAR(128),
                extra_data CHAR(128),
                raw_detection CHAR(128),
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """

        # System specific
        sql_table_tags_system = f"""
            CREATE TABLE IF NOT EXISTS tags_system (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER NOT NULL,
                tag CHAR(64),
                value CHAR(64),
                short_desc CHAR(128),
                short_desc_spa CHAR(128),
                extra_data CHAR(128),
                raw_detection CHAR(128),
                system CHAR(8),
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """

        # Country
        sql_table_tags_country = f"""
            CREATE TABLE IF NOT EXISTS tags_country (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rom_id INTEGER NOT NULL,
                tag CHAR(64),
                country CHAR(120),
                country_spa CHAR(120),
                preferred CHAR(10),
                raw_detection CHAR(128),
                official CHAR(3),
                FOREIGN KEY (rom_id) REFERENCES roms(id) ON DELETE CASCADE
            );
        """

        # Creates cursor
        c = self._conn.cursor()
        
        ### INDICES ###
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_meta_sms_rom_id ON meta_sms(rom_id);",
            "CREATE INDEX IF NOT EXISTS idx_meta_sms_codemasters_meta_sms_id ON meta_sms_codemasters(meta_sms_id);",
            "CREATE INDEX IF NOT EXISTS idx_meta_smd_rom_id ON meta_smd(rom_id);",
            "CREATE INDEX IF NOT EXISTS idx_meta_nes_rom_id ON meta_nes(rom_id);",
            "CREATE INDEX IF NOT EXISTS idx_meta_snes_rom_id ON meta_snes(rom_id);",
            "CREATE INDEX IF NOT EXISTS idx_tags_standard_rom_id ON tags_standard(rom_id);",
            "CREATE INDEX IF NOT EXISTS idx_tags_universal_rom_id ON tags_universal(rom_id);",
            "CREATE INDEX IF NOT EXISTS idx_tags_system_rom_id ON tags_system(rom_id);",
            "CREATE INDEX IF NOT EXISTS idx_tags_country_rom_id ON tags_country(rom_id);"
        ]

        #Main rom table
        c.execute(sql_table_roms)

        # SMS data
        c.execute(sql_table_meta_sms)
        c.execute(sql_table_meta_sms_codemasters)

        # SMD data
        c.execute(sql_table_meta_smd)

        # NES data
        c.execute(sql_table_meta_nes)

        # SNES data
        c.execute(sql_table_meta_snes)

        # TAGS
        c.execute(sql_table_tags_standard)
        c.execute(sql_table_tags_universal)
        c.execute(sql_table_tags_system)
        c.execute(sql_table_tags_country)

        # Indexes
        for index in indexes:
            c.execute(index)

        self._conn.commit()

    def add_rom_full(self, rom_path, default_system="unknown"):
        """
        Process a ROM file and stores its metadata and tags information in database.

        Args:
            rom_path (str): path to ROM file.
            default_system: overrides ROMDetector information about system type.
        """

        # Loads ROM as object
        try:
            romObj = ROMDetector.load(rom_path)
        except InvalidROMFile:
            # Can't load because was not detected correctly
            romObj = None
        except UnsupportedROMError:
            # Can't load because file was detected, but not supported
            romObj = None
        
        # If rom has system_type
        if romObj:
            # If deault_system is specified, then overrides the rom_obj system type.
            system_type = romObj.system_type if default_system == "unknown" else default_system
        else:
            # ROM has no system type (dummy object), tryes to specify from defaul_system
            system_type = default_system
        
        sql = '''INSERT INTO roms(romfile, system, clean_name, hash)
                VALUES(?,?,?,?)'''
        
        basename = os.path.basename(rom_path)
        clean_name = Semantics.remove_tags(basename)

        if romObj:
            sha3 = romObj.get_sha3()
        else:
            dummyObj = ROM()
            sha3 = dummyObj.get_sha3(rom_path)
        
        inserted_id = self._executor_write(sql, (basename, system_type, clean_name, sha3))
        
        if inserted_id:

            # Adds metadata from ROM (headers)
            if romObj:
                if romObj.system_type == "SMS":
                    self._add_metadata_sms(rom_id=inserted_id, romObj=romObj)
                elif romObj.system_type == "SMD":
                    self._add_metadata(rom_id=inserted_id, romObj=romObj, items_set=self.META_SMD_FIELDS)
                elif romObj.system_type == "NES":
                    self._add_metadata(rom_id=inserted_id, romObj=romObj, items_set=self.META_NES_FIELDS)
                elif romObj.system_type == "SNES":
                    self._add_metadata(rom_id=inserted_id, romObj=romObj, items_set=self.META_SNES_FIELDS)

            # Adds tags
            self._scan_tags(inserted_id)

        return inserted_id

    def tag_stored_roms(self):
        """
        Generate tags from ROMs stored in database.
        Warning: if you run this twice, you will ruin database.
        """

        sql = f"""
            SELECT id FROM roms
        """
        rows = None
        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
        
        for row in rows:
            self._scan_tags(row["id"])

    def _add_metadata_sms(self, rom_id, romObj):
        """
        Stores specific SMS metadata (header information) in database.
        This specific method for SMS is because some ROMs contain Codemasters header (stored in meta_sms_codemasters table.)

        Args:
            rom_id (int): ROM's ID from table "roms"
            romObj (ROM): loaded ROM object file.

        Returns:
            int: metadata ID from table meta_sms. It will no return meta_sms_codemasters ID if information was stored in it.
        """

        meta_id = self._add_metadata(rom_id=rom_id, romObj=romObj, items_set=self.META_SMS_FIELDS)

        if romObj.pretty_data["codemasters_header_present"] == "yes":
        
            params = [meta_id] + [item for key, item in romObj.pretty_data.items() if key.startswith("cm_")]

            columns = [key for key in romObj.pretty_data.keys() if key.startswith("cm_")]

            n_items = ",".join(["?"] * (len(columns) + 1))

            columns = ",".join(columns)

            sql = "INSERT INTO meta_sms_codemasters(meta_sms_id, {columns}) VALUES({n_items})".format(
                columns=columns, 
                n_items=n_items
                )
                        
            _ = self._executor_write(sql, params)

        return meta_id

    def _add_metadata(self, rom_id, romObj, items_set):

        data = romObj.pretty_data

        # Set romtype
        romtype = romObj.system_type.lower()

        columns = []
        params = []
        for item in items_set:

            key = item[0].lstrip("_")
            key_no_strip = item[0]

            if key in data:
                columns.append(key_no_strip)
                params.append(data[key])

        
        n_items = ",".join(["?"] * (len(columns) + 1))

        # Add rom_id to params
        params = [rom_id] + params

        # Join columns
        columns = ",".join(columns)

        sql = f"INSERT INTO meta_{romtype}(rom_id, {columns}) VALUES({n_items})"

        id_metadata = self._executor_write(sql, params)

        return id_metadata
    
    def _get_rom(self, rom_id):
        sql = f"""
            SELECT id, romfile, system FROM roms WHERE id=?
        """
        params = (rom_id,)
        row = None
        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
        return row

    def _scan_tags(self, rom_id):
        
        row = self._get_rom(rom_id)
        tagObj = Tags(filename=row["romfile"], rom_type=row["system"])

        if row:
            self._scan_tags_standard(rom_id, tagObj)
            self._scan_tags_universal(rom_id, tagObj)
            self._scan_tags_system(rom_id, tagObj)
            self._scan_tags_country(rom_id, tagObj)

    def _scan_tags_standard(self, rom_id, tagObj):

        list_ids = []
        for tags in tagObj.gc_standard:
            columns = ",".join(list(tags.keys()))
            params = [rom_id] + list(tags.values())

            n_items = ",".join(["?"] * len(params))

            sql = f"""INSERT INTO tags_standard(rom_id,{columns}) VALUES({n_items})"""

            list_ids.append(self._executor_write(sql, params))
        
        return list_ids

    def _scan_tags_universal(self, rom_id, tagObj):
        
        list_ids = []
        for tags in tagObj.gc_universal:
            columns = ",".join(list(tags.keys()))
            params = [rom_id] + list(tags.values())

            n_items = ",".join(["?"] * len(params))

            sql = f"""INSERT INTO tags_universal(rom_id,{columns}) VALUES({n_items})"""

            list_ids.append(self._executor_write(sql, params))
        return list_ids
    
    def _scan_tags_system(self, rom_id, tagObj):
        
        list_ids = []
        for tags in tagObj.gc_universal:
            columns = ",".join( list(tags.keys()) + ["system"] )
            params = [rom_id] + list(tags.values()) + [tagObj.rom_type]

            n_items = ",".join(["?"] * len(params))

            sql = f"""INSERT INTO tags_system(rom_id,{columns}) VALUES({n_items})"""

            list_ids.append(self._executor_write(sql, params))
        return list_ids
    
    def _scan_tags_country(self, rom_id, tagObj):
        
        list_ids = []
        for tags in tagObj.gc_country:
            columns = ",".join( list(tags.keys()) + ["official"] )
            params = [rom_id] + list(tags.values()) + ["yes"]

            n_items = ",".join(["?"] * len(params))

            sql = f"""INSERT INTO tags_country(rom_id,{columns}) VALUES({n_items})"""

            list_ids.append(self._executor_write(sql, params))

        list_ids = []
        for tags in tagObj.gc_country_unofficial:
            columns = ",".join( list(tags.keys()) + ["official"] )
            params = [rom_id] + list(tags.values()) + ["no"]

            n_items = ",".join(["?"] * len(params))

            sql = f"""INSERT INTO tags_country(rom_id,{columns}) VALUES({n_items})"""

            list_ids.append(self._executor_write(sql, params))
        return list_ids
        
# Available elements to be imported
__all__ = ["Database"]

# Only show available
def __dir__():
    return __all__

# Rasie an error if someone wants to import dependencies
def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"Module 'romlib.db' has no attribute '{name}'")
    return globals()[name]