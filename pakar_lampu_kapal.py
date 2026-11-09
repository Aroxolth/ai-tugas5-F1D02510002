"""Sistem pakar sederhana: mengenali jenis kapal dari lampu navigasi di malam hari (COLREGs).

Metode : forward chaining (mesin ditulis sendiri, tanpa library inferensi).
Aturan : dibaca dari kb_lampu_kapal.json.
Jalankan: python pakar_lampu_kapal.py
Opsional: python pakar_lampu_kapal.py --ya 1,2   (jawab "ya" untuk pertanyaan nomor 1 dan 2, tanpa tanya)
"""
import json
import sys
from pathlib import Path

FILE_ATURAN = Path(__file__).with_name("kb_lampu_kapal.json")


def muat(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fakta_dasar(aturan):
    """Fakta yang tidak pernah menjadi hasil aturan, jadi harus ditanyakan ke user."""
    hasil = {r["maka"] for r in aturan}
    urut = []
    for r in aturan:
        for f in r["jika"] + r.get("kecuali", []):
            if f not in hasil and f not in urut:
                urut.append(f)
    return urut


def terpenuhi(r, memori):
    """Syarat 'jika' terpenuhi (dan/atau) dan tidak ada fakta 'kecuali' di memori."""
    ada = [f for f in r["jika"] if f in memori]
    if r["mode"] == "dan":
        syarat_ok = len(ada) == len(r["jika"])
    else:
        syarat_ok = len(ada) > 0
    terblokir = any(f in memori for f in r.get("kecuali", []))
    return syarat_ok and not terblokir


def forward_chaining(aturan, fakta_awal):
    memori = set(fakta_awal)
    asal = {}  # hasil -> aturan yang menghasilkannya (bahan "alasan")
    log = []
    while True:
        cocok = [r for r in aturan if r["maka"] not in memori and terpenuhi(r, memori)]
        if not cocok:
            break
        r = cocok[0]  # ambil aturan pertama
        memori.add(r["maka"])
        asal[r["maka"]] = r
        log.append(r)
    return memori, asal, log


def cetak_alasan(fakta, asal, memori, tingkat=1):
    r = asal[fakta]
    dipakai = [f for f in r["jika"] if f in memori]
    tambahan = "; tanpa pengecualian" if r.get("kecuali") else ""
    print("  " * tingkat + f"{fakta}  <- {r['id']} ({', '.join(dipakai)}{tambahan}) [{', '.join(r['sumber'])}]")
    for f in dipakai:
        if f in asal:
            cetak_alasan(f, asal, memori, tingkat + 1)


def tanya(teks):
    while True:
        try:
            j = input(teks + " (y/t) > ").strip().lower()
        except EOFError:
            return False
        if j in ("y", "ya"):
            return True
        if j in ("t", "tidak"):
            return False
        print("Jawab y atau t.")


def main():
    data = muat(FILE_ATURAN)
    aturan = data["aturan"]
    pertanyaan = fakta_dasar(aturan)

    print(data["judul"])
    ya_otomatis = None
    if "--ya" in sys.argv:
        angka = sys.argv[sys.argv.index("--ya") + 1]
        ya_otomatis = {int(x) for x in angka.split(",") if x.strip()}
    else:
        print("Jawab y/t.")

    fakta_awal = []
    for i, f in enumerate(pertanyaan, 1):
        teks = data["pertanyaan"][f]
        if ya_otomatis is None:
            jawab = tanya(f"{i}. {teks}")
        else:
            jawab = i in ya_otomatis
            print(f"{i}. {teks} (y/t) > {'y' if jawab else 't'}")
        if jawab:
            fakta_awal.append(f)

    print()
    print("Fakta awal:", ", ".join(fakta_awal) if fakta_awal else "(tidak ada)")
    print()

    memori, asal, log = forward_chaining(aturan, fakta_awal)
    for n, r in enumerate(log, 1):
        print(f"Siklus {n}: {r['id']} -> {r['maka']}")
    print(f"Siklus {len(log) + 1}: tidak ada aturan baru, berhenti")
    print()

    hasil = [k for k in data["kesimpulan"] if k in memori]
    if hasil:
        for k in hasil:
            print(f"Kesimpulan: {k}")
            print(f"Saran: {data['kesimpulan'][k]}")
            print("Alasan:")
            cetak_alasan(k, asal, memori)
            print()
    else:
        print("Kesimpulan: tidak ada aturan yang cocok dengan fakta yang dijawab.")
        print("Alasan: tidak ada aturan yang syaratnya terpenuhi.")
        print()

    print("Catatan:", data["batas"])


if __name__ == "__main__":
    main()
