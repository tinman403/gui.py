# -*- coding: utf-8 -*-
# --- veri_isleme.py (Yeniden Düzenlenmiş ve Düzeltilmiş) ---

import pandas as pd
import openpyxl # Excel okumak için
import os
import sys
import json
from typing import Dict, Optional, Any, Tuple

# --- Yardımcı Fonksiyonlar ---

def get_resource_path(relative_path: str) -> str:
    """PyInstaller ile paketlendiğinde veya normal çalışırken dosya yolunu bulur."""
    try:
        # PyInstaller geçici klasörü
        base_path = sys._MEIPASS
    except Exception:
        # Normal çalışma: Bu dosyanın bulunduğu dizinin bir üst dizini (proje ana dizini)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

# --- Ayar Fonksiyonları ---

def load_settings(dosya_adi: str = "ayarlar.json") -> Dict[str, Any]:
    """Ayarlar dosyasını (varsayılan: ayarlar.json) yükler."""
    # Ayarlar dosyasının tam yolu (Proje ana dizininde arar)
    # Not: get_resource_path kullanmak yerine doğrudan göreceli yol kullanmak
    #      genellikle daha basittir, eğer PyInstaller kullanmayacaksanız.
    #      Şimdilik basit yolu kullanalım:
    try:
        # Ana proje dizinini bul (bu dosyanın olduğu yerin bir üstü)
        proje_dizini = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        ayarlar_dosyasi = os.path.join(proje_dizini, dosya_adi)
        print(f"Ayarlar dosyası aranıyor: {ayarlar_dosyasi}")
    except Exception:
         # Eğer dizin bulunamazsa, mevcut dizinde ara (daha az olası)
         ayarlar_dosyasi = dosya_adi


    # Varsayılan ayarlar (dosya bulunamazsa veya bozuksa kullanılır)
    varsayilan_ayarlar = {
        "ders_ayarlari": {},
        "gui_ayarlari": {"tema": "clam", "pencere_boyutu": "1200x700", "baslik": "Performans Değerlendirme Sistemi"},
        "genel_ayarlar": {"basari_siniri": 50, "eksik_veri_degeri": 0, "yazili_agirlik": 0.6, "proje_agirlik": 0.2}
    }

    try:
        # Dosya var mı kontrol et
        if not os.path.exists(ayarlar_dosyasi):
            print(f"Uyarı: Ayarlar dosyası bulunamadı: {ayarlar_dosyasi}. Varsayılan ayarlar kullanılacak ve oluşturulacak.")
            try:
                # Varsayılan ayarları içeren yeni bir dosya oluştur
                with open(ayarlar_dosyasi, 'w', encoding='utf-8') as f:
                    json.dump(varsayilan_ayarlar, f, ensure_ascii=False, indent=4)
                print(f"Varsayılan ayarlar dosyası oluşturuldu: {ayarlar_dosyasi}")
                return varsayilan_ayarlar
            except Exception as create_e:
                print(f"HATA: Varsayılan ayarlar dosyası oluşturulamadı: {create_e}")
                print("Varsayılan ayarlar bellekte kullanılacak.")
                return varsayilan_ayarlar # Yine de varsayılanı döndür

        # Dosya varsa oku
        with open(ayarlar_dosyasi, 'r', encoding='utf-8') as f:
            ayarlar = json.load(f)
            print("Ayarlar dosyası başarıyla okundu.")
            # Yüklenen ayarlarda eksik anahtarlar varsa varsayılanlarla tamamla (güvenlik için)
            for anahtar, deger in varsayilan_ayarlar.items():
                if anahtar not in ayarlar:
                    print(f"Uyarı: Ayarlarda '{anahtar}' bölümü eksik, varsayılan ekleniyor.")
                    ayarlar[anahtar] = deger
                elif isinstance(deger, dict): # Eğer bölüm bir sözlükse, içini de kontrol et
                     for alt_anahtar, alt_deger in deger.items():
                          if alt_anahtar not in ayarlar[anahtar]:
                               print(f"Uyarı: Ayarlarda '{anahtar}.{alt_anahtar}' ayarı eksik, varsayılan ekleniyor.")
                               ayarlar[anahtar][alt_anahtar] = alt_deger
            return ayarlar
    except json.JSONDecodeError:
        print(f"HATA: Ayarlar dosyası ({ayarlar_dosyasi}) geçersiz JSON formatında. Varsayılan ayarlar kullanılıyor.")
        return varsayilan_ayarlar
    except Exception as e:
        print(f"HATA: Ayarlar yüklenirken beklenmedik bir hata oluştu: {e}. Varsayılan ayarlar kullanılıyor.")
        return varsayilan_ayarlar

