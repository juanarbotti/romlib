import os
import shutil
from pathlib import Path
import unicodedata
import py7zr
import zipfile
import time
import json
from hashlib import sha3_256

from . import errors


class ROM:

    # Full path of loaded ROM
    _full_path = None

    # The information storage for the ROM
    _data = {}

    # Variable to store the ROM type class
    _system_type = None

    def __init__(self, full_path=None):
        """
        Generic ROM class manager.
        """
        # Load data
        if full_path != None:
            self._load(full_path)
            
    def load(self, full_path):
        self._clear()
        self._full_path = full_path
        self._load(full_path)

    def _load(self, full_path):
        pass

    def _clear(self):
        self._full_path = None
        self._data = {}
        self._system_type = None
    
    def advanced_text_decode(self, data):
        for encoding in ["ascii", "shift_jis", "euc-jp", "utf-8"]:
            try:
                
                # Tries to decode
                decoded_data = data.decode(encoding)
                
                # Clean null characters
                decoded_data = decoded_data.replace("\x00", "")

                # Convert Half-Width Katakana a Full-Width
                decoded_data = unicodedata.normalize("NFKC", decoded_data)
                
                return decoded_data
            
            except UnicodeDecodeError:
                continue
        
        # If could not decode, then goes to standar utf-8 and replace trash characters, ignoring errors
        return data.replace(b"\x00", b"").decode("utf-8", errors="ignore")

    def get_sha3(self, full_path=None):
        file_objective = self._full_path if not full_path else full_path
        hasher = sha3_256()
        try:
            with open(file_objective, "rb") as f:
                while chunk := f.read(4096):  # Leer en bloques de 4KB
                    hasher.update(chunk)
        except:
            return
        
        return hasher.hexdigest()


    @property
    def pretty_data(self):
        """
        Returns processed and human-friendly data.
        """
        pass

    @property
    def pretty_data_json(self):
        return json.dumps(self.pretty_data,indent=4)
    
    @property
    def raw_data(self):
        """
        Returns raw ROM data read from ROM file.
        """
        return self._data
    
    @property
    def full_path(self):
        return self._full_path
    
    @property
    def system_type(self):
        return self._system_type

    # Helper function for safe operations
    def _safe_get(self, func, *args, default="unknown"):
        try:
            return func(*args)
        except:
            return default

class ROM_SMS(ROM):

    # SMS Region codes
    REGION_CODE = {
        0x3: "SMS Japan",
        0x4: "SMS Export",
        0x5: "GG Japan",
        0x6: "GG Export",
        0x7: "GG International"
    }

    # ROM sizes
    ROM_SIZE = {
        0xa: "8 KB",
        0xb: "16 KB",
        0xc: "32 KB",	 
        0xd: "48 KB",
        0xe: "64 KB",
        0xf: "128 KB",
        0x0: "256 KB",	 
        0x1: "512 KB",
        0x2: "1 MB"
    }

    # Possible header positions, 0x7FF0 is more likle to be
    HEADERS_POSITIONS = [0x1FF0, 0x3FF0, 0x7FF0]

    # Variable to store header position
    _header_position = None 

    # Comdemasters header vars
    _data_codemasters = [bytes(16)] # creates an empty Codemasters' header
    _cm_header = False # sets default no Codemasters' header
    _cm_checksum = None # stores checksum on load
    _cm_inverse_checksum = None # stores inverse checsum on load

    def __init__(self, full_path=None):
        super().__init__(full_path=full_path)
        
        self._system_type = "SMS"
        
        if full_path != None:
            self._load(full_path)

    def _load(self, full_path):
        
        with open(full_path, "rb") as f:
            
            # SMS header can be in different positions, so it will scan for header in them
            for start_byte in self.HEADERS_POSITIONS:
                f.seek(start_byte)
                data = f.read(16)
                try:
                    if data[:8].decode("utf-8") == "TMR SEGA":
                        self._header_position = start_byte
                        break
                except:
                    pass
            
            # Inexistent header. Old games, like SG, sometimes does not have headers
            if self._header_position == None:
                self._clear()
                raise errors.InvalidROMFile(f"File {full_path} is proably an old SMS ROM or not a SMS ROM or maybe file is corrupted.")
            else:
                self._data = data # Header present, load the 16 bytes read
                self._full_path = full_path # Sets the full path file

            # If a SEGA header is present, verify for codemasters extra header
            if self._header_position != None:
                
                # to check CM's header, first seeks for CM's header's position
                # and read 16 bytes from there.
                f.seek(0x7FE0)
                cm_data = f.read(16)

                # Then gets the checksum and inverse checksum values
                checksum = int.from_bytes(cm_data[6:8], "little")
                inverse_checksum = int.from_bytes(cm_data[8:10], "little")

                # Verify checsum against inverse checksum. If ckecusm matches, then asumes a CM's header present
                if inverse_checksum == (0x10000 - checksum):
                    # stores information
                    self._cm_header = True
                    self._data_codemasters = cm_data
                    self._cm_checksum = checksum
                    self._cm_inverse_checksum = inverse_checksum

    @property
    def pretty_data(self):

        # Intialize SMS header values
        data = {
            "loaded_class": "SMS",
            "header_present": "yes" if self._header_position else "no", # Some games does not have headers
            "header_start_byte": "not found" if self._header_position == None else f"0x{self._header_position:04X}", # Header position may vary
            "codemasters_header_present": "yes" if self._cm_header else "no", # Codemasters roms have their own addtional header
            "sega_copyright": "unknown",
            "checksum": "unknown",
            "product_code": "unknown",
            "revision": "unknown",
            "region": "unknown",
            "size": "unknown",
        }

        # If header is presente, then reads and process values
        if data["header_present"] == "yes":

            # The 'TMR SEGA' message
            try:
                data["sega_copyright"] = self.advanced_text_decode(self._data[:8])
            except UnicodeDecodeError:
                data["sega_copyright"] = "invalid"

            # Checksum
            checksum = int.from_bytes(self._data[10:12], "little")
            data["checksum"] = f"0x{checksum:04X}"

            # Product code
            try:
                byte12 = self._data[12]  # Ej: 0x26
                byte13 = self._data[13]  # Ej: 0x70
                byte14_high = self._data[14] >> 4  # High bits D4-D7
                # Put bytes in correct order and represent as integer (byte13, first part, byte12 second part)
                bcd_part = f"{byte13:02X}{byte12:02X}"  # "7026" (0x70 0x26 -> "7026")
                # If byte14 high is present (not zero), represents the first digits of the code
                full_code = f"{byte14_high}{bcd_part}" if byte14_high != 0 else bcd_part
                data["product_code"] = str(full_code)
            except:
                data["product_code"] = "invalid"

            # Revision:
            try:
                byte_14_low = self._data[14] & 0b00001111
                data["revision"] = f"{byte_14_low:02d}" # Force 2 digits, for example 00 for 0
            except:
                data["revision"] = "invalid"

            try:
                # Region code
                byte_15_high = self._data[15] >> 4
                data["region"] = self.REGION_CODE.get(byte_15_high, "unknown")
            except:
                data["region"] = "invalid"

            try:   
                # ROM size informed
                byte_15_low = self._data[15] & 0b00001111
                data["size"] = self.ROM_SIZE.get(byte_15_low, "unknown")
            except:
                data["size"] = "invalid"

        # If CM's ROM, then gets and process CM's header's data.
        if data["codemasters_header_present"] == "yes":

            # Number of 16 kb banks
            data["cm_n_banks"] = self._data_codemasters[0]
            
            # Date, month, year and time of compilation
            day = f"{self._bcd_to_decimal(self._data_codemasters[1]):02d}"
            month = f"{self._bcd_to_decimal(self._data_codemasters[2]):02d}"
            year = f"{self._bcd_to_decimal(self._data_codemasters[3]):02d}"
            hour = f"{self._bcd_to_decimal(self._data_codemasters[4]):02d}"
            minute = f"{self._bcd_to_decimal(self._data_codemasters[5]):02d}"
            data["cm_compilation_date_time"] = f"{year}-{month}-{day} {hour}:{minute}"

            # Checksum and inverse checksum
            data["cm_checksum"] = f"0x{self._cm_checksum:04X}"
            data["cm_inverse_checksum"] = f"0x{self._cm_inverse_checksum:04X}"
        
        return data

    def _clear(self):
        self._full_path = None
        self._data = {}
        self._system_type = None

        # Variable to store header position
        self._header_position = None 

        # Comdemasters header vars
        self._data_codemasters = [bytes(16)] # creates an empty Codemasters' header
        self._cm_header = False # sets default no Codemasters' header
        self._cm_checksum = None # stores checksum on load
        self._cm_inverse_checksum = None # stores inverse checsum on load

    def _bcd_to_decimal(self, bcd_byte):
        """Converts BCD into decimal."""
        return ((bcd_byte >> 4) * 10) + (bcd_byte & 0x0F)

    @property
    def header_position(self):
        """
        Returns:
            str: header position in hex format notation. Will return None if no header found.
        """
        return f"0x{self._header_position:04X}" if self._header_position != None else ""
    
    @property
    def raw_data_codemasters(self):
        """
        Returns
            list[bytes] : 16 bytes from Codemasters' Header. Will be al zeros if no Codemasters' header is present.
        """
        return self._data_codemasters
    
    def _calculate_checksum(header_start_byte, full_path):
        """
        Calculates SEGA's header checksum.

        Args:
            heade_start_byte: ROM header start byte.
            full_path: ROM file full path.

        Returns:

        """
        with open(full_path, "rb") as f:
            rom_data = f.read()  # Read the full ROM
            rom_body = rom_data[:header_start_byte] + rom_data[header_start_byte + 16:] # Gets only the body and excludes header
            calculated_checksum = sum(rom_body) & 0xFFFF  # Sums rom_body bytes and then applys 16 bits mask
            return calculated_checksum

