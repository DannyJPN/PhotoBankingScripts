# Implementace logiky párování companion souborů (JPG ekvivalenty a originály)

## ✅ Status: IMPLEMENTOVÁNO

Datum implementace: 2025-10-25

## 📋 Popis změny

Implementována komplexní logika pro párování média s jejich companion soubory (JPG ekvivalenty pro alternativní formáty, originály pro editované verze). Tato změna dramaticky zlepšuje workflow třídění médií tím, že eliminuje duplicitní kategorizaci.

## 🎯 Cíl

Při třídění nezatříděných médií rozlišovat tři základní případy a chovat se podle následující logiky:

### 1. Neupravené originály (JPG a Video)

**JPG fotografie:**
- Vždy zobrazit GUI pro kategorizaci
- Uložit do: `Foto/JPG/kategorie/rok/měsíc/kamera/`
- Tyto soubory představují **kanonický zdroj pravdy** pro všechny obrazové varianty

**Videa:**
- Vždy zobrazit GUI pro kategorizaci
- Uložit do: `Video/{přípona}/kategorie/rok/měsíc/kamera/`
- Nemají kanonický formát - každé video se třídí samostatně

### 2. Alternativní formáty obrázků (PNG, RAW, TIFF, HEIC...)

**Pokud existuje JPG se stejným názvem:**
- ✅ Přeskočit GUI
- ✅ Použít metadata (kategorie, kamera) z JPG
- ✅ Uložit do: `Foto/{přípona}/kategorie/rok/měsíc/kamera/` (stejná hierarchie jako JPG)

**Pokud JPG neexistuje:**
- Zobrazit GUI pro kategorizaci (zpracovat jako JPG)
- Uložit do: `Foto/{přípona}/kategorie/rok/měsíc/kamera/`

### 3. Editované soubory (fotografie i videa)

**Pokud existuje originál:**
- ✅ Přeskočit GUI
- ✅ Použít metadata z originálu
- ✅ Uložit do zrcadlové struktury: `Upravené Foto/{přípona}/kategorie/rok/měsíc/kamera/`
  (nebo `Upravené Video/...`)

**Pokud originál neexistuje:**
- Zobrazit GUI pro kategorizaci (zpracovat jako nový editovaný originál)
- Uložit do: `Upravené Foto/{přípona}/kategorie/rok/měsíc/kamera/`

## 📂 Implementované soubory

### Nové soubory:

#### 1. `sortunsortedmedialib/companion_file_finder.py`
Nový modul obsahující:
- `find_jpg_equivalent(filename, target_folder)` - hledá JPG se stejným base názvem
- `find_original_file(edited_filename, target_folder, is_video)` - hledá originál pro editovaný soubor
- `extract_metadata_from_path(file_path)` - parsuje cestu a extrahuje kategorii, kameru, datum

#### 2. `tests/unit/test_companion_file_finder.py`
Kompletní unit testy pokrývající:
- Hledání JPG ekvivalentů (existuje/neexistuje)
- Case-insensitive přípony
- Hledání originálů pro fotografie
- Hledání originálů pro videa
- Extrakce metadat z různých typů cest

### Upravené soubory:

#### 3. `sortunsortedmedialib/path_builder.py`
Přidána nová funkce:
- `build_edited_target_path()` - stavba cest do struktury "Upravené Foto"/"Upravené Video"

#### 4. `sortunsortedmediafile.py`
Přepracována funkce `process_media_file()`:
- **Řádky 75-113**: Nová rozhodovací logika (Case A/B/C)
- **Řádky 115-141**: Podmíněné zobrazení GUI vs. použití metadat z companion souboru
- **Řádky 143-165**: Použití `build_edited_target_path()` pro editované soubory

## 🔄 Workflow diagram

