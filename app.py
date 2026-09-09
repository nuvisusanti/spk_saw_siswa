import plotly.express as px
import streamlit as st
import numpy as np
import pandas as pd
import io
import sqlite3

# ==============================================================================
# 1. KONFIGURASI HALAMAN UTAMA WEBSITE
# ==============================================================================
st.set_page_config(page_title="SPK Siswa Berprestasi", page_icon="🏆", layout="wide")

# ==============================================================================
# 2. SISTEM MANAJEMEN BASIS DATA (DATABASE SQLITE)
# ==============================================================================
def init_db():
    """Membuat file database 'spk_saw.db' dan tabel siswa jika belum ada"""
    conn = sqlite3.connect("spk_saw.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS siswa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            c1 REAL NOT NULL,
            c2 REAL NOT NULL,
            c3 REAL NOT NULL,
            c4 REAL NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM siswa")
    if cursor.fetchone()[0] == 0:
        data_default = [
            ("Andi", 85.0, 75.0, 80.0, 2.0),
            ("Budi", 90.0, 80.0, 70.0, 0.0),
            ("Citra", 88.0, 95.0, 90.0, 1.0)
        ]
        cursor.executemany("INSERT INTO siswa (nama, c1, c2, c3, c4) VALUES (?, ?, ?, ?, ?)", data_default)
        conn.commit()
    conn.close()

def load_data():
    """Mengambil data siswa dari database untuk ditampilkan ke tabel website"""
    conn = sqlite3.connect("spk_saw.db")
    df = pd.read_sql_query(
        "SELECT nama AS 'Nama Siswa', c1 AS 'C1 (Rapor)', c2 AS 'C2 (Ekskul)', c3 AS 'C3 (Prestasi)', c4 AS 'C4 (Absensi)' FROM siswa", 
        conn
    )
    conn.close()
    return df

def save_data(df_edited):
    """Menyimpan data hasil perubahan dari website kembali ke database secara permanen"""
    conn = sqlite3.connect("spk_saw.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM siswa")
    for _, row in df_edited.iterrows():
        if pd.notna(row["Nama Siswa"]) and str(row["Nama Siswa"]).strip() != "":
            cursor.execute(
                "INSERT INTO siswa (nama, c1, c2, c3, c4) VALUES (?, ?, ?, ?, ?)",
                (row["Nama Siswa"], float(row["C1 (Rapor)"]), float(row["C2 (Ekskul)"]), float(row["C3 (Prestasi)"]), float(row["C4 (Absensi)"]))
            )
    conn.commit()
    conn.close()

# Jalankan database di latar belakang
init_db()

# ==============================================================================
# 3. SISTEM KEAMANAN & MANAJEMEN AKSES (LOGIN SESSION)
# ==============================================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def Halaman_Login():
    """Menampilkan antarmuka formulir login di tengah layar website"""
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔐 Login Sistem Portal SPK SAW</h2>", unsafe_allow_html=True)
    col_kiri, col_tengah, col_kanan = st.columns([1, 2, 1])
    with col_tengah:
        username = st.text_input("Username / ID Pengguna", placeholder="Masukkan username", key="login_username")
        password = st.text_input("Password / Kata Sandi", type="password", placeholder="Masukkan password", key="login_password")
        if st.button("Masuk Ke Sistem", type="primary", use_container_width=True, key="btn_login"):
            if username == "admin" and password == "sekolah123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Kredensial Salah! Pastikan Username 'admin' & Password 'sekolah123'")

# ==============================================================================
# 4. ALUR UTAMA HALAMAN INTERN WEBSITE SPK
# ==============================================================================
if not st.session_state["logged_in"]:
    Halaman_Login()