class ROM_SMD(ROM):

    TYPES_SMD = {
        "SEGA": "Sega game",
        "SEGA MEGA DRIVE":	"Mega Drive",
        "SEGA GENESIS":	"Mega Drive",
        "SEGA 32X": "Mega Drive + 32X",
        "SEGA EVERDRIVE": "Mega Drive (Everdrive extensions)",
        "SEGA SSF": "Mega Drive (Mega Everdrive extensions)",
        "SEGA MEGAWIFI": "Mega Drive (Mega Wifi extensions)",
        "SEGA PICO": "Pico",
        "SEGA TERA68K": "Tera Drive (boot from 68000 side)",
        "SEGA TERA286": "Tera Drive (boot from x86 side)"
    }

    SOFTWARE_TYPE = {
        "GM": "Game",
        "AI": "Aid",
        "OS": "Boot ROM (TMSS)",
        "BR": "Boot ROM (Sega CD)"
    }

    SUPPORTED_DEVICES = {
        "J":"3-button controller",
        "6":"6-button controller",
        "0":"Master System controller",
        "A":"Analog joystick",
        "4":"Multitap",
        "G":"Lightgun",
        "L":"Activator",
        "M":"Mouse",
        "B":"Trackball",
        "T":"Tablet",
        "V":"Paddle",
        "K":"Keyboard or keypad",
        "R":"RS-232",
        "P":"Printer",
        "C":"CD-ROM (Sega CD)",
        "F":"Floppy drive",
        "D":"Download?" 
    }

    EXTRA_SRAM_TYPES = {
        0xA0: ("No","16-bit"),
        0xB0: ("No","8-bit (even addresses)"),
        0xB8: ("No","8-bit (odd addresses)"),
        0xE0: ("Yes","16-bit"),
        0xF0: ("Yes","8-bit (even addresses)"),
        0xF8: ("Yes","8-bit (odd addresses)") 
    }
    
    REGION_SYSTEMS = {
        "J": "NTSC-J",
        "U": "NTSC-U",
        "E": "PAL"
    }

    REGION_SYSTEMS_1995 = {
        "0": "hardware incompatible",
        "1": "NTSC-J",
        "4": "NTSC-U",
        "8": "PAL",
        "F": "region free"
    }

    def __init__(self, full_path=None):
        super().__init__(full_path)
        
        self._system_type = "SMD"
        
        if full_path != None:
            self._load(full_path)
        
    def _load(self, full_path):

        with open(full_path, "rb") as f:
            f.seek(0x100)
            data = f.read(256)

        invalid_rom_error =  errors.InvalidROMFile(f"File {full_path} is proably not a {self._system_type} ROM or file is corrupted.")
        try:
            if data[0:4].decode("ascii") != "SEGA":
                self._clear()
                raise invalid_rom_error
        except:
            self._clear()
            raise invalid_rom_error
    
        self._data = data
        self._full_path = full_path


    @property
    def pretty_data(self):

        # prepare exit dictionary
        data = {
            "loaded_class": "SMD",
            "system_type": "unknown",
            "copyright_release_date": "unknown",
            "title_domestic": "unknown",
            "title_overseas": "unknown",
            "serial_number_full": "unknown",
            "software_type": "unknown",
            "serial_number": "unknown",
            "revision": "unknown",
            "checksum": "unknown",
            "supported_devices": "unknown",
            "rom_size": "unknown",
            "ram_size": "unknown",
            "extra_memory_available": "unknown",
            "modem_support": "unknown",
            "region": "unknown"
        }

        # Set system type. If fails, then stops and returns unknown type (not a valid SMD ROM) (16 bytes)
        data["system_type"] = self._safe_get(lambda: self._data[0:16].decode("utf-8").strip())
        
        # Copyright and release date (16 bytes)
        data["copyright_release_date"] = self._safe_get(lambda: self._data[16:32].decode("utf-8").strip())
        
        # Domestic title (48 bytes)
        data["title_domestic"] = self._safe_get(lambda: self.advanced_text_decode(self._data[32:80]).strip())
        
        # Title overseas (48 bytes)
        data["title_overseas"] = self._safe_get(lambda: self.advanced_text_decode(self._data[80:128]).strip())
        
        # Full serial number data '[cartrdige code] [serial number]-[revision]" (14 bytes)
        data["serial_number_full"] = self._safe_get(lambda: self._data[128:142].decode("utf-8").strip())
        
        if data["serial_number_full"] != "unknown":
            # Software type, serial number and revision, derivated from the full serial number
            data["software_type"] = self.SOFTWARE_TYPE.get(data["serial_number_full"][0:2], "unknown")
            data["serial_number"] = data["serial_number_full"][2:-2].replace("-"," ").strip()
            data["revision"] = data["serial_number_full"][-2:]

        # Checksum (2 bytes)
        data["checksum"] = self._safe_get(lambda: ' '.join(f'0x{byte:02X}' for byte in self._data[142:144]))
        
        # Supported devices (16 byres)
        supported_devices = self._safe_get(lambda: self._data[144:160].decode("utf-8").strip())
        if supported_devices != "unknown":
            devices_lst = []
            for dev in supported_devices:
                element = self.SUPPORTED_DEVICES.get(dev, "unrecognized device")
                devices_lst.append(element)
            data["supported_devices"] = ", ".join(devices_lst) if len(devices_lst) > 0 else "no device found"

        # ROM size (8 byes)
        try:
            bytes_4 = self._safe_get(lambda: self._data[160:168][-4:])
            if bytes_4 != "unknown":
                if len(bytes_4) == 4: 
                    int_value = int.from_bytes(bytes_4, byteorder='big')
                    rom_size_mb = (int_value + 1) // 1024
                    data["rom_size"] = f"{rom_size_mb} KB"
                else:
                    data["rom_size"] = "unknown"
        except Exception as e:
            data["rom_size"] = f"unknown"
        
        # RAM size (8 byes)
        ram_start_bytes = self._safe_get(lambda: self._data[168:172])
        ram_end_bytes = self._safe_get(lambda: self._data[172:176])
        
        if ram_start_bytes != "unknown" and ram_end_bytes != "unknown":
            if len(ram_start_bytes) == 4 and len(ram_end_bytes) == 4:
                ram_start = int.from_bytes(ram_start_bytes, byteorder="big")
                ram_end = int.from_bytes(ram_end_bytes, byteorder="big")

                ram_size = (ram_end - ram_start) + 1 
                ram_size_kb = ram_size // 1024 

                if ram_size_kb >= 1024:
                    ram_size_mb = round(ram_size / (1024 * 1024), 1)
                    data["ram_size"] = f"{ram_size_mb} MB"
                else:
                    data["ram_size"] = f"{ram_size_kb} KB"
            else:
                data["ram_size"] = "undetermined"


        # Extra Memory (SRAM or EEPROM)
        extra_memory = self._safe_get(lambda: self._data[176:188])

        if extra_memory != "uknown":
            if extra_memory[0:2] != b'RA':
                data["extra_memory_available"] = "no"
            else:
                data["extra_memory_available"] = "yes"
                
                # Type SRAM
                if extra_memory[2] in self.EXTRA_SRAM_TYPES.keys():

                    # Set type to SRAM and check wich type uses and if it cappable to save
                    data["extra_memory_type"] = "SDRAM"
                    data["extra_memory_sram_type"] = self.EXTRA_SRAM_TYPES.get(extra_memory[2])[1]
                    data["extra_memory_sram_saves"] = self.EXTRA_SRAM_TYPES.get(extra_memory[2])[0]
                    
                    # Calculates SRAM size, based on informed starting and ending addresses
                    sram_start = int.from_bytes(extra_memory[4:8], byteorder="big")
                    sram_end = int.from_bytes(extra_memory[8:12], byteorder="big")

                    sram_size = (sram_end - sram_start) + 1  
                    if sram_size > 1024:
                        data["extra_memory_size"] = f"{sram_size // 1024} KB"
                    else:
                        data["extra_memory_size"] = f"{sram_size} bytes"

                # Type EEPROM: seems not possible to calculate EEPROM size, it is not informed in header
                elif extra_memory[2] == 0xE8:
                    data["extra_memory_type"] = "EEPROM"

        # Modem (only detection, no more data shown)
        # TO DO: extra information about modem
        mdm = self._data[188:200]
        data["modem_support"] = self._safe_get(lambda: "yes" if mdm.strip() != b'' else "no" )
        

        try:
            region_bytes = self._data[240:243]
            region = region_bytes.decode("ascii").strip()
            
            regions_list = []
            for chr_reg in region:
                region_val = self.REGION_SYSTEMS.get(chr_reg, None)
                if region_val != None:
                    regions_list.append(region_val)
            regions_str = "region free" if len(regions_list) == 3 else ", ".join(regions_list).strip()
            
            if regions_str == "":
                data["region"] = self.REGION_SYSTEMS_1995.get(region[0], "unrecognized")
            else:
                data["region"] = regions_str
        except:
            data["region"] = "unknown"
        return data