```
Soubor ke zpracování
        │
        ├─── Je JPG nebo Video?
        │    └─── ANO → GUI kategorizace → Foto/JPG nebo Video/{ext}
        │
        ├─── Je alternativní formát (PNG, RAW...)?
        │    ├─── Existuje JPG?
        │    │    ├─── ANO → Použij metadata z JPG → Foto/{ext}/...
        │    │    └─── NE → GUI kategorizace → Foto/{ext}/...
        │
        └─── Je editovaný?
             ├─── Existuje originál?
             │    ├─── ANO → Použij metadata → Upravené Foto/{ext}/...
             │    └─── NE → GUI kategorizace → Upravené Foto/{ext}/...
```

## 📊 Příklady použití

### Příklad 1: RAW soubor s JPG ekvivalentem

**Vstup:**
- Zatříděno: `I:/Roztříděno/Foto/JPG/Příroda/2024/10/Canon/IMG_1234.JPG`
- Zpracováváme: `IMG_1234.ARW`

**Proces:**
1. Detekce: alternativní formát (RAW)
2. Hledání JPG: NALEZEN `Foto/JPG/Příroda/2024/10/Canon/IMG_1234.JPG`
3. **GUI: NE** ✅ (přeskočeno)
4. Extrakce metadat: `kategorie=Příroda, kamera=Canon`
5. Uložení: `I:/Roztříděno/Foto/ARW/Příroda/2024/10/Canon/IMG_1234.ARW`

### Příklad 2: Editovaný JPG s originálem

**Vstup:**
- Zatříděno: `I:/Roztříděno/Foto/JPG/Město/2024/9/Nikon/IMG_5678.JPG`
- Zpracováváme: `IMG_5678_bw.JPG`

**Proces:**
1. Detekce: editovaný soubor (tag "_bw")
2. Hledání originálu: NALEZEN `Foto/JPG/Město/2024/9/Nikon/IMG_5678.JPG`
3. **GUI: NE** ✅ (přeskočeno)
4. Extrakce metadat: `kategorie=Město, kamera=Nikon`
5. Uložení: `I:/Roztříděno/Upravené Foto/JPG/Město/2024/9/Nikon/IMG_5678_bw.JPG`

### Příklad 3: PNG bez JPG ekvivalentu

**Vstup:**
- Zpracováváme: `SCREENSHOT_2024.PNG`

**Proces:**
1. Detekce: alternativní formát (PNG)
2. Hledání JPG: NENALEZEN
3. **GUI: ANO** 📋 (uživatel kategorizuje jako nový soubor)
4. Uživatel vybere: `kategorie=Práce, kamera=Unknown`
5. Uložení: `I:/Roztříděno/Foto/PNG/Práce/2024/10/Unknown/SCREENSHOT_2024.PNG`

## ⚙️ Technické detaily

### Hledání JPG ekvivalentu

```python
def find_jpg_equivalent(filename: str, target_folder: str) -> Optional[str]:
    base_name = os.path.splitext(filename)[0]  # "IMG_1234"
    jpg_extensions = ['.JPG', '.jpg', '.JPEG', '.jpeg']

    # Rekurzivně hledá v Foto/JPG/
    for root, dirs, files in os.walk(os.path.join(target_folder, 'Foto', 'JPG')):
        for file in files:
            if os.path.splitext(file)[0] == base_name and os.path.splitext(file)[1] in jpg_extensions:
                return os.path.join(root, file)
    return None
```

### Hledání originálu pro editované

```python
def find_original_file(edited_filename: str, target_folder: str, is_video: bool) -> Optional[str]:
    # Odstraní edit tagy (_bw, _edited, _cut...) z názvu
    original_base_name = remove_edit_tags(edited_filename)

    if is_video:
        # Hledá v Video/
        search_root = os.path.join(target_folder, 'Video')
    else:
        # Hledá v Foto/JPG/ nebo Foto/{stejná přípona}/
        search_roots = [
            os.path.join(target_folder, 'Foto', 'JPG'),
            os.path.join(target_folder, 'Foto', file_ext.upper())
        ]
    # ...rekurzivní hledání
```

### Extrakce metadat z cesty

