# Issue #2: Automatické oříznutí fotopastí Bunaty - vytvoření _daterem verze

## Popis problému

Fotografie a videa z fotopastí Bunaty (Bunaty Micro 4K, Bunaty WiFi Solar) obsahují časové razítko v podobě malé linky na spodní straně snímku. Toto razítko:

- Snižuje profesionální vzhled fotografie
- Obsahuje datum a čas, které mohou být nežádoucí v komerčním obsahu
- Musí být odstraněno před nahráním na fotobanky

### Aktuální stav
- Uživatel musí manuálně vytvářet oříznuté verze v externím editoru
- Proces je časově náročný a opakující se
- Riziko nekonzistentního ořezu mezi fotkami

### Požadovaný stav
- Automatické vytvoření _daterem verze při zpracování fotky z fotopasti v `givenew` (preparemediafile.py)
- Originál označen jako "zamítnuto" (nedá se použít kvůli razítku)
- _daterem verze označena jako "připraveno" (čistá fotka bez razítka)

## Detekce fotopastí

Fotopasti se detekují podle **názvu složky**, kde se fotka nachází. Skript `sortunsortedmedia` již správně detekuje a označuje fotky z fotopastí na základě:

1. **Regex vzoru názvu souboru** (definováno v `sortunsortedmedialib/constants.py`):
   - **Bunaty Micro 4K**: `PICT0195.JPG` → regex `r"^PICT\d{4,6}$"`
   - **Bunaty WiFi Solar**: `20240914051558_IM_01008.JPG` → regex `r"^\d{14}_IM_\d{5}$"`

2. **EXIF metadat**:
   - Bunaty Micro 4K: Make="iCatch", Software="BUNATY_BV18AD_07"
   - Bunaty WiFi Solar: variabilní EXIF data

3. **Výsledný název složky**:
   - Příklad: `J:\Foto\JPG\knelts\2023\5\Bunaty WiFi Solar\`
   - Příklad: `J:\Foto\JPG\Abstrakty\2024\7\Bunaty Micro 4K\`

**Pro givenew je směrodatný název složky**, např. "Bunaty Micro 4K" nebo "Bunaty WiFi Solar".

## Analýza časového razítka

### Ukázka z fotopasti
Na základě ukázkové fotky z `J:\Foto\JPG\knelts\2023\5\Bunaty WiFi Solar\20230508100838_IM_00224.JPG`:

```
Časové razítko je umístěno:
- V pravém dolním rohu
- Světlý text na tmavém/transparentním podkladu
- Obsahuje datum a čas
- Výška pásu: cca 20-30 pixelů (nutno přesně změřit)
```

### Měření výšky ořezu

**TODO: Změřit přesnou výšku časového pásu z existujících fotek**

Postup měření:
1. Otevřít několik fotek z různých fotopastí v Photoshop/GIMP
2. Změřit výšku oblasti s časovým razítkem (v pixelech)
3. Vypočítat relativní výšku vůči celkové výšce fotky (%)
4. Určit bezpečnou výšku ořezu (s rezervou)

**Navržená konstanta:**
```python
# V givephotobankreadymediafileslib/constants.py
TRAIL_CAMERA_CROP_BOTTOM_PIXELS = 30  # Pixely k oříznutí ze spodku
# Nebo
TRAIL_CAMERA_CROP_BOTTOM_PERCENT = 0.02  # 2% výšky fotky
```

**Rozhodnutí:** Použít **absolutní pixely** nebo **procenta**?
- **Absolutní pixely**: jednodušší, ale nemusí fungovat pro různé rozlišení
- **Procenta**: flexibilnější, funguje pro jakékoli rozlišení
- **Doporučení**: Použít **absolutní pixely s kontrolou minimální výšky** (např. max 50px nebo 3% výšky)

## Implementace

### 1. Detekce fotopasti

V `givephotobankreadymediafiles/preparemediafile.py`:

```python
def is_trail_camera(file_path: str) -> bool:
    """
    Detekuje, zda fotka pochází z fotopasti na základě názvu složky.

    Args:
        file_path: Cesta k souboru

    Returns:
        True pokud fotka je z fotopasti (Bunaty), False jinak
    """
    # Konstanta s názvy fotopastí
    TRAIL_CAMERA_NAMES = ["Bunaty Micro 4K", "Bunaty WiFi Solar"]

    # Získat název rodičovské složky (název kamery)
    parent_folder = os.path.basename(os.path.dirname(file_path))

    return parent_folder in TRAIL_CAMERA_NAMES
```

### 2. Vytvoření _daterem verze

V `givephotobankreadymediafiles/givephotobankreadymediafileslib/alternative_generator.py`:

Přidat nový typ alternativy:

```python
def generate_daterem_version(self, source_path: str, output_dir: str) -> Optional[str]:
    """
    Vytvoří _daterem verzi fotky s oříznutým spodním pásem (časové razítko).

    Args:
        source_path: Cesta k originální fotce
        output_dir: Výstupní složka

    Returns:
        Cesta k vytvořenému souboru nebo None
    """
    from PIL import Image
    from givephotobankreadymediafileslib.constants import TRAIL_CAMERA_CROP_BOTTOM_PIXELS

    try:
        # Otevřít obrázek
        img = Image.open(source_path)
        width, height = img.size

        # Vypočítat výšku ořezu (max 3% nebo TRAIL_CAMERA_CROP_BOTTOM_PIXELS)
        crop_height = min(TRAIL_CAMERA_CROP_BOTTOM_PIXELS, int(height * 0.03))

        # Ořezat spodní část
        img_cropped = img.crop((0, 0, width, height - crop_height))

        # Vytvořit název souboru
        filename = os.path.basename(source_path)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_daterem{ext}"
        output_path = os.path.join(output_dir, new_filename)

        # Uložit
        img_cropped.save(output_path, quality=95, optimize=True)
        logging.info(f"Created _daterem version: {output_path} (cropped {crop_height}px from bottom)")

        return output_path

    except Exception as e:
        logging.error(f"Failed to create _daterem version for {source_path}: {e}")
        return None
