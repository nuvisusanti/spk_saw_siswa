import numpy as np

# 1. Inisialisasi Data Awal (Matriks X)
# Baris: Andi, Budi, Citra | Kolom: C1 (Rapor), C2 (Ekskul), C3 (Prestasi), C4 (Absensi)
X = np.array([
    [85, 75, 80, 2],
    [90, 80, 70, 1],
    [95, 85, 90, 0]
])

# 2. Definisikan Bobot (W) dan Jenis Atribut
W = np.array([0.40, 0.20, 0.25, 0.15])
is_benefit = [True, True, True, False] # C1,C2,C3 = Benefit | C4 = Cost

# 3. Proses Normalisasi Matriks (R)
R = np.zeros(X.shape)
for j in range(X.shape[1]):
    if is_benefit[j]:
        R[:, j] = X[:, j] / np.max(X[:, j])
    else:
        # Untuk menghindari pembagian dengan nol pada absensi 0, tambahkan handling khusus
        min_val = np.min(X[:, j])
        for i in range(X.shape[0]):
            R[i, j] = 1.0 if X[i, j] == 0 else (min_val + 1) / (X[i, j] + 1)

# 4. Perhitungan Nilai Preferensi Akhir (V)
V = np.dot(R, W)

# 5. Output Ranking Hasil
siswa = ["Andi", "Budi", "Citra"]
hasil = sorted(zip(siswa, V), key=lambda x: x[1], reverse=True)

print("--- HASIL REKOMENDASI SISWA BERPRESTASI (SAW) ---")
for rank, (nama, skor) in enumerate(hasil, 1):
    print(f"Peringkat {rank}: {nama} dengan Skor {skor:.4f}")
