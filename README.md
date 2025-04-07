# ROMLib

## 📌 Descripción General del Proyecto
**ROMLib** es una librería para la lectura y análisis de metadatos en ROMs de diversas consolas clásicas. Soporta varios formatos y estándares de archivo, incluyendo GoodSets y múltiples tipos de headers. El proyecto nace de mi entusiásmo por los juegos clásicos.

**Este paquete no distribuye ninguna ROM de juegos de ningún tipo. Tampoco tengo afiliaciones con las empresas, organizaciones o sitios webs mencionados en todo el proyecto, incluyendo la presente documentación.**

## 📂 Estructura de Módulos

### 🔹 `roms`
Contiene clases para la manipulación de diferentes tipos de ROMs:

- **`ROM`** (class): Clase base para todas las ROMs.
- **`ROMDetector`** (class): Permite detectar y crear el objeto según el tipo de ROM detectado.
- **`ROMCompressed`** (class): Permite maniuplar los ROMs comprimidos en ZIP o 7z, clasificarlos y comprimirlos o descomprimirlos individualmente.
- **`ROM_SMD`** (class): Parser de ROMs de **Sega Mega Drive / Genesis**. Soporta dumps de cartuchos estándar y **32X**. Compatible con archivos `.bin` y `.smd`, entre otros.
- **`ROM_SMS`** (class): Parser de ROMs de **Sega Master System**. Detecta headers estándar y los propietarios de Codemasters. También intenta ubicar headers en posiciones no convencionales.
- **`ROM_NES`** (class): Parser de ROMs de **Nintendo Entertainment System**. Compatible con los formatos **iNES** y **NES 2.0**, permitiendo la identificación de mappers y otros metadatos avanzados.
- **`ROM_SNES`** (class): Parser de ROMs de **Super Nintendo Entertainment System**. Detecta headers en las ROMs de SNES, que pueden estar en difernete posición de acuerdo al esquema de memoria del cartucho o si contiene un header del volcador (dumper header). Esta clase es la que implementa la lógica más compleja de todas.

### 🔹 `tags`
- **`Tags`** (class): Extrae e interpreta etiquetas estándar de **GoodSets** para determinar información como región, estado del dump, versiones, etc.

## 🛠️ Módulo *rom*
### ROMDetector
Se usa para autodetectar e instanciar la clase correspondiente.

#### .detectType()
Detecta el tipo de ROM y lo devuelve en formato string.

```python
from romlib.roms import ROMDetector

romType = ROMDetector.detectType("/ROMs/Mega Drive/Comix Zone (U) (Prototype - Jun 03, 1995)") 
print(romType)

>> 'Mega Drive'

```
#### .load()
Detecta el tipo de ROM y devuelve una instancia de su clase correspondiente

```python

romObject = ROMDetector.load("/ROMs/Mega Drive/Comix Zone (U) (Prototype - Jun 03, 1995)")
print(romObject)

>> <romlib.roms.ROM_SMD object at 0x7f0b7d0360d0>

```

### ROMcompressed
Se emplea para manipular archivos comprimidos. Descormprime sets de ROMs en formato 7z o ZIP, ordena en carpetas según su tipo y a la vez puede comprimir o descomprimir ROMs de manera individual.

#### .getCompressedFileList()
Carga información sobre un archivo comprimido a manipular. Los argumentos son:
- full_path (str): ruta completa del archivo comprimido (7z o ZIP unicamente)
- create_compatible_list_only (bool): si es True, solamente cargará los archivos que sean potenciales ROMs de los sistemas soportados, según su extensión.

```python
from romlib.roms import ROMcompressed

rc = ROMcompressed()
rc.getCompressedFileList(full_path="/media/mis_roms/Varios.7z", create_compatible_list_only=True)

print(rc.compressed_type)

>> '7z'

print(rc.main_compressed_file)

>> '/media/mis_roms/Varios.7z'

print(rc.file_list)

>> ['SMD/Comix Zone (U) [f2].bin','SMD/Alex Kidd - Cheongongmaseong (K) [!].bin','NES/multiples/35-in-1 [p1].nes']
```