```

### 3. Integrace do preparemediafile.py

V `preparemediafile.py`, po uložení originálních metadat (řádek ~167):

```python
# Po uložení originálních metadat, před generováním alternativ
if is_trail_camera(args.file):
    logging.info("Trail camera detected - creating _daterem version")

    # Vytvořit _daterem verzi
    target_dir, edited_dir = get_alternative_output_dirs(args.file)
    daterem_path = generate_daterem_version(args.file, edited_dir)

    if daterem_path:
        # Přidat _daterem verzi do CSV
        records = load_csv(args.media_csv)
        file_basename = os.path.basename(args.file)

        # Najít originální záznam
        original_record = None
        for record in records:
            if record.get(COL_FILE) == file_basename:
                original_record = record
                break

        if original_record:
            # 1. Změnit status originálu na "zamítnuto"
            for field_name in original_record.keys():
                if field_name.endswith(COL_STATUS_SUFFIX):
                    original_record[field_name] = STATUS_REJECTED
            logging.info(f"Set original trail camera photo to 'zamítnuto': {file_basename}")

            # 2. Vytvořit záznam pro _daterem verzi
            daterem_record = original_record.copy()
            daterem_filename = os.path.basename(daterem_path)
            daterem_record[COL_FILE] = daterem_filename
            daterem_record[COL_PATH] = daterem_path
            daterem_record[COL_ORIGINAL] = ORIGINAL_NO

            # Nastavit status na "připraveno"
            for field_name in daterem_record.keys():
                if field_name.endswith(COL_STATUS_SUFFIX):
                    if original_record[field_name].lower() == STATUS_UNPROCESSED.lower():
                        daterem_record[field_name] = STATUS_PREPARED

            # Přidat do CSV
            records.append(daterem_record)
            save_csv_with_backup(records, args.media_csv)
            logging.info(f"Added _daterem version to CSV with status 'připraveno': {daterem_filename}")
```

### 4. Ignorování přepínačů pro edited

**_daterem verze se provádí VŽDY pro fotopasti**, ignoruje přepínače:
- `--no-bw`
- `--no-negative`
- `--no-sharpen`
- atd.

Tyto přepínače ovlivňují **pouze běžné edited alternativy** (_bw, _negative, atd.), nikoli _daterem.

## Konstanty

V `givephotobankreadymediafileslib/constants.py`:

```python
# Trail camera detection and processing
TRAIL_CAMERA_NAMES = ["Bunaty Micro 4K", "Bunaty WiFi Solar"]
TRAIL_CAMERA_CROP_BOTTOM_PIXELS = 30  # TODO: Změřit přesnou hodnotu z existujících fotek
TRAIL_CAMERA_CROP_MAX_PERCENT = 0.03  # Maximum 3% výšky fotky
```

## Implementační kroky

- [ ] Změřit přesnou výšku časového pásu z existujících fotek Bunaty
- [ ] Určit optimální hodnotu konstanty `TRAIL_CAMERA_CROP_BOTTOM_PIXELS`
- [ ] Přidat konstanty do `givephotobankreadymediafileslib/constants.py`
- [ ] Vytvořit funkci `is_trail_camera(file_path)` v `preparemediafile.py`
- [ ] Vytvořit funkci `generate_daterem_version()` v `alternative_generator.py`
- [ ] Integrovat logiku do `preparemediafile.py` (po uložení metadat)
- [ ] Zajistit změnu statusu originálu na "zamítnuto"
- [ ] Zajistit nastavení statusu _daterem verze na "připraveno"
- [ ] Ověřit, že _daterem ignoruje přepínače pro edited varianty
- [ ] Otestovat na skutečných fotkách z obou fotopastí (Micro 4K a WiFi Solar)
- [ ] Otestovat s různými rozlišeními fotek
- [ ] Ověřit kvalitu ořezu (není vidět zbytek razítka)
- [ ] Napsat unit testy
- [ ] Aktualizovat dokumentaci

## Testování

### Testovací fotky
- `J:\Foto\JPG\knelts\2023\5\Bunaty WiFi Solar\20230508100838_IM_00224.JPG`
- `J:\Foto\JPG\Abstrakty\2024\7\Bunaty Micro 4K\PICT0195.JPG`

### Test scénáře
1. Spustit `preparemediafile.py` na fotce z fotopasti
2. Ověřit vytvoření _daterem verze v editované složce
3. Ověřit, že spodní razítko bylo odstraněno
4. Ověřit změnu statusu originálu na "zamítnuto" v CSV
5. Ověřit status _daterem verze jako "připraveno" v CSV
6. Ověřit, že metadata jsou zkopírována z originálu

## Poznámky

- _daterem verze **nemá vlastní metadata z AI** - používá metadata originálu (název, popis, klíčová slova)
- Pouze se mění fyzický soubor (oříznutí) a statusy
- Alternativní edited verze (_bw, _negative, atd.) se **negenerují pro _daterem** verzi
- Pro video soubory z fotopastí bude třeba použít FFmpeg pro ořez videa (zatím není v scope)

## Související soubory

- `givephotobankreadymediafiles/preparemediafile.py`
- `givephotobankreadymediafiles/givephotobankreadymediafileslib/alternative_generator.py`
- `givephotobankreadymediafiles/givephotobankreadymediafileslib/constants.py`
- `sortunsortedmedia/sortunsortedmedialib/constants.py` (referenční detekce fotopastí)