else:
    # Desain CSS Kustom untuk memperindah tampilan
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stButton>button { border-radius: 8px; font-weight: 600; }
        .stDataFrame { border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1, h2, h3 { color: #1E3A8A; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        </style>
    """, unsafe_allow_html=True)

    # Kontrol Keluar Sistem di Sidebar
    with st.sidebar:
        st.markdown("### 👤 Sesi Aktif: Admin")
        if st.button("🚪 Keluar (Log Out)", type="secondary", use_container_width=True, key="btn_logout"):
            st.session_state["logged_in"] = False
            st.session_state["calculated"] = False  # Reset hasil kalkulasi saat logout
            st.rerun()
        st.markdown("---")

    # Judul Utama Dashboard
    st.title("🏆 Dashboard Pemilihan Siswa Berprestasi Utama")
    st.markdown("Aplikasi platform penilai objektif menggunakan integrasi algoritma **Simple Additive Weighting (SAW)**.")
    st.markdown("---")

    # --------------------------------------------------------------------------
    # KONFIGURASI BOBOT DI SIDEBAR
    # --------------------------------------------------------------------------
    st.sidebar.header("🛠️ Panel Pengaturan Bobot")
    st.sidebar.markdown("Sesuaikan persentase kepentingan nilai kriteria di bawah ini:")

    w1 = st.sidebar.slider("C1: Nilai Rapor (%)", 0, 100, 40, key="slider_c1") / 100
    w2 = st.sidebar.slider("C2: Ekstrakurikuler (%)", 0, 100, 20, key="slider_c2") / 100
    w3 = st.sidebar.slider("C3: Prestasi/Lomba (%)", 0, 100, 25, key="slider_c3") / 100
    w4 = st.sidebar.slider("C4: Absensi (Ketidakhadiran) (%)", 0, 100, 15, key="slider_c4") / 100

    total_bobot = round(w1 + w2 + w3 + w4, 2)
    if total_bobot != 1.0:
        st.sidebar.error(f"⚠️ Total kombinasi bobot Anda: {total_bobot*100:.0f}%. Angka akumulasi wajib menyentuh nilai 100%!")
    else:
        st.sidebar.success("✅ Akumulasi Bobot Tepat 100%")

    # --------------------------------------------------------------------------
    # STRUKTUR TABS INTERAKTIF
    # --------------------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "📋 1. Lembar Manajemen Nilai", 
        "🔄 2. Matriks Normalisasi (R)", 
        "🏆 3. Hasil Perankingan Akhir"
    ])

    # --- TAB 1: MANAJEMEN DATA ---
    with tab1:
        st.subheader("Lembar Manajemen Nilai Mentah Siswa")
        st.caption("💡 Anda bisa mengetik langsung nilai baru atau menambah baris siswa di bagian bawah tabel.")
        
        df_siswa = load_data()
        edited_df = st.data_editor(df_siswa, num_rows="dynamic", use_container_width=True, key="data_editor_siswa")
        
        st.markdown("###")
        proses_hitung = st.button("🚀 Jalankan Kalkulasi Algoritma SAW", type="primary", use_container_width=True, key="btn_kalkulasi")

    # Logika Matematika Perhitungan SAW
    if proses_hitung:
        if total_bobot != 1.0:
            st.error("Proses kalkulasi ditolak. Silakan sesuaikan bobot kriteria pada panel sidebar hingga berjumlah tepat 100%.")
        elif edited_df.empty:
            st.error("Gagal memproses data. Tabel nilai mentah siswa tidak boleh kosong.")
        else:
            save_data(edited_df)
            
            # Ekstraksi array numerik dari dataframe
            X = edited_df[["C1 (Rapor)", "C2 (Ekskul)", "C3 (Prestasi)", "C4 (Absensi)"]].to_numpy()
            nama_siswa = edited_df["Nama Siswa"].tolist()
            W = np.array([w1, w2, w3, w4])
            is_benefit = [True, True, True, False] # C1, C2, C3 = Benefit | C4 = Cost
            
            # --- TAHAP 1: NORMALISASI MATRIKS (R) ---
            R = np.zeros(X.shape)
            for j in range(X.shape[1]):
                if is_benefit[j]:
                    max_val = np.max(X[:, j])
                    R[:, j] = X[:, j] / max_val if max_val != 0 else 0
                else:
                    min_val = np.min(X[:, j])
                    for i in range(X.shape[0]):
                        R[i, j] = 1.0 if X[i, j] == 0 else (min_val + 1) / (X[i, j] + 1)

            # --- TAHAP 2: PENJUMLAHAN TERBOBOT (V) ---
            V = np.dot(R, W)
            
            # Simpan hasil ke Session State agar tidak hilang saat berpindah tab
            st.session_state["calculated"] = True
            st.session_state["nama_siswa"] = nama_siswa
            st.session_state["R_matrix"] = R
            st.session_state["V_scores"] = V

    # --- MENAMPILKAN HASIL PADA TAB 2 DAN TAB 3 ---
    if st.session_state.get("calculated", False):
        nama_siswa_cache = st.session_state["nama_siswa"]
        R_cache = st.session_state["R_matrix"]
        V_cache = st.session_state["V_scores"]

         # --- TAB 2: MATRIKS NORMALISASI ---
        with tab2:
            st.subheader("Hasil Normalisasi Matriks Keputusan (R)")
            df_normalisasi = pd.DataFrame(R_cache, columns=["C1 (Rapor)", "C2 (Ekskul)", "C3 (Prestasi)", "C4 (Absensi)"])
            df_normalisasi.insert(0, "Nama Siswa", nama_siswa_cache)
            st.dataframe(df_normalisasi.style.format(precision=3), use_container_width=True)

        # --- TAB 3: PERANKINGAN AKHIR & VISUALISASI ---
        with tab3:
            df_hasil = pd.DataFrame({"Nama Siswa": nama_siswa_cache, "Skor Akhir (V)": V_cache})
            df_hasil = df_hasil.sort_values(by="Skor Akhir (V)", ascending=False).reset_index(drop=True)
            
            df_tabel = df_hasil.copy()
            df_tabel.index += 1  # Penomoran rangking dimulai dari angka 1

            siswa_terbaik = df_hasil.iloc[0]["Nama Siswa"]
            skor_terbaik = df_hasil.iloc[0]["Skor Akhir (V)"]
            
            col_info, col_metric = st.columns(2)
            with col_info:
                st.subheader("Rekomendasi Hasil Akhir Perankingan")
                st.markdown(f"Berdasarkan akumulasi perhitungan bobot, sistem menetapkan siswa terbaik yang menjadi kandidat utama.")
            with col_metric:
                st.metric(label="🥇 Siswa Berprestasi Utama", value=siswa_terbaik, delta=f"{skor_terbaik:.4f} Skor")

            # Layout Berdampingan untuk Tabel dan Grafik Bar Chart
            col_table, col_chart = st.columns(2)
            with col_table:
                st.markdown("**Tabel Peringkat Resmi**")
                st.dataframe(df_tabel.style.format({"Skor Akhir (V)": "{:.4f}"}), use_container_width=True)
            with col_chart:
                st.markdown("**Grafik Perbandingan Nilai Akhir**")
                st.bar_chart(data=df_hasil, x="Nama Siswa", y="Skor Akhir (V)", color="#1E3A8A", use_container_width=True)

            # Fitur Unduh Hasil Peringkat ke File CSV
            csv_buffer = io.StringIO()
            df_tabel.to_csv(csv_buffer, index=True)
            st.download_button(
                label="📥 Unduh Laporan Peringkat (CSV)",
                data=csv_buffer.getvalue(),
                file_name="Laporan_SPK_Siswa_Berprestasi.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_download_csv"
            )