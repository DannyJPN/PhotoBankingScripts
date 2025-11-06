# Issue #1: Refaktor markmediaaschecked - Změna cyklu z fotky→fotobanky na fotobanky→fotky

## Popis problému

Aktuální implementace skriptu `markmediaaschecked` prochází cyklem po jednotlivých fotkách a pro každou fotku se ptá na statusy pro všechny fotobanky. Tento přístup není vhodný z hlediska workflow:

- Uživatel musí neustále přepínat kontext mezi různými fotobankami při jedné fotce
- Není efektivní pro schvalování velkého množství fotek pro jednu konkrétní fotobanku
- Chybí možnost zpracovat jen jednu vybranou fotobanku

## Požadované změny

### 1. Otočení cyklů
Změnit logiku z:
```
FOR každá fotka:
    FOR každá fotobanka:
        Ptej se na status
```

Na:
```
FOR každá fotobanka:
    FOR každá fotka:
        Ptej se na status pro tuto fotobanku
```

### 2. Nový přepínač pro výběr fotobanky

Přidat přepínač `--bank` pro výběr konkrétní fotobanky, **totožným způsobem** jako je implementován v `exportpreparedmedia.py`:

```bash
# Příklady použití
python markmediaaschecked.py --shutterstock
python markmediaaschecked.py --adobestock --dreamstime
python markmediaaschecked.py --all
```

Podporované fotobanky (stejné jako v exportpreparedmedia):
- `--shutterstock`
- `--adobestock`
- `--dreamstime`
- `--depositphotos`
- `--bigstockphoto`
- `--123rf`
- `--canstockphoto`
- `--pond5`
- `--gettyimages`
- `--alamy`
- `--all` (zpracuje všechny)

### 3. Nový UI

Navrhnout a implementovat vhodné UI pro tento případ použití. Možnosti:

**Varianta A: Konzolové UI s přehledem**
```
=== SHUTTERSTOCK - Schvalování fotek ===
Nalezeno 143 fotek se statusem "připraveno"

[1/143] IMG_1234.JPG
Cesta: J:\Foto\JPG\Příroda\2024\5\Canon EOS R5\IMG_1234.JPG
Název: Beautiful sunset over the mountains
Popis: Stunning golden hour landscape with...

Schválit pro ShutterStock? [Y/n/s/q]:
  Y = Ano (změní status na "kontrolováno")
  n = Ne (ponechá status "připraveno")
  s = Skip (přeskočí fotku)
  q = Quit (ukončí skript)
```

**Varianta B: GUI okno** (podobné jako preparemediafile.py)
- Zobrazení náhledu fotky
- Informace o fotce (název, popis, klíčová slova, kategorie)
- Tlačítka: "Schválit", "Přeskočit", "Ukončit"

**Doporučení:** Začít s variantou A (konzolové UI) pro rychlost implementace, GUI lze přidat později.

## Technické detaily

### Soubory k úpravě

1. **`markmediaaschecked/markmediaaschecked.py`**
   - Přidat CLI argumenty pro jednotlivé fotobanky (zkopírovat z exportpreparedmedia.py řádky 52-73)
   - Přidat kontrolu `--all` vs. jednotlivé banky (řádky 88-107)
   - Změnit hlavní cyklus

2. **`markmediaaschecked/markmediaascheckedlib/mark_handler.py`**
   - Přidat funkci `get_enabled_banks(args)` (podobně jako v exportpreparedmedia)
   - Refaktorovat `update_statuses()` pro práci s jednou fotobankou najednou

3. **`markmediaaschecked/markmediaascheckedlib/constants.py`**
   - Přidat mapování názvů fotobank na názvy sloupců se statusy
   - Příklad: `BANK_STATUS_COLUMNS = {"shutterstock": "ShutterStock_status", ...}`

### Návrh nové logiky

```python
def main():
    args = parse_arguments()

    # Získání povolených fotobank
    enabled_banks = get_enabled_banks(args)
    if not enabled_banks:
        logging.warning("No banks enabled. Use --shutterstock, --adobestock, etc.")
        return

    # Načtení CSV
    all_records = load_csv(args.photo_csv_file)

    # Filtrování záznamů
    records_to_process = filter_records_by_edit_type(all_records, include_edited=args.include_edited)

    # Cyklus po fotobankách
    for bank_name in enabled_banks:
        status_column = get_status_column_for_bank(bank_name)

        # Filtrování záznamů se statusem "připraveno" pro tuto fotobanku
        bank_records = filter_ready_records_for_bank(records_to_process, status_column)

        if not bank_records:
            logging.info(f"No records with 'připraveno' status for {bank_name}")
            continue

        print(f"\n=== {bank_name.upper()} - Schvalování fotek ===")
        print(f"Nalezeno {len(bank_records)} fotek se statusem 'připraveno'\n")

        # Cyklus po fotkách pro tuto fotobanku
        approved_count = 0
        for i, record in enumerate(bank_records):
            # Zobrazit info o fotce
            print(f"\n[{i+1}/{len(bank_records)}] {record['Název souboru']}")
            print(f"Cesta: {record['Cesta']}")
            print(f"Název: {record.get('Název', 'N/A')}")
            print(f"Popis: {record.get('Popis', 'N/A')[:100]}...")

            # Ptát se na schválení
            response = input(f"\nSchválit pro {bank_name}? [Y/n/s/q]: ").strip().lower()

            if response == 'q':
                print("\nUkončuji...")
                break
            elif response == 's':
                print("Přeskakuji...")
                continue
            elif response in ['', 'y', 'yes', 'ano']:
                record[status_column] = STATUS_CHECKED
                approved_count += 1
                print("✓ Schváleno")
            else:
                print("Ponecháno bez změny")

        print(f"\n{bank_name}: Schváleno {approved_count} z {len(bank_records)} fotek")

    # Uložení CSV
    save_csv_with_backup(all_records, args.photo_csv_file)
    logging.info("Změny uloženy")
```

## Implementační kroky

- [ ] Prostudovat implementaci přepínačů fotobank v `exportpreparedmedia.py` (řádky 52-107)
- [ ] Přidat CLI argumenty do `markmediaaschecked.py`
- [ ] Vytvořit funkci `get_enabled_banks(args)` v `mark_handler.py`
- [ ] Vytvořit funkci `get_status_column_for_bank(bank_name)` v constants.py
- [ ] Vytvořit funkci `filter_ready_records_for_bank(records, status_column)` v `mark_handler.py`
- [ ] Refaktorovat hlavní logiku v `main()` - změnit cyklus na fotobanky→fotky
- [ ] Implementovat konzolové UI pro schvalování fotek
- [ ] Otestovat s různými kombinacemi přepínačů
- [ ] Otestovat zpětnou kompatibilitu s `--include-edited`
- [ ] Otestovat s `--all` přepínačem
- [ ] Napsat unit testy pro nové funkce
- [ ] Aktualizovat dokumentaci a README

## Poznámky

- Stávající přepínač `--include-edited` musí zůstat funkční
- Pokud není zadán žádný přepínač fotobanky, zobrazit warning stejně jako exportpreparedmedia
- Kontrolovat vzájemné vylučování `--all` a jednotlivých přepínačů fotobank
- UI by mělo být intuitivní a podporovat rychlé schvalování velkého množství fotek

## Související soubory

- `markmediaaschecked/markmediaaschecked.py`
- `markmediaaschecked/markmediaascheckedlib/mark_handler.py`
- `markmediaascheckedlib/constants.py`
- `exportpreparedmedia/exportpreparedmedia.py` (referenční implementace přepínačů)