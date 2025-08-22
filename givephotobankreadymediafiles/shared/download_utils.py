"""
Utility funkce pro stahování souborů s progress barem.
Tento modul poskytuje generické funkce pro stahování souborů z internetu,
které lze použít v jakémkoliv projektu.
"""

import logging
import os
from collections.abc import Callable

import requests
from tqdm import tqdm


def download_file(
    url: str,
    destination_path: str,
    chunk_size: int = 8192,
    timeout: int = 30,
    headers: dict[str, str] | None = None,
    show_progress: bool = True,
    description: str | None = None,
    callback: Callable[[int, int], None] | None = None,
    verify_ssl: bool = True,
    create_dirs: bool = True,
    overwrite: bool = False,
) -> bool:
    """
    Stáhne soubor z URL s progress barem a uloží ho do cílového umístění.

    Args:
        url: URL adresa souboru ke stažení
        destination_path: Cesta, kam má být soubor uložen
        chunk_size: Velikost chunků pro stahování (v bajtech)
        timeout: Timeout pro HTTP požadavek (v sekundách)
        headers: Volitelné HTTP hlavičky
        show_progress: Zda zobrazit progress bar
        description: Popis pro progress bar
        callback: Volitelná callback funkce, která dostane (staženo, celkem)
        verify_ssl: Zda ověřovat SSL certifikáty
        create_dirs: Zda vytvořit adresáře v cestě, pokud neexistují
        overwrite: Zda přepsat existující soubor

    Returns:
        True pokud bylo stahování úspěšné, jinak False
    """
    try:
        # Kontrola, zda soubor již existuje
        if os.path.exists(destination_path) and not overwrite:
            logging.info(f"Soubor již existuje: {destination_path}")
            return True

        # Vytvoření adresářů, pokud neexistují
        if create_dirs:
            os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)

        # Nastavení HTTP hlaviček
        if headers is None:
            headers = {}

        # Inicializace HTTP požadavku
        logging.info(f"Stahuji soubor z {url} do {destination_path}")
        response = requests.get(url, stream=True, headers=headers, timeout=timeout, verify=verify_ssl)
        response.raise_for_status()

        # Získání velikosti souboru
        total_size = int(response.headers.get("content-length", 0))

        # Nastavení progress baru
        progress_args = {
            "total": total_size,
            "unit": "B",
            "unit_scale": True,
            "unit_divisor": 1024,
        }

        if description:
            progress_args["desc"] = description
        else:
            progress_args["desc"] = f"Stahuji {os.path.basename(destination_path)}"

        # Stažení souboru s progress barem
        with open(destination_path, "wb") as f:
            if show_progress:
                with tqdm(**progress_args) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # filtrování keep-alive chunků
                            f.write(chunk)
                            downloaded = len(chunk)
                            pbar.update(downloaded)
                            if callback:
                                callback(pbar.n, total_size)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filtrování keep-alive chunků
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback:
                            callback(downloaded, total_size)

        logging.info(f"Stahování dokončeno: {destination_path}")
        return True

    except requests.exceptions.RequestException as e:
        logging.error(f"Chyba při stahování souboru {url}: {e}")
        # Odstranění částečně staženého souboru
        if os.path.exists(destination_path):
            try:
                os.remove(destination_path)
                logging.info(f"Odstraněn částečně stažený soubor: {destination_path}")
            except Exception as remove_error:
                logging.error(f"Nelze odstranit částečně stažený soubor: {remove_error}")
        return False

    except Exception as e:
        logging.error(f"Neočekávaná chyba při stahování souboru {url}: {e}")
        return False


def download_multiple_files(
    urls_and_paths: dict[str, str],
    show_progress: bool = True,
    headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
    create_dirs: bool = True,
    overwrite: bool = False,
) -> dict[str, bool]:
    """
    Stáhne více souborů s progress barem.

    Args:
        urls_and_paths: Slovník mapující URL na cílové cesty
        show_progress: Zda zobrazit progress bar
        headers: Volitelné HTTP hlavičky
        verify_ssl: Zda ověřovat SSL certifikáty
        create_dirs: Zda vytvořit adresáře v cestě, pokud neexistují
        overwrite: Zda přepsat existující soubory

    Returns:
        Slovník mapující URL na výsledek stahování (True/False)
    """
    results = {}

    for i, (url, path) in enumerate(urls_and_paths.items()):
        description = f"Soubor {i+1}/{len(urls_and_paths)}: {os.path.basename(path)}"
        result = download_file(
            url=url,
            destination_path=path,
            show_progress=show_progress,
            description=description,
            headers=headers,
            verify_ssl=verify_ssl,
            create_dirs=create_dirs,
            overwrite=overwrite,
        )
        results[url] = result

    # Výpis výsledků
    success_count = sum(1 for result in results.values() if result)
    logging.info(f"Stahování dokončeno: {success_count}/{len(urls_and_paths)} souborů úspěšně staženo")

    return results