#### .extractFiles()
Extrae el contenido del archivo ZIP o 7z cargado. Los argumentos son:
- **full_path** (str): ruta de destino de la extracción.
- **create_type_directory** (bool): creará los directorios para cada tipo de ROM hallado. En caso de hallar un archivo no soportado, se creará una carpeta con el prefijo 'unknown_system_' y un timestamp como sufjio. Si es 'False', extraerá todos los archivos en el destino sin clasificarlos en careptas por sistema.
- **clean_destination** (bool): borrará todo el contenido especificado en *full_path* antes de efectuar la extracción (**PRECACUCIÓN**).

```python
rc.extractFiles(full_path="/juegos/ROMs", create_type_directory=True, clean_destination=False):
```
La estructura creada para ese ejemplo es:
```bash
/juegos/
    | -- ROMs/
        |-- Mega Drive/
        |   |-- Comix Zone (U) [f2].bin
        |   |-- Alex Kidd - Cheongongmaseong (K) [!].bin
        |-- NES/
            |-- 35-in-1 [p1].nes
```

#### .compressIndividually()
Comprime los archivos de ROMs de manera indiviudal, de manera recursiva.
- **full_path** (str): ruta dónde se encuentran los archivos ROMs a procesar.
- **known_extensions_only** (bool): si es 'True' procesará solamente los archivos que reconozca como ROMs por su extensión.
- **file_format** (str): valores posibles: 'zip' o '7z'.
- **delete_original** (bool): si elimina los archivos originales luego de realizar la compresión.

```python
compressIndividually(full_path="/juegos/ROMs", known_extensions_only=False, file_format="zip", delete_original=True):
```

El resultado del ejemplo es:
```bash
/juegos/
    |-- ROMs/
        |-- Mega Drive/
        |   |-- Comix Zone (U) [f2].zip
        |   |-- Alex Kidd - Cheongongmaseong (K) [!].zip
        |-- NES/
            |-- 35-in-1 [p1].zip
```

#### .decompressInvidiually()
Descomprime los archivos indiviudales en su lugar, de manera recursiva.
- **full_path** (str): ruta dónde se encuentran los archivos comprimidos a procesar.
- **delete_original** (bool): si elimina los archivos originales luego de realizar la descompresión.

```python
rc.decompressIndividually(self, full_path="/juegos/roms", delete_original=False):
```

El resultado del ejemplo es:
```bash
/juegos/
    |-- ROMs/    
        |-- Mega Drive/
        |   |-- Comix Zone (U) [f2].zip
            |-- Comix Zone (U) [f2].bin
        |   |-- Alex Kidd - Cheongongmaseong (K) [!].zip
            |-- Alex Kidd - Cheongongmaseong (K) [!].bin
        |-- NES/
            |-- 35-in-1 [p1].zip
            |-- 35-in-1 [p1].nes
```


#### .romClassify()
Intenta identificar cada ROM por su header y, secundariamente, por su extensión para luego crear (si no existe previamente) el directorio de su tipo y moverlo a este último.
- **directory_src** (str): directorio dónde se encuentran las ROMs sin clasificar.
- **directory_dest** (str): directorio dónde crear las carpetas de cada sistema y mover las ROMs respectivamente.
- **not_found_prefix** (str): prefijo para la carpeta dónde se almacenarán los archivos de ROMs que no pudieron ser clasificados en ningún sistema.


Ej. de contenido de *directory_src*:
```bash
/juegos/
    |-- sin clasificar/
        |-- Metal Gear (U) [T+Fre1.00_Generation IX].nes
        |-- Namco Classic (J) [!].nes
        |-- Chuck Rock (EB) [!].sms
        |-- Archivo Desconocido.rom
```

```python
rc.romClassify(directory_src="/juegos/sin clasificar", directory_dest="/juegos/roms", not_found_prefix="_"):
```

