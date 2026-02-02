import os
import sys
import requests
import locale
import time
from datetime import datetime
import pytz
from dotenv import load_dotenv
import concurrent.futures
from pathlib import Path
import warnings
import cfgrib
import logging

# Suppress warnings
warnings.filterwarnings('ignore')
logging.getLogger('cfgrib').setLevel(logging.ERROR)

def generate_idx(grib_path):
    """Generate .idx file for the GRIB file."""
    idx_path = grib_path + '.idx'
    try:
        # open_datasets is more robust for mixed files than open_file
        # We explicitly set the indexpath
        datasets = cfgrib.open_datasets(grib_path, backend_kwargs={'indexpath': idx_path})
        return True
    except Exception as e:
        # Even if opening fails due to dataset build issues, the index might have been created
        if os.path.exists(idx_path):
            return True
        print(f"⚠️  Failed to trigger index generation for {os.path.basename(grib_path)}: {e}")
        return False

def download_file(filename, target_dir, base_url, api_key):
    """Fungsi yang dijalankan oleh setiap thread untuk mengunduh satu file."""
    save_path = os.path.join(target_dir, filename)
    url = f"{base_url}/{filename}"

    # Cek sekali lagi jika file sudah ada (untuk menghindari race condition)
    if os.path.exists(save_path):
        # Generate idx if missing even if skipped
        if not os.path.exists(save_path + '.idx'):
             generate_idx(save_path)
        return {"status": "skipped", "filename": filename, "path": save_path}

    try:
        r = requests.get(
            url, headers={"spire-api-key": api_key}, stream=True, timeout=90)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Determine success
        status = "success"
        
        # Generate .idx after download
        generate_idx(save_path)

        return {"status": status, "filename": filename, "path": save_path}
    except requests.exceptions.RequestException as e:
        return {"status": "failed", "filename": filename, "error": str(e)}
    except Exception as e:
        return {"status": "failed", "filename": filename, "error": str(e)}

def main():
    """Skrip utama untuk mengunduh semua bundle file secara paralel."""
    try:
        locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
    except locale.Error:
        print("Peringatan: Locale 'id_ID.UTF-8' tidak terinstal. Menggunakan format default.")

    # 1. KONFIGURASI & SETUP
    load_dotenv()

    API_KEY = os.getenv("SPIRE_API_KEY")
    if not API_KEY:
        print("Error: Variabel SPIRE_API_KEY tidak ditemukan di file .env Anda.")
        return
    
    BASE_URL = "https://api.wx.spire.com/forecast/file"

    root_dir = os.getenv("SAVE_DIR_ROOT", "../grib_files/")
    SAVE_DIR_ROOT_GRIB = Path(root_dir) 
    SAVE_DIR_ROOT_GRIB.mkdir(parents=True, exist_ok=True)

    BUNDLES = ["core-v2", "upper-air", "thunderstorm", "derived"]
    
    # Worker count for downloading
    MAX_WORKERS = 20 

    # 2. TENTUKAN DIREKTORI PENYIMPANAN
    # Direktori tujuan: grib_files di root project
    root_dir = os.getenv("SAVE_DIR_ROOT", "../grib_files")
    SAVE_DIR_ROOT_GRIB = Path(root_dir)
    SAVE_DIR_ROOT_GRIB.mkdir(parents=True, exist_ok=True)
    
    # Download directly to grib_files (flat structure)
    target_dir_grib = str(SAVE_DIR_ROOT_GRIB)

    print(f"File GRIB2 akan disimpan di: {target_dir_grib}")

    # 3. AMBIL DAFTAR FILE DARI SEMUA BUNDLE
    all_filenames = set()
    print("\nMengambil daftar file dari semua bundle...")
    for bundle in BUNDLES:
        try:
            print(f"  - Mengambil bundle: '{bundle}'...")
            resp = requests.get(
                BASE_URL,
                params={"product": "srfs", "bundle": bundle,
                        "time_bundle": "hourly_6day"},
                headers={"spire-api-key": API_KEY},
                timeout=30
            )
            resp.raise_for_status()
            files_in_bundle = resp.json()["files"]
            all_filenames.update(files_in_bundle)
            print(f"    -> Ditemukan {len(files_in_bundle)} file.")
        except requests.exceptions.RequestException as e:
            print(f"    -> Gagal mengambil daftar file untuk bundle '{bundle}': {e}")

    if not all_filenames:
        print("\nTidak ada file untuk diunduh. Selesai.")
        return

    print(f"\nTotal file unik yang akan diunduh: {len(all_filenames)}")

    # 4. UNDUH SEMUA FILE SECARA PARALEL
    print("\n" + "="*60)
    print("TAHAP 1: DOWNLOAD FILE")
    print("="*60)
    print("Memulai proses unduhan paralel...")

    download_success = 0
    download_failed = 0
    download_skipped = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_filename = {
            executor.submit(download_file, filename, target_dir_grib, BASE_URL, API_KEY): filename 
            for filename in all_filenames
        }

        for future in concurrent.futures.as_completed(future_to_filename):
            result = future.result()

            if result['status'] == 'success':
                download_success += 1
                print(f"✅ Downloaded: {result['filename']}")
            elif result['status'] == 'skipped':
                download_skipped += 1
                print(f"⏭️  Skipped: {result['filename']} (already exists)")
            else:
                download_failed += 1
                print(f"❌ Failed: {result['filename']} -> {result.get('error', 'Unknown error')}")

    # 5. RINGKASAN
    print("\n" + "="*60)
    print("RINGKASAN PROSES DOWNLOAD")
    print("="*60)
    print(f"📥 Download: {download_success} berhasil, {download_failed} gagal, {download_skipped} dilewati")
    print(f"📂 Lokasi GRIB2: {target_dir_grib}")
    print("="*60)

    print("\n✅ Proses selesai.")

if __name__ == "__main__":
    main()