```python
def extract_metadata_from_path(file_path: str) -> Dict[str, str]:
    # Parsuje: .../Foto/JPG/Příroda/2024/10/Canon EOS R5/IMG.JPG
    # Vrací: {'category': 'Příroda', 'camera_name': 'Canon EOS R5', 'year': '2024', 'month': '10'}

    path_parts = Path(file_path).parts
    # Najde index "Foto" nebo "Video"
    # Extrahuje category = parts[media_type_idx + 2]
    # Extrahuje camera = parts[media_type_idx + 5]
    # ...
```

## 🧪 Testování

### Spuštění unit testů

```bash
cd F:\Dropbox\Scripts\Python\Fotobanking\sortunsortedmedia
python -m pytest tests/unit/test_companion_file_finder.py -v
```

### Manuální testovací případy

**Test 1: JPG originál**
```bash
python sortunsortedmediafile.py --media_file "I:\Neroztříděno\IMG_1234.JPG"
# Očekáváno: GUI zobrazeno, soubor uložen do Foto/JPG/
```

**Test 2: PNG s JPG ekvivalentem**
```bash
# Předpoklad: IMG_1234.JPG už je v Foto/JPG/Příroda/2024/10/Canon/
python sortunsortedmediafile.py --media_file "I:\Neroztříděno\IMG_1234.PNG"
# Očekáváno: GUI PŘESKOČENO, soubor uložen do Foto/PNG/Příroda/2024/10/Canon/
```

**Test 3: RAW bez JPG**
```bash
python sortunsortedmediafile.py --media_file "I:\Neroztříděno\IMG_9999.ARW"
# Očekáváno: GUI zobrazeno, soubor uložen do Foto/ARW/
```

**Test 4: Editovaný JPG s originálem**
```bash
# Předpoklad: IMG_5678.JPG už je v Foto/JPG/Město/2024/9/Nikon/
python sortunsortedmediafile.py --media_file "I:\Neroztříděno\IMG_5678_bw.JPG"
# Očekáváno: GUI PŘESKOČENO, soubor uložen do Upravené Foto/JPG/Město/2024/9/Nikon/
```

**Test 5: Editované video bez originálu**
```bash
python sortunsortedmediafile.py --media_file "I:\Neroztříděno\VID_1111_cut.MP4"
# Očekáváno: GUI zobrazeno, soubor uložen do Upravené Video/MP4/
```

## ⚠️ Známé limitace

1. **Hledání je case-sensitive pro base name**: `IMG_1234.JPG` a `img_1234.JPG` jsou považovány za různé soubory
2. **Přípony jsou case-insensitive**: `.JPG`, `.jpg`, `.JPEG`, `.jpeg` jsou ekvivalentní
3. **Výkon**: Pro velké složky může hledání trvat déle (rekurzivní walk)
4. **Edit tagy**: Pouze tagy v `EDITED_TAGS` z constants.py jsou rozpoznány

## 📈 Výhody

✅ **Eliminace duplicitní kategorizace**: PNG/RAW s JPG se již neptá uživatele
✅ **Automatické párování editovaných**: Editované verze se ukládají vedle originálů
✅ **Konzistence metadat**: Všechny varianty jednoho média mají stejnou kategorii
✅ **Úspora času**: Méně klikání pro uživatele
✅ **Čistší struktura**: Editované v samostatné větvi "Upravené"

## 🔧 Údržba

### Přidání nového edit tagu

Editovat `sortunsortedmedialib/constants.py`:
```python
EDITED_TAGS = {
    "_bw": "Black and White",
    "_edited": "Generic Edit",
    "_cut": "Video Cut",
    "_new_tag": "New Edit Type",  # ← přidat zde
}
```

### Změna struktury složek

Upravit `build_target_path()` a `build_edited_target_path()` v `path_builder.py`.

## 📝 Související issue

- Issue #1: Refactor markmediaaschecked
- Issue #2: Automatické oříznutí fotopastí Bunaty
- Issue #3: Batch režim pro givenew
- Issue #4: Rozšíření přečíslování z PICT na NIK_

## 👥 Autor

Implementováno Claude Code na základě specifikace uživatele.