Luego de la ejecución, el contenido de '/juegos/sin clasificar' estará vacio. Siguiendo con el ejemplo anterior, el contenido de 'directory_dest' (/juegos/roms) será:
```bash
/juegos/
    |-- ROMs/
        |-- Mega Drive/
        |   |-- Comix Zone (U) [f2].bin
        |   |-- Alex Kidd - Cheongongmaseong (K) [!].bin
        |-- NES/
            |-- 35-in-1 [p1].nes
            |-- Metal Gear (U) [T+Fre1.00_Generation IX].nes
            |-- Namco Classic (J) [!].nes
        |-- Master System/
            |-- Chuck Rock (EB) [!].sms
        |-- _unclassified_ROMs()
            |-- Archivo Desconocido.rom

```

### ROM, ROM_SMD, ROM_SMS, ROM_NES, ROM_SNES
La clase ROM es la clase base de estructura para las demás. Todas comparten una serie de propiedades y métodos, pero la información que otorgan varía dependiendo del tipo de clase de ROM cargada. Al emplear ROMDetector intentará devolver la clase apropiada para cada ROM procesado, es decir, si detecta una ROM de **Master System**, devolverá un objeto *ROM_SMS*.

ROM_SMD, ROM_SMS y ROM_NES pueden ser instanciadas de manera directa y es recomendable hacerlo. Es decir, si sabemos que una ROM es de Master System, será preferible instanciar ROM_SMS en lugar de emplear ROMDetector.

A continuación se describen los métodos y propiedades comunes a todos las clases de ROMs.

### ROM
Clase común a todos los ROMs. Todos los ROMs comparten sus propiedades y sus métodos. Al inicializarla se puede especificar la ROM a cargar:
- **full_path** (str): ruta a la ROM que se va a cargar.

#### .load()
Este método carga una ROM e inmeditamente la analiza buscando la información en bruto.
- **full_path** (str): ruta a la ROM que se va a cargar.

#### *.full_path*
Devuelve la ruta (str) del archivo de ROM cargado.

#### *.system_type*
Devuelve el tipo de clase:
- "SMD" para ROM_SMD
- "SMS" para ROM_SMS
- "NES" para ROM_NES

#### *.raw_data*
Develve la información en bruto leida en el header (bytes) cargada al momento de ejecución de *load()*.

#### *.pretty_data*
Devuelve un **diccionario** con las propiedades obtenidas del ROM cargado en la instancia. Estas propiedades varían de acuerdo al tipo de ROM en cuestión. Esta propiedad es la más importante, ya que devuelve la información interpretada por la clase y 'humano legible' en la mayoría de los casos.

Los valores de pretty_data pueden tener el formato str o int. En casos en que no se halle ningún dato, el valor por defecto es 'unknown'. La propiedad pretty_data puede contener campos adicionales, como es el caso de las ROMs de Master System de Codemasters, que poseen un header adicional con mas información. Algunos campos informan valores inválidos como 'invalid' o términos similares.

### ROM_SMD
El proceso de carga de una ROM de Mega Drive es bastante simple, ya que los datos presentan poca variabilidad y se trata de un volcado 'bruto' de un hardware que no posee mucha complejidad adicional (diferente a lo que ocurre con las ROMs de NES).