class ROM_NES(ROM):

    # Mappers
    MAPPERS = {
        0: "NROM",
        1: "SxROM, MMC1",
        2: "UxROM",
        3: "CNROM",
        4: "TxROM, MMC3, MMC6",
        5: "ExROM, MMC5",
        7: "AxROM",
        9: "PxROM, MMC2",
        10: "FxROM, MMC4",
        11: "Color Dreams",
        13: "CPROM",
        15: "100-in-1 Contra Function 16",
        16: "Bandai EPROM (24C02)",
        18: "Jaleco SS8806",
        19: "Namco 163",
        21: "VRC4a, VRC4c",
        22: "VRC2a",
        23: "VRC2b, VRC4e",
        24: "VRC6a",
        25: "VRC4b, VRC4d",
        26: "VRC6b",
        34: "BNROM, NINA-001",
        64: "RAMBO-1",
        66: "GxROM, MxROM",
        68: "After Burner",
        69: "FME-7, Sunsoft 5B",
        71: "Camerica/Codemasters",
        73: "VRC3",
        74: "Pirate MMC3 derivative",
        75: "VRC1",
        76: "Namco 109 variant",
        79: "NINA-03/NINA-06",
        85: "VRC7",
        86: "JALECO-JF-13",
        94: "Senjou no Ookami",
        105: "NES-EVENT",
        113: "NINA-03/NINA-06??",
        118: "TxSROM, MMC3",
        119: "TQROM, MMC3",
        159: "Bandai EPROM (24C01)",
        166: "SUBOR",
        167: "SUBOR",
        180: "Crazy Climber",
        185: "CNROM with protection diodes",
        192: "Pirate MMC3 derivative",
        206: "DxROM, Namco 118 / MIMIC-1",
        210: "Namco 175 and 340",
        228: "Action 52",
        232: "Camerica/Codemasters Quattro"
    }

    # Submappers
    SUB_MAPPERS = {
        0: "Normal",
        1: "Waixing VT03",
        2: "Power Joy Supermax",
        3: "Zechess/Hummer Team",
        4: "Sports Game 69-in-1",
        5: "Waixing VT02",
        12: "Cheertone",
        13: "Cube Tech",
        14: "Karaoto",
        15: "Jungletac"
    }

    # List of Mappers that does not support submappers
    NO_SUBMAPPERS = {
                0, 2, 3, 7, 11, 13, 15, 16, 18, 21, 22, 23, 24, 25, 26, 34, 64, 66,
                68, 71, 73, 74, 75, 76, 79, 86, 94, 105, 113, 159, 166, 167, 180, 185, 192, 206, 228
            }

    CONSOLE_TYPE = {
        0: "Nintendo Entertainment System",
        1: "Nintendo Vs. System",
        2: "Nintendo Playchoice 10",
        3: "Extended console type",
    }

    CPU_PPU_TIMINGS = {
        0: "RP2C02 (NTSC NES)",
        1: "RP2C07 (Licensed PAL NES)",
        2: "Multiple-region",
        3: "UA6538 (Dendy)"
    }

    def __init__(self, full_path=None):
        super().__init__(full_path=full_path)

        self._system_type = "NES"
        
        if full_path != None:
            self._load(full_path)


    def _load(self, full_path):
        
        with open(full_path, "rb") as f:
            data = f.read(16)

        if not data[0:4] == b'NES\x1a':
            self._clear()
            raise errors.InvalidROMFile(f"File {full_path} is proably not a NES ROM or file is corrupted.")
        
        self._data = data
        self._full_path = full_path
        
    @property
    def pretty_data(self):

        if not self._full_path:
            raise errors.NoROMLoaded("No ROM was loaded.")

        pretty_data = {
            "loaded_class": "NES",
            "romfile_type": "unknown",
            "PRG_ROM_size": "unknown",
            "CHR_ROM_size": "unknown",
            "nametable_arrangement": "unknown",
            "persistent_memory": "unknown",
            "512_byte_trainer": "unknown",
            "alternative_nametable": "unknown",
            "vs_unisystem": "unknown",
            "playchoice_10": "unknown",
            "PRG_RAM_size": "unknown",
            "tv_system": "unknown",
            "mapper_number": "unknown",
            "mapper": "unknown"
        }

        # Is a valid iNES file?
        pretty_data["romfile_type"] = self._safe_get(lambda: "iNES" if self._data[0:4] == b'NES\x1a' else "unknown")
        
        # Is NES 2.0?
        is_nes20 = self._safe_get(lambda: (self._data[7] & 0x0C) == 0x08)
        pretty_data["romfile_type"] = self._safe_get(lambda: "NES 2.0"if is_nes20 else pretty_data["romfile_type"])
        

        #if pretty_data["romfile_type"] == "iNES":
        pretty_data = self._read_iNES(pretty_data)

        if pretty_data["romfile_type"] == "NES 2.0":
            pretty_data = self._read_NES2(pretty_data)

        return pretty_data
    
    def _read_iNES(self, data):

        # Read PRG ROM size
        data["PRG_ROM_size"] = str(self._data[4] * 16) + " KB"

        # Read CHR ROM size
        chr_rom_size = "no" if self._data[5] == 0 else str(self._data[5] * 8) + " KB"
        data["CHR_ROM_size"] = chr_rom_size

        # Get flags from byte 6
        nametable_arrangement = (self._data[6] & 0b00000001) >> 0
        data["nametable_arrangement"] = "horizontal (vertically mirrored)" if nametable_arrangement == 1 else "vertical (horizontally mirrored)"
        
        persistent_memory = (self._data[6] & 0b00000010) >> 1
        data["persistent_memory"] = "yes" if persistent_memory == 1 else "no"
        
        trainer = (self._data[6] & 0b00000100) >> 2
        data["512_byte_trainer"] = "yes" if trainer else "no"

        alt_nametable = self._data[6] & 0b00001000
        data["alternative_nametable"] = "yes" if alt_nametable else "no"

        vs_unisystem = (self._data[7] & 0b00000001) >> 0
        playchoice_10 = (self._data[7] & 0b00000010 >> 1)
        data["vs_unisystem"] = "yes" if vs_unisystem == 1 else "no"
        data["playchoice_10"] = "yes" if playchoice_10 == 1 else "no"

        byte_8 = self._data[8]
        data["PRG_RAM_size"] = f"{max(1, byte_8) * 8} KB"

        byte_9 = self._data[9]
        if byte_9 == 0:
            data["tv_system"] = "NTSC"
        elif byte_9 == 1:
            data["tv_system"] = "PAL"
        else:
            data["tv_system"] = "Dual-compatible (NTSC & PAL)"

        # Mapper
        mapper_number = ((self._data[7] & 0b11110000) | (self._data[6] >> 4))
        data["mapper_number"] = mapper_number
        data["mapper"] = self.MAPPERS.get(mapper_number, "unknown")

        return data

    def _read_NES2(self, data):

        # pops out not valid fiels for NES 2.0
        data.pop("alternative_nametable", None)
        data.pop("playchoice_10", None)
        data.pop("vs_unisystem", None)

        data.update({
            "mapper_number": "unknown",
            "mapper": "unknown",
            "submapper_number": "unknown",
            "console_type": "unknown",
            "PRG_RAM_size": "unknown",
            "PRG_NVRAM_size": "unknown",
            "CHR_RAM_size": "unknown",
            "CHR_NVRAM_size": "unknown",
            "tv_system": "unknown",
            "miscellaneus_rom": "unknown",
            "default_expansion_device": "unknown"
        })

        mapper_number = ((self._data[8] & 0b00001111) << 8) | (self._data[7] & 0x11110000) | (self._data[6] >> 4)
        data["mapper_number"] = mapper_number
        data["mapper"] = self.MAPPERS.get(mapper_number, "unknown")

        submapper_number = self._get_submapper(self._data[8], mapper_number)
        data["submapper_number"] = submapper_number if submapper_number != -1 else "not apply"

        console_type = self._data[7] & 0b00000011
        data["console_type"] = self.CONSOLE_TYPE[console_type]

        prg_ram_shift = self._data[10] & 0b00001111  # Bits 3-0 (PPPP)
        prg_nvram_shift = (self._data[10] >> 4) & 0b00001111  # Bits 7-4 (pppp)
        prg_ram = 64 << prg_ram_shift if prg_ram_shift else 0
        prg_nvram_eeprom = 64 << prg_nvram_shift if prg_nvram_shift else 0
        
        data["PRG_RAM_size"] = f"{prg_ram / 1024} KB" if prg_ram != 0 else "8 KB"
        data["PRG_NVRAM_size"] = f"{prg_nvram_eeprom / 1024} KB" if prg_ram != 0  else "not present"

        ram_shift = self._data[11] & 0b00001111  # Bits 3-0 (PPPP)
        nvram_shift = (self._data[11] >> 4) & 0b00001111 # Bits 7-4 (pppp)        
        chr_ram = 64 << ram_shift if ram_shift else 0
        chr_nvram = 64 << nvram_shift if nvram_shift else 0
        data["CHR_RAM_size"] = f"{chr_ram / 1024} KB" if chr_ram != 0 else "not present"
        data["CHR_NVRAM_size"] = f"{chr_nvram / 1024} KB" if chr_nvram != 0 else "not present"

        # Timing modes (bits position 0 and 1)
        vv_bits = self._data[12] & 0b00000011
        data["tv_system"] = self.CPU_PPU_TIMINGS.get(vv_bits, "Unknown timing mode")

        # Vs. system type or Vs. extended console type
        low_nybble = self._data[13] & 0b00001111
        high_nybble = self._data[13] & 0b11110000
        if data["console_type"] == self.CONSOLE_TYPE[1]:
            data["VS_PPU_type"] = low_nybble
            data["VS_hardware_type"] = high_nybble
        elif data["console_type"] == self.CONSOLE_TYPE[3]:
            data["extended_console_type"] = low_nybble

        # Miscellaneus ROMs
        data["miscellaneus_roms"] = int(self._data[14] & 0b00000011)

        # Default expansion device
        data["default_expansion_device"] = int(self._data[15] & 0b00111111)

        return data     

    def _get_submapper(self, byte_8: int, mapper_number: int) -> int:
        """
        Retruns submapper number (0-15) or -1 mapper does not support submappers.
        Args:
            byte_8: Byte 8 from NES 2.0 header.
            mapper_number: Mapper number.
        Returns:
            Submapper (0-15) o -1 if does not apply.
        """
        return -1 if mapper_number in self.NO_SUBMAPPERS else (byte_8 >> 4) & 0b00001111