def save_settings(ayarlar: Dict[str, Any], dosya_adi: str = "ayarlar.json") -> bool:
    """Ayarları JSON dosyasına (varsayılan: ayarlar.json) kaydeder."""
    try:
        # Ana proje dizinini bul
        proje_dizini = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        ayarlar_dosyasi = os.path.join(proje_dizini, dosya_adi)
    except Exception:
         ayarlar_dosyasi = dosya_adi

    try:
        with open(ayarlar_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=4)
        print(f"Ayarlar başarıyla kaydedildi: {ayarlar_dosyasi}")
        return True
    except Exception as e:
        print(f"HATA: Ayarlar kaydedilirken bir hata oluştu: {e}")
        return False

# --- Veri Yükleme Fonksiyonu (Excel için) ---

def veri_yukle_excel(dosya_yolu: str, satir_atla: int = 15, sheet_name=0) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Belirtilen Excel (.xlsx) dosyasını okur, başlık satırlarını atlar ve temel sütunları yeniden adlandırır.
    DataFrame ve sınıf adı (sheet adından veya dosya adından) döndürür.

    Args:
        dosya_yolu (str): Okunacak Excel dosyasının yolu.
        satir_atla (int): Dosyanın başından atlanacak satır sayısı (0'dan başlar).
                         Başlık satırının BİR ÜSTÜNDEKİ satırın index'i.
                         Eğer başlıklar 16. satırdaysa, satir_atla=15 girilmelidir.
        sheet_name (int or str): Okunacak sayfanın indeksi (0) veya adı.

    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: (DataFrame, Sınıf Adı) veya (None, None)
    """
    print(f"Excel dosyası okunuyor: {dosya_yolu}, Atlanacak satır: {satir_atla}, Sayfa: {sheet_name}")
    try:
        # *** === KOLON EŞLEŞTİRME (DÜZELTİLDİ!) === ***
        # Bu sözlükteki anahtarlar (sol taraf) Excel'deki GERÇEK başlıklar olmalı.
        # Değerler (sağ taraf) program içinde kullanacağımız isimlerdir.
        kolon_eslestirme = {
            # Excel Başlığı : Programdaki Adı
            "Okul No"      : "Öğrenci No",
            "Adı Soyadı"   : "Ad Soyad",
            "Y1"           : "Y1",          # Düzeltildi (Önce "1. Yazılı" idi)
            "Y2"           : "Y2",          # Düzeltildi (Önce "2. Yazılı" idi)
            "P1"           : "Perf1",       # Düzeltildi (Önce "1. Performans" idi)
            "P2"           : "Perf2",       # Düzeltildi (Önce "2. Performans" idi)
            "D.ET.KAT."    : "DersEtKat",   # Düzeltildi (Önce "Ders Et. Kat." idi)
            "PROJE"        : "PROJE"
            # Başka sütunlar da almak isterseniz buraya ekleyebilirsiniz.
            # Örneğin: "Ortalama": "Eokul Ortalama" # e-Okul'un kendi ortalamasını almak için
        }
        # *** ======================================== ***
        print(f"Kullanılacak kolon eşleştirmesi: {kolon_eslestirme}")

        # Excel dosyasını oku
        # header=0: satir_atla kadar atladıktan SONRAKI ilk satırı başlık olarak kabul et.
        df = pd.read_excel(
            dosya_yolu,
            sheet_name=sheet_name,
            skiprows=satir_atla,
            header=0, # Atladıktan sonraki ilk satır başlık
            engine='openpyxl'
        )
        print(f"Dosya okundu, ilk satırlar (başlıktan sonra):\n{df.head()}")

        # Sütun adlarındaki baştaki/sondaki boşlukları temizle (çok önemli!)
        df.columns = df.columns.str.strip()
        print(f"Temizlenmiş sütun başlıkları: {df.columns.tolist()}")

        # Tamamen boş olan sütunları kaldır
        df.dropna(axis=1, how='all', inplace=True)

        # Gerekli sütunların varlığını kontrol et ve yeniden adlandırmak için hazırla
        kullanilacak_excel_sutunlari = list(kolon_eslestirme.keys())
        mevcut_excel_sutunlari = [col for col in kullanilacak_excel_sutunlari if col in df.columns]
        eksik_excel_sutunlari = [col for col in kullanilacak_excel_sutunlari if col not in df.columns]

        if eksik_excel_sutunlari:
            print(f"UYARI: Excel dosyasında şu beklenen sütunlar bulunamadı: {', '.join(eksik_excel_sutunlari)}")
            print("       Bu sütunlar olmadan devam edilecek.")

        if not mevcut_excel_sutunlari:
            # Eşleştirilecek hiçbir sütun bulunamadıysa, bu ciddi bir sorun.
            raise ValueError("Excel dosyasında eşleştirme için tanımlanan sütunların ('Okul No', 'Adı Soyadı', 'Y1' vb.) HİÇBİRİ bulunamadı! "
                             "'kolon_eslestirme' sözlüğünü veya 'Atlanacak Satır Sayısı'nı kontrol edin.")

        # Sadece bulunan ve eşleştirmede yer alan sütunları DataFrame'de tut
        df = df[mevcut_excel_sutunlari].copy()

        # Sütunları yeniden adlandır (program içindeki isimlere)
        # Sadece mevcut olanları yeniden adlandırmak için eşleştirmeyi filtrele:
        yeniden_adlandirma_map = {excel_col: program_col
                                  for excel_col, program_col in kolon_eslestirme.items()
                                  if excel_col in mevcut_excel_sutunlari}
        df.rename(columns=yeniden_adlandirma_map, inplace=True)
        print(f"Sütunlar yeniden adlandırıldı. Yeni sütunlar: {df.columns.tolist()}")

        # Sayısal olması gereken sütunları sayısal türe dönüştür
        # Program içinde kullanılacak standart adları buraya yazın
        sayisal_hedef_sutunlar = ["Öğrenci No", "Y1", "Y2", "Perf1", "Perf2", "DersEtKat", "PROJE"]
        for col in sayisal_hedef_sutunlar:
            if col in df.columns: # Sütun yeniden adlandırma sonrası var mı kontrol et
                print(f"'{col}' sütunu sayısal türe dönüştürülüyor...")
                # Önce str yapıp virgülü noktaya çevir (varsa), sonra numeric yap
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
                # errors='coerce': Sayıya çevrilemeyen değerleri NaN (Not a Number) yapar.
                if df[col].isnull().any():
                    print(f"   Uyarı: '{col}' sütununda sayıya dönüştürülemeyen bazı değerler bulundu ve boş bırakıldı (NaN).")

        # Eksik (NaN) sayısal değerleri 0 ile doldur (veya ayarlardan gelen değerle)
        try:
            ayarlar = load_settings()
            eksik_veri_degeri = ayarlar.get("genel_ayarlar", {}).get("eksik_veri_degeri", 0)
            # Özellikle sayısal olması gereken sütunlardaki NaN'ları dolduralım
            doldurulacak_sutunlar = [col for col in sayisal_hedef_sutunlar if col in df.columns]
            df[doldurulacak_sutunlar] = df[doldurulacak_sutunlar].fillna(eksik_veri_degeri)
            print(f"Eksik sayısal değerler '{eksik_veri_degeri}' ile dolduruldu.")
        except Exception as fill_e:
            print(f"HATA: Eksik veriler doldurulurken hata oluştu: {fill_e}. NaN değerler kalmış olabilir.")

        # Öğrenci No'ya göre sırala (isteğe bağlı)
        if "Öğrenci No" in df.columns:
            # Öğrenci No'yu integer yapmayı dene (hatalı veri varsa sorun çıkarabilir)
            try:
                 df["Öğrenci No"] = df["Öğrenci No"].astype(int)
                 df.sort_values(by="Öğrenci No", inplace=True)
                 print("Veriler Öğrenci No'ya göre sıralandı.")
            except ValueError:
                 print("Uyarı: Öğrenci No sütununda tam sayıya dönüştürülemeyen değerler var, sıralama yapılamadı.")
            except Exception as sort_e:
                 print(f"Sıralama sırasında hata: {sort_e}")


        # Sınıf/Sayfa adını belirle
        sinif_adi = "Bilinmeyen"
        try:
            excel_file = pd.ExcelFile(dosya_yolu, engine='openpyxl')
            if isinstance(sheet_name, int): # Eğer sayfa indeksi verildiyse
                if sheet_name < len(excel_file.sheet_names):
                    sinif_adi = excel_file.sheet_names[sheet_name]
                else: # Geçersiz indeks ise ilk sayfayı kullan
                    print(f"Uyarı: İstenen sayfa indeksi ({sheet_name}) geçersiz, ilk sayfa adı kullanılacak.")
                    sinif_adi = excel_file.sheet_names[0]
            elif isinstance(sheet_name, str): # Eğer sayfa adı verildiyse
                if sheet_name in excel_file.sheet_names:
                    sinif_adi = sheet_name
                else: # Geçersiz ad ise ilk sayfayı kullan
                     print(f"Uyarı: Belirtilen sayfa adı '{sheet_name}' bulunamadı, ilk sayfa adı kullanılacak.")
                     sinif_adi = excel_file.sheet_names[0]
            else: # Ne olduğu belli değilse ilk sayfayı kullan
                 sinif_adi = excel_file.sheet_names[0]
            excel_file.close() # Dosyayı kapat
            print(f"Sınıf/Sayfa adı belirlendi: '{sinif_adi}'")
        except Exception as e:
            print(f"Sayfa adından sınıf adı alınırken hata: {e}")
            # Alternatif: Dosya adından tahmin
            try:
                sinif_adi = os.path.basename(dosya_yolu).split('.')[0]
            except: pass # Tahmin de başarısız olursa "Bilinmeyen" kalır


        print(f"Veri yükleme tamamlandı. Sınıf/Sayfa: '{sinif_adi}', Öğrenci Sayısı: {len(df)}")
        # Başarıyla yüklenen DataFrame ve sınıf adını döndür
        return df, sinif_adi

    except FileNotFoundError:
        print(f"HATA: Dosya bulunamadı: {dosya_yolu}")
        return None, None # Hata durumunda None döndür
    except ValueError as e:
         # Genellikle sütun bulunamadığında veya tür dönüşümünde çıkar
         print(f"HATA: Veri işleme hatası (ValueError): {e}")
         return None, None
    except ImportError:
         print("HATA: 'openpyxl' kütüphanesi bulunamadı. Excel (.xlsx) okumak için gereklidir.")
         print("Lütfen terminalde 'pip install openpyxl' komutunu çalıştırın.")
         return None, None
    except Exception as e:
        # Diğer tüm beklenmedik hatalar (izinler, bozuk dosya vb.)
        import traceback
        print(f"HATA: Excel okuma/işleme sırasında beklenmedik bir hata oluştu: {e}")
        print(traceback.format_exc()) # Detaylı hata çıktısı için
        return None, None

# --- ESKİ, ARTIK KULLANILMAYAN FONKSİYONLAR BURADAN SİLİNDİ ---
# (veri_oku, veri_yaz, siniflara_ayir, performans_sutununu_bul vb.)