#### *.pretty_data*
Valores de *pretty_data* para la clase ROM_SMD:
|Clave|Valor|Valores posibles|
|-----|-----|---------------|
|loaded_class| Identifica el objeto de clase generado para la ROM cargada.|*Valor fijo:* "SMD"|
|system_type| El tipo de sistema cargado, informado por el propio header en la ROM.|*Uno de:* "Sega game",Mega Drive", "Mega Drive + 32X", "Mega Drive (Everdrive extensions)", "Mega Drive (Mega Everdrive extensions)", "Mega Drive (Mega Wifi extensions)", "Pico","Tera Drive (boot from 68000 side)", "Tera Drive (boot from x86 side)"|
|copyright_release_date| Información sobre el copyright del juego, mes y año de la publicación.|*Variable* Ejemplo: "(C)SEGA 1996.NOV"|
|title_domestic|Título del juego dado en el lugar de origen.|*Variable*
|title_overseas|Título con el que fue lanzado al mundo.|*Variable*
|serial_number_full|Campo con el número de serie completo.|*Variable* Este campo informa tipo de juego, número de serie y número de revisión.
|software_type|Tipo de software ('Game': juego, etc.), es desglose de serial_number_full.|*Uno de:* "Game", "Aid", "Boot ROM (TMSS)", "Boot ROM (Sega CD)"
|serial_number|Número de serie del producto, es desglose de serial_number_full.|*Variable*|
|revision|Número de revisión, si la compañia lanzó más de una será diferente a 00, también es desglose de serial_number_full.|*Variable*|
|checksum|Checksum de la ROM.|*Variable*|
|supported_devices|Periféricos y accesorios soportados.| *Múltiples valores, separados por coma:* "3-button controller", "6-button controller", "Master System controller","Analog joystick", "Multitap", "Lightgun", "Activator", "Mouse", "Trackball", "Tablet", "Paddle", "Keyboard or keypad", "RS-232",  "Printer", "CD-ROM (Sega CD)", "Floppy drive", "Download?" 
|rom_size|Tamaño de la ROM y su unidad (KB) informado por la misma.|*Variable*
|ram_size|Tamaño de la RAM y su unidad (KB) (¿Es un valor constante en todas las ROMs?).|*Variable*|
|extra_memory_available|Si existe o no una memoria extra (SRAM o EEPROM).|*Respuesta fija:* "yes", "no"|
|modem_support|Si la ROM posee soporte para modem. Existen más datos sobre el modem pero es algo pendiente de construír.|*Respuesta fija:* "yes", "no"|
|region|Informa sobre la región soportada por la ROM (y por ende, la norma de TV, que puede ser NTSC-J, NTSC-U o PAL). Los juegos a partir del año 1995 implementaban una forma diferente de almacenamiento de este dato, la clase intenta hallarlo de ambas maneras.|*Una de:* "hardware incompatible", "NTSC-J", "NTSC-U", "PAL", "region free"
|*extra_memory_type*|Tipo de memoria extra. Sólo estará presente si *exra_memory_available* tiene valor 'yes'.|*Uno de:* "SRAM","EEPROM"|
|*extra_memory_sram_type*|Si el tipo de memoria informado en *extra_memory_type* es 'SRAM', entonces muestra el tamaño en KB. Solo estará presente si *extra_memory_type* está presente y con valor 'SRAM'.|*Variable*|
|*extra_memory_sram_saves*|Informa si la memoria SRAM se emplea para guardar partidas o no. Solo disponible si *extra_memory_type* es 'SRAM'.|*Uno de:* "yes", "no"|
|*extra_memory_size*|Informa el tamaño en KB de SRAM disponible. Solo estará disponible si "extra_memory_type" es 'SRAM'.| *Variable*|

### ROM_SMS
#### *.pretty_data*
Valores de *pretty_data* para la clase ROM_SMD:
|Clave|Valor|Valores posibles|
|-----|-----|---------------|
|loaded_class|Identifica el objeto de la clase cargada.|*Valor fijo:* "SMS"|
|header_present|Informa si la ROM tiene un header presente. Algunos juegos, especialmente los más antigüos no poseen ningún header. En ese caso, no habrá información que acceder.|*Uno de:* "yes", "no"|
|header_start_byte|El header en una ROM de Master System puede estar en una posición diferente a la más común (0x7FF0). Esta clave devuelve la posición del header hallada|*Variable*|
|codemasters_header_present|Las ROMs de Codemasters tienen un header adicional con más información. Esta clave informa si ese header está presente o no.|*Uno de:* "yes", "no" 1
|sega_copyright|Mensaje de copyright de Sega, usualmente 'TMR SEGA'.|*Variable*|
|checksum|El checksum de la ROM.|*Variable*|
|product_code|El código de producto-|*Variable*|
|revision|Número de revisión del juego.|*Variable*|
|region|Informa la región del juego.|*Uno de:* "SMS Japan", "SMS Export", "GG Japan", "GG Export", "GG International"|
|size|Informa el tamaño de la ROM explícito en el header.|*Variable:* "8 KB", "16 KB", "32 KB", "48 KB", "64 KB", "128 KB", "256 KB", "512 KB", "1 MB"|
|*cm_n_banks*|Número de bancos de 16kb sobre los que calcula el checksum. Solo presente si *codemasters_header_present* es 'yes'|*Variable*|
|*cm_compilation_date_time*|Fecha y hora de compilación. Este es un valor complejo calculado a partir de múltiples bytes. Devuelve una string con un formato estandarizado: 'YY-mm-dd hh:mm'.|*Variable:* sigue el formato 'YY-mm-dd hh:mm'.
|*cm_checksum*|Checksum de Codemasters.|*Variable*|
|*cm_inverse_checksum*|Checksum inverso de Codemasters.|*Variable*|