class ROM_SNES(ROM):

    HEADER_POSITIONS = {
        0x7fb0: "LoROM",
        0xffb0: "HiROM",
        0x40ffb0: "ExHiROM"
    } 
    
    MAP_MODE = {
        0x20: ("Mode 20", "2.68 MHz (normal speed)"),
        0x21: ("Mode 21", "2.68 MHz (normal speed)"),
        0x22: ("Reserved", "Unused?"),
        0x23: ("Mode 23 (SA-1)", "2.68 MHz (normal speed)"),
        0x25: ("Mode 25", "2.68 MHz (normal speed)"),
        0x30: ("Mode 20", "3.58 MHz (high speed)"),
        0x31: ("Mode 21", "3.58 MHz (high speed)"),
        0x35: ("Mode 25", "3.58 MHz (high speed)")
    }

    EXPANSION_RAM = {
        0x00: "None",
        0x01: "16 KBit",
        0x03: "64 KBit",
        0x05: "256 KBit",
        0x06: "512 KBit",
        0x07: "1 MBit"
    }

    CARTRIDGE_TYPE = {
        0x0: "ROM only",
        0x1: "ROM + RAM",
        0x2: "ROM + RAM + battery",
        0x3: "ROM + coprocessor",
        0x4: "ROM + coprocessor + RAM",
        0x5: "ROM + coprocessor + RAM + battery",
        0x6: "ROM + coprocessor + battery"
    }

    COPROCESSOR = {
        0x0: "DSP (DSP-1, 2, 3 or 4)",
        0x10: "GSU (SuperFX)",
        0x20: "OBC1",
        0x30: "SA-1",
        0x40: "S-DD1",
        0x50: "S-RTC",
        0xE0: "Other (Super Game Boy/Satellaview)",
        0xF0: "Custom"
    }

    ROM_SIZE = {
        0x09: "3-4 MBit",
        0x0A: "5-8 MBit",
        0x0B: "9-16 MBit",
        0x0C: "17-32 MBit",
        0x0D: "33-64 MBit"
    }

    RAM_SIZE = {
        0x00: "No RAM",
        0x01: "16 KBit",
        0x03: "64 KBit",
        0x05: "256 KBit",
        0x06: "512 KBit",
        0x07: "1 MBit"
    }

    DESTINATION_COUNTRY = {
        0x00: "Japan",
        0x01: "North America (USA and Canada)",
        0x02: "Europe",
        0x03: "Scandinavia",
        0x06: "Europe (French only)",
        0x07: "Dutch",
        0x08: "Spanish",
        0x09: "German",
        0x0A: "Italian",
        0x0B: "Chinese",
        0x0D: "Korean",
        0x0E: "Common",
        0x0F: "Canada",
        0x10: "Brazil",
        0x11: "Australia",
        0x12: "Other",
        0x13: "Other",
        0x14: "Other"
    }

    # Header's offset position, depending on if it is LoROM, HiROM, ExHiROM or has a developer's header built in
    # This variable shows position where expanded header and cartridge header starts.
    _header_offset = None
    
    # Memory map mode, if cartrdirge is LoROM, HiROM or ExHiROM
    _memory_map_mode = None

    # If it has a dumper's header, then it stores here
    _dumper_header = None

    # The expanded header, not always present
    _expanded_header = None

    # The cartdrige header
    _cart_header = None


    def __init__(self, full_path=None):
        super().__init__(full_path=full_path)
        
        self._system_type = "SNES"
    
        if full_path != None:
            self._load(full_path)

    def _load(self, full_path):

        # Get rom size
        romsize = os.path.getsize(full_path)
        
        # If rom size modulo 1024 is equal to 512, there is probably a dump header
        dh_present = (romsize % 1024) == 512

        # If dump header could be present, then tryes to find the header in the offset position of 512 bytes (dumpers headers bytes)
        # Dumper's header is at the begining of the ROM
        offset_tests_order = [True, False] if dh_present else [False, True]

        # Tries to find the header in the order set before, depending on dumper's header prescence
        result = None
        for offset_orders in offset_tests_order:
            result = self._find_headers(full_path, romsize, offset_orders)
            if result != None:
                # If it finds a header, then stores the values and stop the searching process
                self._headers_offset, self._memory_map_mode, self._dumper_header, \
                    self._expanded_header, self._cart_header = result
                break
        
        if result == None:
            self._clear()
            raise errors.InvalidROMFile(f"File {full_path} is proably not a {self._system_type} ROM or file is corrupted.")
        
        self._data = self._dumper_header if self._dumper_header else bytes(0) + self._expanded_header + self._cart_header
        self._full_path = full_path
    
    def _find_headers(self, file, romsize, additiona_offset=False):
        """
        Tryes to find a valid SNES header.

        Args:
            file (str): the file path of the ROM.
            romsize (int): the real ROM size.
            additiona_offset (bool):  if the rom has a dumper's header, applys a 512 k offset. Otherwise, it use the standar positions for HiROM, LoROM and ExHiROM.

        Returns:
            touple: 
                - real_offset (byte): the offset where data found starts
                - rom_type (str): "LoROM", "HiROM", "ExHiROM"
                - dumper_header (bytes): 32 bytes representing header's information, if exists. Otherwise returns None.
                - expanded_header (bytes): 16 bytes representing the expanded header information.
                - cart_header (bytes): 32 bytes representing the SNES header itself. 
        """

        result = None
        with open(file, "rb") as f:
            
            for offset, rom_type in self.HEADER_POSITIONS.items():
                
                real_offset = offset + (512 if additiona_offset else 0)
                
                # Check if potential header is inside the ROM limits
                if real_offset + 48 > romsize:
                    return
                
                f.seek(real_offset)
                data = f.read(48)

                # Read the data
                dumper_header = data[0:512] if additiona_offset else None
                expanded_header = data[512:528] if additiona_offset else data[0:16]
                cart_header = data[528:560] if additiona_offset else data[16:48]

                result = (real_offset, rom_type, dumper_header, expanded_header, cart_header)
                
                try:
                    if self._verify_checksum(cart_header):
                        return result
                except:
                    return None
                
        return result
    
    def _verify_checksum(self, header: bytes) -> bool:
        """
        Verifies checksum from header information.

        Args:
            header: 32 bytes header containing checksum bytes and complement checksum at the very end.
        
        Returns:
            bool: True if checksum is valid.
        """

        # Read checksum and inverse checksum from the suposed header
        checksum = (header[28] << 8) | header[29]
        inv_checksum = (header[30] << 8) | header[31]

        # Verify checksum. If the test is negative, then sets no header found 
        return (checksum + inv_checksum) & 0xFFFF == 0xFFFF


    @property
    def pretty_data(self):
        """Returns data in a friendly format dictionary"""
        
        data = {
            "loaded_class": "SNES",
            "title": "unknown",
            "map_mode": "unknown",
            "cpu_clock": "unknown",
            "cartridge_type": "unknown",
            "coprocesor": "unknown",
            "rom_size": "unknown",
            "ram_size": "unknown",
            "destination_country_code": "unknown",
            "developer_id_present": "unknown",
            "mask_rom_version": "unknown",
            "checksum_complement": "unknown",
            "checksum": "unknown"
        }

        # Game Title
        data["title"] = self.advanced_text_decode(self._cart_header[0:21]).strip()

        # ROM speed and memory map mode
        map_mode = self.MAP_MODE.get(self._cart_header[21], ("unknown", "unknown"))
        data["map_mode"] = map_mode[0]
        data["cpu_clock"] = map_mode[1]

        # Extracts lower nibble (d0 to d3) ROM/RAM/battery and high nibble for coprocessor
        try:
            config_nibble = self._cart_header[22] & 0b00001111
            coprocessor_nibble = self._cart_header[22] & 0b11110000

            data["cartridge_type"] = self.CARTRIDGE_TYPE.get(config_nibble)
            if config_nibble not in [0,1,2]:
                data["coprocessor"] = self.COPROCESSOR.get(coprocessor_nibble)
            else:
                data["coprocessor"] = "not apply"
        except:
            data["cartridge_type"] = "undetermined"
            data["compressor"] = "undetermined"

        data["rom_size"] = self.ROM_SIZE.get(self._cart_header[23], "unknown")
        data["ram_size"] = self.RAM_SIZE.get(self._cart_header[24], "unknown")

        data["destination_country_code"] = self.DESTINATION_COUNTRY.get(self._cart_header[25], "undetermined")

        data["developer_id_present"] = "yes" if self._cart_header[26] == 0x33 else "no"

        data["mask_rom_version"] = self._cart_header[27]

        data["checksum_complement"] = hex(self._cart_header[28])
        data["checksum"] = hex(self._cart_header[29])


        if data["developer_id_present"] == "yes":
            # if self._cart_header[26] == 0x33 or self._cart_header[20] == 0x0:
            # Maker code
            data["maker_code"] = self._expanded_header[0:2].decode("ascii", errors="replace")
            data["game_code"] = self._expanded_header[2:6].decode("ascii", errors="replace")

            data["expansion_ram_size"] = self.EXPANSION_RAM.get(self._expanded_header[13], "undetermined")

            data["special_version"] = "yes" if self._expanded_header[14] != 0x0 else "no"
            data["cartridge_subnumber"] = self._expanded_header[15]

        return data

    def _clear(self):
        self._full_path = None
        self._data = {}
        self._system_type = None

        # Header's offset
        self._header_offset = None
        
        # Memory map mode
        self._memory_map_mode = None

        # Dumper's header
        self._dumper_header = None

        # Expanded header
        self._expanded_header = None

        # Cart header
        self._cart_header = None
    
    @property
    def dumper_header(self):
        """Returns dumper's header."""
        return self._dumper_header

    @property
    def expanded_header(self):
        """Returns the expanded header"""
        return self._expanded_header

    @property
    def cart_header(self):
        """Returns the cart header"""
        return self._cart_header
    
    @property
    def memory_map_mode(self):
        """Returns the memmory map mode detected (str)"""
        return self._memory_map_mode