#### *.header_position*
Devuelve en notación hexadecimal la posición del header estandar de Sega en formato string.

#### *.raw_data_codemasters*
Esta propiedad devuelve los bytes en bruto del header de Codemasters, si está presente.

### ROM_NES
Esta clase detecta automáticamente si una ROM está en formato iNES (el mas antigüo y más usado) o si se encuentra en NES 2.0 (mejor compatibilidad con emuladores y programas de análisis). El header de NES 2.0, además de extender la información suministrada, presenta algunas diferencias con el de iNES, y por lo tanto, las claves informadas en .pretty_data.

#### *.pretty_data*
Valores de *pretty_data* para la clase ROM_NES:

|Clave|Valor|Valores posibles|
|-----|-----|---------------|
|romfile_type|Que tipo de ROM se trata (iNES o NES 2.0).|*Uno de:* "iNES", "NES 2.0"|
|PRG_ROM_size|Tamaño de PRG-ROM|*Variable*|
|CHR_ROM_size|Tamaño de CHR-ROM|*Variable*|
|nametable_arrangement|Disposición de la 'tabla de nombres'.|*Uno de:* "horizontal (vertically mirrored)", "vertical (horizontally mirrored)"|
|persistent_memory|Presencia de memoria persistente.|*Uno de:* "yes", "no"|
|512_byte_trainer|Si trainer de 512 bytes está presente.|*Uno de:* "yes", "no"|
|alternative_nametable*|Uso alternativo de tabla de nombres.|*Uno de:* "yes", "no"|
|vs_unisystem*|Si se trata de una ROM VS. Unisystem.|*Uno de:* "yes", "no"|
|playchoice_10*|Si se trata de una ROM PlayChoice 10.|*Uno de:* "yes", "no"|
|PRG_RAM_size|Tamaño de PRG-RAM, informado en KB.|*Variable*|
|tv_system|Norma de TV soportada.|*Uno de:* "NTSC", "PAL", "Dual-compatible (NTSC & PAL)"|
|mapper_number|Código de mapper que emplea la ROM.|*Variable*|
|mapper|El nombre del mapper obtenido a partir de mapper_number. Es posible ver la lista completa llamando a *ROM_NES.MAPPERS*.|*Variable*|
|submapper_number**|Número de submapper.|*Variable*|
|console_type**|Tipo de consola.|*Uno de:* "Nintendo Entertainment System", "Nintendo Vs. Ssytem", "Nintendo Playchoice 10", "Extended console type"|
|PRG_RAM_size**|Informa el tamaño de PRG-RAM en KB si está presente.|*Variable*|
|CHR_NVRAM_SIZE**|Informa el tamapo de CHR-NVRAM-SIZE en KB si está presente.|*Variable*|
|tv_system**|CPU PPU timing denota la norma de TV y la región.|*Uno de:* "RP2C02 (NTSC NES)", "RP2C07 (Licensed PAL NES)", "Multiple-region", "UA6538 (Dendy)"|
|VS_PPU_type***|Tipo de VS-PPU, solo disponible si console_type informa 'Nintendo Vs. System'|*Variable*|
|VS_hardware_type***|Tipo de Hardware, solo si *console_type* informa 'Nintendo Vs. System'|*Variable*
|extended_console_type****|Tipo de consola VS Extendida. Solo dipsonible si *console_type* informa "Extended console type".|*Variable*|
|miscellaneus_roms*|ROMs misceláneos|*Variable|
|default_expansion_device*|Dispositivo de expansión por defecto|*Variable*

\* no presentes si la ROM es NES 2.0\
\*\* solo presente si la ROM es NES 2.0\
\*\*\* sólo si la ROM es NES 2.0 y el tipo de sistema es "Nintendo Vs System"\
\*\*\*\* sólo si la ROM es NES 2.0 y el tipo de sistema es "Extended console type"

### ROM_SNES
Esta clase es la más compleja, debido a que las ROMs de SNES presentan el encabezado en posición variable, dependiendo de si presentan o no una cabecera del volcador (dumper's header), si son de tipo LoROM, HiROM o ExHiROM.

#### *.pretty_data*
Valores de *pretty_data* para la clase ROM_SNES:

|Clave|Valor|Valores posibles|
|-----|-----|---------------|
|loaded_class|El identificador de la clase.|*Valor fijo:* "SNES"|
|title|Título del juego.|*Variable*|
|map_mode|Modo del mapeo de memoria (detectado en el header).|*Uno de* .MAP_MODE|
|cpu_clock|Velocidad del reloj del CPU.|*Uno de* .MAP_MODE|
|cartridge_type|Tipo de cartucho.|*Uno de* .CARTDRIGE_TYPE|
|coprocesor|Dependiendo del tipo de cartucho, si tiene co-procesador, será informado aqui.|*Uno de* .COPROCESSOR|
|rom_size|Tamaño de la ROM|*Uno de* .ROM_SIZE|
|ram_size|Tamaño de la RAM|*Uno de* .RAM_SIZE|
|destination_country_code|Región a la que el juego estaba destinado.|*Uno de* .COUNTRY_CODE|
|developer_id_present|Si developer ID está activado, entonces hay información en el header expandido.|*Uno de* "yes" o "no"|
|mask_rom_version|Máscara del número de revisión. Denota el número de revisión de la ROM.|*Variable*|
|checksum_complement|Valor del complemento de checksum|*Variable*|
|checksum|Valor del checksum|*Variable*|
|*maker_code\**|Proviene del header expandido. Código del fabricante, asignado por Nintendo.|*Variable*|
|*game_code\**|Código del juego.|*Variable*|
|*expansion_ram_size\**|Tamaño de la RAM expandida, si está presente.|*Uno de* .EXPANSION_RAM|
|*special_version\**|Si es una versión especial o regular.|*Uno de* "yes", "no"|
|*cartridge_subnumber\**|Número de cartucho. Normalmente cero. Solo necesario para juegos que usan el mismo cartucho.|*Variable*|

\* solo se muestran si el expanded header está presente.

## 🛠️ Módulo *tags*

### Tags
El módulo tags contiene la clase **Tags** que permite escanear y detectar los tags definidos y empleados por *GoodTools (GoodSets)*, que es una herramienta para la gestión de ROMs para Windows. También posee un método capaz de 'limpiar' el nombre del archivo y devolverlo lo más original posible. Aunque puede trabajar con rutas, se recomienda usarlo con nombres de archivos con o sin extensión.

#### .load()
Este método permite cargar una string correspondiente a un nombre de archivo, con o sin su extensión. Al cargarla, es inmediatamente analizada y su resultado cargado en memoria.
- **filename** (str): el nombre de archvo o cadena a analizar.
- **rom_type** (str): si se define como none (valor por defecto), analizará todos los sets de tags posibles. Si se le especifica un tipo (valores posibles: "SMD", "SMS", "SNES", "NES") evitará analizar aquellos que no correspondan.

#### .clear()
Descarga la string analizada y limpia todas sus variables.

#### *.fullname*
Devuelve la string tal cuál fue cargada con su ruta.

#### *.rom_name*
Devuelve una string con el nombre del archivo 'limpio', es decir, sin tags ni extensiones.

#### *.gc_all*
Devuelve una lista de diccionarios de todos los tags hallados para la cadena evaluada, sin clasificaciones.

#### *.gc_all_json*
Devuelve una lista de todo los tags hallados para la cadena evaluada en formato *json*, en sus respectivas categorías.

#### *.gc_standard, .gc_universal, .gc_nes, .gc_snes, .gc_genesis*
* **.gc_standard**: Devuelve una lista de diccionarios de los tags hallados para la categoría de **tags estándar**.
* **.gc_universal**: Devuelve una lista de diccionarios de los tags hallados para la categoría **tags universales**.
* **.gc_nes, .gc_snes, .gc_genesis**: Devuelve una lista de diccionarios con los tags hallados específicamente para el sistema en cuestión (NES, SNES, MegaDrive/Genesis respectivamente). No hay códigos especiales para *Master System*.

Todas estas propiedades devuelven una lista de diccionarios con las siguientes claves:
```
[
    {
        "tag": <tag reconocido>,
        "value": <valor, si corresponde>,
        "short_desc": <descripción corta del tag hallado, en inglés>,
        "short_desc_spa": <descripcion corta del tag hallado, español>,
        "extra_data": <información adicional>,
        "raw_detection": <tag extraído de la string sin procesar>
    },
    ...
]
```

Por ejemplo, para **"[T+Eng2b_DackR]"**, el parseado devuelve:
```python
[
    {
        "tag": "[T+]",
        "value": "Eng",
        "short_desc": "NewerTranslation",
        "short_desc_spa": "Traducción nueva",
        "extra_data": "2b_DackR"
        "raw_detection": "[T+Eng2b_DackR]"
    }
]
```
Los campos son fijos y se rellenan con *None* en caso de no poseer un valor.


#### *.gc_country, .gc_country_unofficial*
* **.gc_country**: Devuelve los tags oficiales que identifican la región del juego, especificados en la categoría **región** de *GoodTools*.
* **.gc_country_unofficial**: Devuelve una lista de diccionarios de los tags de identificación de **región** que no son oficiales de *GoodTools*.

Todas estas propiedades devuelven una lista de diccionarios con las siguientes claves:
```
[
    {
        "tag": <tag reconocido>,
        "country": <país o región en inglés>,
        "country_spa": <país o región, en español>,
        "preferred": <para los 'unofficial' tags, si es preferido su uso.>,
        "raw_detection": <tag extraído de la string sin procesar>
    },
    ...
]
```

Por ejemplo, para **"[JUE]"**, el parseado devuelve:
```python
[
    {
        "tag": "[JUE]",
        "country": "Japan, USA, Europe",
        "country_spa": "Japón, USA, Europa",
        "preferred": "not apply",
        "raw_detection": "[JUE]"
    }
]
```

#### *.gc_ ... _json*
Cada propiedad que comienza con el prefijo **gc_** tiene una homóloga con el sufijo **_json** que permite obtener los elementos en el formato en cuestión. Por ejemplo, *'.gc_genesis_json'* devolverá la lista de diccionarios de tags parseados en formato *json*.

**gc_all_json** devuevle los elementos englobados en categorías: *"standard", "universal", "country", "country_unofficial"* y si corresponde: *"genesis", "nes", "snes"*.

## 🛠️ Módulo *errors*
Documentación pendiente de confeccionar.

## ToDo
- [ ] Terminar la documentación
- [X] Añadir más tags a la detección (quedan pendientes algunos tags específicos de sistema)
- [ ] Agregar la funcionalidad de forzado para las clases del módulo *ROM*, para que la clase se cargue igual aunque el ROM sea uno inválido.

## Fuentes
- **NESDev** https://www.nesdev.org/
- **SNES Development Manual** Nintendo of America (r) - Consultado en Archive.org: https://archive.org/details/SNESDevManual
- **Plutiedev** https://plutiedev.com/
- **SegaRetro** https://segaretro.org/
- **SMSPower** https://www.smspower.org/
- **GameTechWiki** GoodTools https://emulation.gametechwiki.com/index.php/GoodTools
## Licencia

Este proyecto está licenciado bajo la **GNU General Public License v3.0**.  
Puedes ver el archivo [LICENSE](LICENSE) para más detalles.