class ROMDetector:

    ROM_EXTENSIONS = {
        # Sega
        "Mega Drive": [".md", ".gen", ".smd", ".bin", ".32x", ".mdx"], # Mega Drive and Mega Drive 32X ROMS
        "Master System": [".sms", ".sg", ".sc", ".gg", ".mv"], # Master System and Game Gear ROMS
        
        # Nintendo
        "NES": [".nes", ".fds", ".unf"], # NES ROMS
        "SNES": [".smc", ".sfc", ".fig", ".bs", ".st"], # Super NES ROMS
        "Game Boy": [".gb", ".gbc", ".cgb"], # Game Boy and Game Boy Color
        "Nintendo 64": [".n64", ".v64", ".z64"], # Nintendo 64
    }

    ALL_ROM_EXTENSIONS = {ext for lista in ROM_EXTENSIONS.values() for ext in lista}

    def __init__(self):
        pass

    @staticmethod
    def load(full_path):

        if not os.path.exists(full_path):
            raise FileNotFoundError("File not found.")

        rom_type = ROMDetector.detectType(full_path)
        
        if rom_type == "Mega Drive":
            return ROM_SMD(full_path)
        
        elif rom_type == "Master System":
            return ROM_SMS(full_path)
        
        elif rom_type == "NES":
            return ROM_NES(full_path)
        
        elif rom_type == "SNES":
            return ROM_SNES(full_path)

        raise errors.UnsupportedROMError(f"ROM type not supported.")
        
    @staticmethod
    def detectType(full_path):
        """
        Tryes to detect the ROM system type
        Possible return values of detected ROMs are:
            - 'Mega Drive' : Megadrive/Genesis, 32X
            - 'Master System' : Master System, Game Gear, SG
            - 'NES' : Nintendo Entertainment System
        It will return None if ROM is not detected.

        Args:
            full_path (str): full path to ROM file.
        
        Returns:
            (str) : the rom type. It will return None on failure.
        """

        # First, it will attempt to read ROM header to determine its type
        rom_type = None
        with open(full_path, 'rb') as f:
            
            # NES type
            data = f.read(4)
            if b'NES\x1A' == data:
                rom_type = "NES"
            else:
                # Mega Drive
                f.seek(256)
                data = f.read(4)
                if b'SEGA' == data:
                    rom_type = "Mega Drive"
                else:
                    # SMS or GG type
                    f.seek(0x7ff0)
                    data = f.read(8)
                    if b'TMR SEGA' == data:
                        rom_type = "Master System"

        # SNES are special, they do not have a string or a magic number... so, the easy way to do detect them, is to load its class
        # as it will do the complex procedure of detection.
        if rom_type == None:
            try:
                _ = ROM_SNES(full_path)
                rom_type = "SNES"
            except errors.InvalidROMFile:
                pass

        # If ROM header method fails, then tries to guess from its extension
        if rom_type == None:
            _, extension = os.path.splitext(full_path)
            for key, items in ROMDetector.ROM_EXTENSIONS.items():
                if extension in items:
                    return key

        return rom_type

class ROMcompressed:

    _main_compressed_file = None
    _file_type = None
    _file_list = []

    def __init__(self):
        pass

    def getCompressedFileList(self, full_path, create_compatible_list_only=False):
        """
        Loads compressed file and creates a file list with its content.
        The file list will not load directories, only files.

        Args:
            full_path (str): path to compressed file.
            create_compatible_list_only (bool): generates the list file only with known ROM system extensions, otherwise will load all files.
        """

        # Check if file exists
        if os.path.exists(full_path):
            self._main_compressed_file = full_path
        else:
            raise FileNotFoundError("File not loaded.")
        
        # Check if file is format supported
        self._check_compressed_type(full_path)
        if self._file_type not in ["zip", "7z"]:
            raise errors.FileFormatNotSupported("File is not zip or 7z format.")

        # Generates list
        raw_file_list = []
        if self._file_type == "7z":
            with py7zr.SevenZipFile(self._main_compressed_file, mode='r') as file7zip:
                # Obtener metadatos completos (incluye info de directorios)
                raw_file_list = [
                    file.filename for file in file7zip.files 
                    if not file.is_directory  # Filtra directorios
                ]
        elif self._file_type == "zip":
            with zipfile.ZipFile(self._main_compressed_file, 'r') as zip_file:
                raw_file_list = [name for name in zip_file.namelist() if not name.endswith('/')]
        
        # Loads only compatible files, by its extension
        self._file_list = []
        if create_compatible_list_only:
            for file_item in raw_file_list:
                base_name, extension = os.path.splitext(file_item)
                if extension.lower() in ROMDetector.ALL_ROM_EXTENSIONS:
                    self._file_list.append(file_item)
        else:
            self._file_list = raw_file_list

    def extractFiles(self, full_path, create_type_directory=False, clean_destination=False):
        """
        Extract the loaded compressed file into a specific directory. 
        
        Args:
            full_path (str): the directory to extract.
            create_type_directory (bool): it will try to detect and create ROM system folder for its corresponding file.
            clean_destination (bool): erase everything contained in full_path directory before extraction.
        """

        # If target directory does not exist....
        if not os.path.exists(full_path):
            os.mkdir(full_path)
        # But if exists and it has clean order....
        elif clean_destination:
            # Get the path, list all files and directories and erase them all
            path = Path(full_path)
            for item in path.glob('*'):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

        # Sets a string time for multiple uses
        string_time = str(int(time.time()))

        if create_type_directory:
            tmp_dir_name = "tmp_rom_folder_" + string_time
            temp_dir = os.path.join(full_path, tmp_dir_name)
            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)
        else:
            temp_dir = full_path

        try:
            if zipfile.is_zipfile(self._main_compressed_file):
                with zipfile.ZipFile(self._main_compressed_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            else:
                with py7zr.SevenZipFile(self._main_compressed_file, mode='r') as sz_ref:
                    sz_ref.extractall(temp_dir)

            # If should create system emulator type directory...
            if create_type_directory:

                # For each file read in compressed file...
                for item_file in self._file_list:
                    
                    # sets path from origin
                    origin_file_path = os.path.join(temp_dir, item_file)

                    # extracts extension
                    _, file_extension = os.path.splitext(origin_file_path)
                    
                    # Looks for corresponding system in ROM_EXTENSIONS
                    file_type = "unknown_system_" + string_time
                    for key in ROMDetector.ROM_EXTENSIONS:
                        if file_extension.lower() in ROMDetector.ROM_EXTENSIONS[key]:
                            file_type = key
                            break

                    # Sets the emulator system directory, if it does not exist
                    system_directory = os.path.join(full_path, file_type)
                    os.makedirs(system_directory, exist_ok=True)

                    # Creates the full destination path
                    clean_filename = os.path.basename(item_file)
                    destination_file_path = os.path.join(system_directory, clean_filename)

                    # Moves the file
                    shutil.move(origin_file_path, destination_file_path)
        finally:
            # Cleaning
            if create_type_directory:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def compressIndividually(self, full_path, known_extensions_only=False, file_format="zip", delete_original=True):
        """
        Compress files individually in its own directory.

        Args:
            full_path (str): directory with files to be compressed.
            known_extension_only (bool): only compress files with knowns system ROMS.
            file_format (str): 'zip' or '7z' only.
            delete_original (bool): deletes the original file after compression.
        """

        if file_format not in ["zip", "7z"]:
            raise errors.FileCompressionFormatNotSupported("Unsopported compression format, only 'zip' or '7z' is allowed.")

        file_list = [str(archivo) for archivo in Path(full_path).rglob('*') if archivo.is_file()]

        file_list_final = []
        if known_extensions_only:
            for eval_file in file_list:
                _, extension = os.path.splitext(eval_file)
                for key in ROMDetector.ROM_EXTENSIONS:
                    if extension.lower() in ROMDetector.ROM_EXTENSIONS[key]:
                        file_list_final.append(eval_file)
                        break
        else:
            file_list_final = file_list

        for item_file in file_list_final:
            self._compressIndividualFile(item_file, format=file_format, delete_original=delete_original)
    
    def decompressIndividually(self, full_path, delete_original=True):
        """
        Decompress files individually in its own directory.

        Args:
            full_path (str): directory with files to be decompressed.
            delete_original (bool): deletes the original file after decompression.
        """
        file_list = [str(archivo) for archivo in Path(full_path).rglob('*') if archivo.is_file()]

        for file in file_list:
            self._decompressIndividualFile(file, delete_original=delete_original)

    def romClassify(self, directory_src, directory_dest, not_found_prefix="_"):
        """
        Detects and classify ROMS, moving them to destination directory in individual system directories.
        
        Args:
            directory_src(str): path where ROMs are stored.
            directory_dest (str): path to create ROM system directories and to store ROMs.
            not_found_prefix: a prefix to create a folder to store not classified ROMs.
        """

        if not os.path.exists(directory_src):
            raise errors.DirectoryNotFound("Source directory not found.")
        if not os.path.exists(directory_dest):
            raise errors.DirectoryNotFound("Destination directory not found.")

        file_list = [str(file) for file in Path(directory_src).rglob('*') if file.is_file()]

        romObj = ROM()

        for file in file_list:

            # Tries to recognize file type
            rom_type = ROMDetector.detectType(file)

            # Sets destination
            if rom_type != None:
                # If destination does not exist
                destination = os.path.join(directory_dest, rom_type)
            else:
                destination = os.path.join(directory_dest, not_found_prefix+"unclassified_ROMs")
            
            # Creates destination if it doesn't exist
            if not os.path.exists(destination):
                os.mkdir(destination)

            # Moves the ROM
            final_destination = os.path.join(destination, os.path.basename(file))
            shutil.move(file, final_destination)
            
    @property
    def main_compressed_file(self):
        """
        Returns full path of compressed file loaded.
        
        Returns:
            str: full compressed file path.
        """
        return self._main_compressed_file
    
    @property
    def compressed_type(self):
        """
        Returns compressed file type.

        Returns:
            str: filetype, could be 'zip' or '7z'
        """
        return self._file_type
    
    @property
    def file_list(self):
        """
        Returns list of files in compressed file loaded.

        Returns:
            list[str]: list of files read in compressed file.
        """
        return self._file_list
    
    def _check_compressed_type(self, full_path):
        """
        Checks if file is zip or 7zip type and stores in _file_type variable.

        Args:
            full_path (str): path to file.
        """
        with open(full_path, 'rb') as f:
            # Read first 4 bytes
            header = f.read(6)

        # check if is 7z
        if header.startswith(b'7z\xBC\xAF'):
            self._file_type = "7z"
        # check if it is zip
        elif header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06'):
            self._file_type = "zip"
        else:
            self._file_type = None

    def _compressIndividualFile(self, file_path, format='zip', delete_original=False):

        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        base_name, extension = os.path.splitext(file_name)
        compressed_path = os.path.join(file_dir, f"{base_name}.{format}")

        if extension.lower() not in [".zip", ".7z"]:

            if format == 'zip':
                with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(file_path, arcname=file_name)
            elif format == '7z':
                with py7zr.SevenZipFile(compressed_path, 'w') as szf:
                    szf.write(file_path, arcname=file_name)

            if delete_original and os.path.exists(compressed_path):
                os.unlink(file_path)

    def _decompressIndividualFile(self, file_path, delete_original=False):
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        base_name, extension = os.path.splitext(file_name)

        if extension in [".zip", ".7z"]:

            compressed_file_list = []
            if extension == ".zip":

                # Extracts the zipfile
                with zipfile.ZipFile(file_path, "r") as zipf:
                    # Frist get the file list
                    compressed_file_list = zipf.namelist()
                    # then extracts
                    zipf.extractall(file_dir)
            
            elif extension == ".7z":
                with py7zr.SevenZipFile(file_path, mode="r") as sevenzf:
                    # First get the file list
                    compressed_file_list = sevenzf.getnames()
                    # then extracts
                    sevenzf.extractall(file_dir)
                
            # Check presence of all files listed in the zip file
            for check_file in compressed_file_list:
                full_check_path = os.path.join(file_dir,check_file)
                if not os.path.exists(full_check_path):
                    raise errors.DecompressionFailure("Failed decompression for ", file_path)
            
            if delete_original:
                # If everything went ok, removes original zip file
                os.remove(file_path)


# Available elements to be imported
__all__ = ["ROMcompressed", "ROMDetector", "ROM_SMD", "ROM_SMS", "ROM_NES", "ROM_SNES"]

# Only show available
def __dir__():
    return __all__

# Rasie an error if someone wants to import dependencies
def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"Module 'romlib.roms' has no attribute '{name}'")
    return globals()[name]