# -*- coding: utf-8 -*-
# --- gui.py ---
# Bu dosya, Performans Değerlendirme Uygulamasının
# ana grafik arayüzünü (GUI) içerir.
# Kodun tamamı tutarlı 4 boşluk girintileme ile yazılmıştır.
# Lütfen yapıştırırken mevcut içeriği tamamen silin.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, Frame, Label, Entry, Button, PanedWindow, Scrollbar, Canvas, Toplevel
import pandas as pd
import os
import sys
import copy # Ayarlar düzenleme için derin kopya
from typing import Dict, List, Optional, Any, Tuple

# --- Modül Importları ---
try:
    # modules klasörünün main.py ile aynı dizinde olduğunu varsayıyoruz
    from modules import veri_isleme
    from modules import hesaplamalar
    # Raporlama modülü ileride kullanılabilir
    # from modules import raporlama
except ImportError as import_err:
    # Eğer modüller bulunamazsa kullanıcıyı bilgilendir ve çık
    # Bu hatayı görmek için önce Tkinter'in başlaması gerekebilir,
    # bu yüzden ana kod bloğunda tekrar kontrol edilebilir.
    print(f"Kritik Hata: Modüller yüklenemedi: {import_err}")
    print("Lütfen 'modules' klasörünün ve içindeki .py dosyalarının doğru yerde olduğundan emin olun.")
    # GUI başlamadan hata vermek için Tkinter kullanmak yerine doğrudan çıkalım
    sys.exit(f"Modül Hatası: {import_err}")

# --- Ana Uygulama Sınıfı ---
class PerformansYonetimApp:
    """Performans değerlendirme ana uygulama sınıfı."""

    def __init__(self, root: tk.Tk) -> None:
        """Uygulama penceresini başlatır ve ayarlar."""
        self.root = root
        print("PerformansYonetimApp __init__ başlatıldı.")

        # --- Ayarları Yükle (Başlangıçta) ---
        try:
            # veri_isleme modülündeki fonksiyonu kullan
            self.ayarlar = veri_isleme.load_settings()
            print("Ayarlar başarıyla yüklendi.")
            # Gerekli anahtarların varlığını kontrol et (opsiyonel ama güvenli)
            if not all(k in self.ayarlar for k in ["ders_ayarlari", "gui_ayarlari", "genel_ayarlar"]):
                print("Uyarı: Ayarlar dosyasında bazı ana bölümler eksik, varsayılanlarla tamamlanacak.")
                # Eksikleri tamamlama load_settings içinde yapılıyor olmalı.
        except Exception as e:
            print(f"Kritik Hata: Ayarlar yüklenemedi! Hata: {e}")
            messagebox.showerror("Kritik Hata", f"Ayarlar dosyası ('ayarlar.json') yüklenemedi veya bozuk:\n{e}\nUygulama başlatılamıyor.")
            self.root.destroy() # Ayarlar yüklenemezse başlama
            return

        # --- Ana Pencere Özellikleri ---
        try:
            gui_ayarlari = self.ayarlar.get("gui_ayarlari", {})
            baslik = gui_ayarlari.get("baslik", "Performans Değerlendirme Sistemi")
            boyut = gui_ayarlari.get("pencere_boyutu", "1200x700")
            tema = gui_ayarlari.get("tema", "clam")

            self.root.title(baslik)
            self.root.geometry(boyut)
            self.root.resizable(True, True)
            self.root.minsize(900, 500)
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            print("Pencere ayarları uygulandı.")

            # Tema Ayarı
            self.style = ttk.Style()
            available_themes = self.style.theme_names()
            if tema in available_themes:
                self.style.theme_use(tema)
                print(f"Tema ayarlandı: {tema}")
            else:
                print(f"Uyarı: Ayarlardaki tema '{tema}' bulunamadı. Varsayılan tema kullanılıyor.")
                # Kullanılabilir bir tema bulmaya çalış
                use_theme = "clam" # Varsayılan
                if "clam" in available_themes: use_theme = "clam"
                elif "vista" in available_themes: use_theme = "vista" # Windows için alternatif
                elif "aqua" in available_themes: use_theme = "aqua" # MacOS için alternatif
                elif available_themes: use_theme = available_themes[0] # İlk bulduğunu kullan
                self.style.theme_use(use_theme)
                print(f"Kullanılan tema: {use_theme}")

        except Exception as e:
            print(f"Pencere veya tema ayarları uygulanırken hata: {e}")
            # Hata olsa bile varsayılanlarla devam etmeye çalış
            self.root.title("Performans Değerlendirme Sistemi")
            self.root.geometry("1200x700")


        # --- Uygulama Veri ve Durum Değişkenleri ---
        self.df = pd.DataFrame()                 # Yüklü öğrenci verileri
        self.mevcut_dosya_yolu: Optional[str] = None # Yüklenen dosyanın yolu
        self.mevcut_sinif_adi: Optional[str] = None  # Yüklenen sınıf/sayfa adı
        self.mevcut_ders: Optional[str] = None       # Seçili ders adı
        self.secili_ogrenci_index: Optional[int] = None # Treeview'de seçili öğrencinin df index'i

        # Kriter giriş alanlarını (Entry) tutacak sözlük {kriter_adı: entry_widget}
        self.kriter_entry_widgets: Dict[str, ttk.Entry] = {}
        # Ayarlar penceresi için geçici ayarlar (düzenleme sırasında kullanılır)
        self.gecici_ayarlar: Dict = {}
        # Ayarlar penceresindeki dinamik widget'lar için (dersler)
        self.ders_widgets: Dict[str, Dict[str, Any]] = {}
        # Ayarlar penceresindeki dinamik widget'lar için (kriterler)
        self.kriter_widgets: List[Dict[str, Any]] = []


        # --- Arayüzü Oluştur ---
        try:
            self.arayuzu_olustur()
            print("Arayüz başarıyla oluşturuldu.")
        except Exception as e:
             print(f"Kritik Hata: Arayüz oluşturulurken hata oluştu! Hata: {e}")
             import traceback
             traceback.print_exc()
             messagebox.showerror("Kritik Hata", f"Arayüz oluşturulamadı:\n{e}\nUygulama başlatılamıyor.")
             self.root.destroy()


    # --- Pencere Kapatma İşlemi ---
    def on_closing(self) -> None:
        """Pencere kapatılırken onay ister."""
        print("Kapatma işlemi başlatıldı.")
        # İleride kaydedilmemiş değişiklik kontrolü eklenebilir
        if messagebox.askokcancel("Çıkış", "Uygulamadan çıkmak istediğinize emin misiniz?"):
            print("Çıkış onaylandı, uygulama kapatılıyor.")
            self.root.destroy()
        else:
            print("Çıkış iptal edildi.")

    # --- Ana Arayüz Kurulumu ---
    def arayuzu_olustur(self) -> None:
        """Ana arayüz elemanlarını (widget'ları) oluşturur."""
        # Önceki widget'ları temizle (varsa)
        for widget in self.root.winfo_children():
            widget.destroy()

        # --- 1. Üst Panel: Kontroller ---
        ust_panel = ttk.Frame(self.root, padding="5")
        ust_panel.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))

        # Veri Yükle Butonu
        ttk.Button(ust_panel, text="📊 Veri Yükle (.xlsx)", command=self.dosya_sec_ve_yukle).pack(side=tk.LEFT, padx=5)

        # Ders Seçimi
        ttk.Label(ust_panel, text="Ders:").pack(side=tk.LEFT, padx=(10, 2))
        self.ders_combobox = ttk.Combobox(ust_panel, state="disabled", width=20) # Genişlik artırıldı
        self.ders_combobox.pack(side=tk.LEFT, padx=2)
        self.ders_combobox.bind("<<ComboboxSelected>>", self.ders_degisti)

        # Bilgi Etiketi
        self.bilgi_etiketi = ttk.Label(ust_panel, text="Lütfen veri dosyası yükleyin.", anchor="center", relief="sunken", padding=3)
        self.bilgi_etiketi.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Dışa Aktar Butonu
        self.disa_aktar_buton = ttk.Button(ust_panel, text="💾 Veriyi Dışa Aktar", command=self.veriyi_disa_aktar, state="disabled")
        self.disa_aktar_buton.pack(side=tk.RIGHT, padx=5)

        # Ayarlar Butonu
        ttk.Button(ust_panel, text="⚙️ Ayarlar", command=self.ayarlari_duzenle_ui).pack(side=tk.RIGHT, padx=5)

        # --- 2. Ana Alan: Liste ve Düzenleme ---
        ana_alan = PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        try:
             # Arka plan rengini tema ile uyumlu yapmaya çalış
             bg_color = self.style.lookup('TFrame', 'background')
             ana_alan.configure(background=bg_color)
        except tk.TclError:
             pass # Tema rengi alınamazsa varsayılan kalır
        ana_alan.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 2a. Sol Panel: Öğrenci Listesi (Treeview) ---
        sol_panel = ttk.Frame(ana_alan, padding=0)
        sol_panel.columnconfigure(0, weight=1)
        sol_panel.rowconfigure(0, weight=1)
        # Sol paneli ana alana ekle, başlangıç ağırlığı 3 (daha geniş)
        ana_alan.add(sol_panel, weight=3)

        tree_scrollbar_y = Scrollbar(sol_panel, orient=tk.VERTICAL)
        tree_scrollbar_x = Scrollbar(sol_panel, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(
            sol_panel,
            yscrollcommand=tree_scrollbar_y.set,
            xscrollcommand=tree_scrollbar_x.set,
            selectmode='browse' # Tek satır seçimi
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        tree_scrollbar_y.config(command=self.tree.yview)
        tree_scrollbar_x.config(command=self.tree.xview)
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self.ogrenci_secildi)

        # --- 2b. Sağ Panel: Düzenleme Alanı ---
        self.edit_frame = ttk.Frame(ana_alan, padding=10)
        self.edit_frame.columnconfigure(1, weight=1) # Entry'ler için
        # Sağ paneli ana alana ekle, başlangıç ağırlığı 2 (daha dar)
        ana_alan.add(self.edit_frame, weight=2)

        # --- Sağ Panel İçeriği ---
        ttk.Label(self.edit_frame, text="Seçili Öğrenci Bilgileri", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        ttk.Label(self.edit_frame, text="Öğrenci No:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.no_etiket = ttk.Label(self.edit_frame, text="-", relief="groove", padding=3, width=25, anchor='w') # Anchor eklendi
        self.no_etiket.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(self.edit_frame, text="Ad Soyad:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.ad_etiket = ttk.Label(self.edit_frame, text="-", relief="groove", padding=3, width=25, anchor='w') # Anchor eklendi
        self.ad_etiket.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        ttk.Separator(self.edit_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(self.edit_frame, text="1. Yazılı:").grid(row=4, column=0, padx=5, pady=3, sticky="w")
        self.y1_entry = ttk.Entry(self.edit_frame, width=10)
        self.y1_entry.grid(row=4, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(self.edit_frame, text="2. Yazılı:").grid(row=5, column=0, padx=5, pady=3, sticky="w")
        self.y2_entry = ttk.Entry(self.edit_frame, width=10)
        self.y2_entry.grid(row=5, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(self.edit_frame, text="Proje:").grid(row=6, column=0, padx=5, pady=3, sticky="w")
        self.proje_entry = ttk.Entry(self.edit_frame, width=10)
        self.proje_entry.grid(row=6, column=1, padx=5, pady=3, sticky="w")

        ttk.Separator(self.edit_frame, orient=tk.HORIZONTAL).grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(self.edit_frame, text="Performans Kriter Notları", font=("Arial", 10, "bold")).grid(row=8, column=0, columnspan=2, pady=(0, 5), sticky="w")

        # Dinamik Kriter Alanları İçin Çerçeve
        self.kriter_cercevesi = ttk.Frame(self.edit_frame)
        self.kriter_cercevesi.grid(row=9, column=0, columnspan=2, sticky="nsew", pady=(0,5))
        self.kriter_cercevesi.columnconfigure(1, weight=0) # Entry'ler genişlemesin

        # Hesapla ve Kaydet Butonu
        self.kaydet_buton = ttk.Button(
            self.edit_frame,
            text="🔄 Hesapla ve Değişiklikleri Kaydet",
            command=self.hesapla_ve_kaydet,
            state="disabled"
        )
        self.kaydet_buton.grid(row=10, column=0, columnspan=2, pady=(10, 5), sticky="ew")

    # --- Dosya Yükleme İşlemi ---
    def dosya_sec_ve_yukle(self) -> None:
        """Kullanıcıya Excel dosyası seçtirir, veriyi yükler ve arayüzü günceller."""
        print("Dosya seçme işlemi başlatıldı...")
        dosya_yolu = filedialog.askopenfilename(
            title="e-Okul Not Listesi Seçin (.xlsx)",
            filetypes=[("Excel Dosyaları", "*.xlsx"), ("Tüm Dosyalar", "*.*")]
        )
        if not dosya_yolu:
            print("Dosya seçilmedi.")
            return

        print(f"Seçilen dosya: {dosya_yolu}")

        try:
            varsayilan_satir_atla = 15
            satir_atla = simpledialog.askinteger(
                "Başlık Satırı Atlama",
                "Excel dosyasının başından kaç satır atlanacak?\n(Genellikle 15 veya 16'dır)",
                parent=self.root, initialvalue=varsayilan_satir_atla, minvalue=0, maxvalue=100
            )
            if satir_atla is None:
                print("Satır atlama sayısı girişi iptal edildi.")
                return
            print(f"Atlanacak satır sayısı: {satir_atla}")
        except Exception as e:
            messagebox.showerror("Giriş Hatası", f"Satır atlama sayısı alınamadı: {e}")
            return

        print("veri_isleme.veri_yukle_excel çağrılıyor...")
        try:
            # veri_isleme modülünü kullan
            df_yeni, sinif_adi = veri_isleme.veri_yukle_excel(dosya_yolu, satir_atla=satir_atla)
        except Exception as e:
            print(f"veri_yukle_excel çağrılırken hata: {e}")
            messagebox.showerror("Yükleme Hatası", f"Dosya işlenirken beklenmedik bir hata oluştu:\n{e}")
            df_yeni, sinif_adi = None, None # Hata durumunda None ata

        if df_yeni is None or not isinstance(df_yeni, pd.DataFrame):
            messagebox.showerror("Yükleme Başarısız", f"'{os.path.basename(dosya_yolu)}' yüklenemedi.\nKonsol çıktılarını ve dosya formatını kontrol edin.")
            return

        # Başarılı yükleme
        self.df = df_yeni
        self.mevcut_dosya_yolu = dosya_yolu
        self.mevcut_sinif_adi = sinif_adi if sinif_adi else "Bilinmeyen Sınıf"
        self.mevcut_ders = None
        self.secili_ogrenci_index = None

        self.bilgi_etiketi.config(text=f"Yüklü: {os.path.basename(dosya_yolu)} [{self.mevcut_sinif_adi}] ({len(self.df)} Öğr.)")

        dersler = list(self.ayarlar.get("ders_ayarlari", {}).keys())
        self.ders_combobox['values'] = dersler
        if dersler:
            self.ders_combobox.config(state="readonly")
            self.ders_combobox.set(dersler[0])
            self.ders_degisti(event=None) # İlk dersi seç ve ilgili fonksiyonları tetikle
        else:
            self.ders_combobox.set("")
            self.ders_combobox.config(state="disabled")
            self.mevcut_ders = None
            self.kriter_alanlarini_guncelle()
            messagebox.showwarning("Ders Bulunamadı", "Ayarlarınızda tanımlı ders yok. Lütfen ders ekleyin.")

        self.treeview_doldur()
        self.disa_aktar_buton.config(state="normal")
        self.edit_alanlarini_temizle()
        messagebox.showinfo("Yükleme Başarılı", f"{len(self.df)} öğrenci verisi yüklendi.")
        print("Dosya yükleme ve ilk arayüz güncelleme tamamlandı.")

    # --- Ders Değiştirme İşlemi ---
    def ders_degisti(self, event=None) -> None:
        """Ders Combobox'ı değiştiğinde ilgili alanları günceller."""
        yeni_ders = self.ders_combobox.get()
        if yeni_ders and yeni_ders != self.mevcut_ders:
            self.mevcut_ders = yeni_ders
            print(f"Ders değiştirildi: {self.mevcut_ders}")
            self.kriter_alanlarini_guncelle()
            self.treeview_doldur() # Sütunlar değişmiş olabilir
            self.edit_alanlarini_temizle()

    # --- Kriter Alanlarını Güncelleme ---
    def kriter_alanlarini_guncelle(self) -> None:
        """Sağ paneldeki kriter notu giriş alanlarını günceller."""
        for widget in self.kriter_cercevesi.winfo_children():
            widget.destroy()
        self.kriter_entry_widgets.clear()

        if not self.mevcut_ders:
            ttk.Label(self.kriter_cercevesi, text="Lütfen bir ders seçin.", font=("Arial", 9, "italic")).grid(row=0, column=0, columnspan=2, pady=5, sticky="w")
            return

        print(f"'{self.mevcut_ders}' için kriter alanları oluşturuluyor...")
        try:
            kriterler = self.ayarlar.get("ders_ayarlari", {}).get(self.mevcut_ders, {}).get("kriterler", [])
            if not kriterler:
                 ttk.Label(self.kriter_cercevesi, text="Bu ders için tanımlı kriter yok.", font=("Arial", 9, "italic")).grid(row=0, column=0, columnspan=2, pady=5, sticky="w")
                 return

            for i, kriter in enumerate(kriterler):
                kriter_adi = kriter.get("ad")
                kriter_agirlik = kriter.get("agirlik", 0.0) * 100
                if not kriter_adi: continue

                label_text = f"{kriter_adi} (%{kriter_agirlik:.1f}):"
                label = ttk.Label(self.kriter_cercevesi, text=label_text)
                label.grid(row=i, column=0, padx=5, pady=3, sticky="w")
                entry = ttk.Entry(self.kriter_cercevesi, width=10)
                entry.grid(row=i, column=1, padx=5, pady=3, sticky="w")
                self.kriter_entry_widgets[kriter_adi] = entry
            print(f"{len(self.kriter_entry_widgets)} kriter alanı oluşturuldu.")
        except Exception as e:
             ttk.Label(self.kriter_cercevesi, text=f"Kriterler yüklenirken hata: {e}", foreground="red").grid(row=0, column=0, columnspan=2, pady=5, sticky="w")
             print(f"Kriter alanları güncellenirken hata: {e}")

    # --- Treeview Doldurma ---
    def treeview_doldur(self) -> None:
        """DataFrame'deki verileri Treeview'e yükler."""
        print("Treeview dolduruluyor...")
        try: # Önce temizle
            for item in self.tree.get_children():
                self.tree.delete(item)
        except tk.TclError: pass # Widget yoksa hata vermesin

        if self.df.empty:
            print("DataFrame boş.")
            return

        # Sütunları belirle
        temel_sutunlar = ["Öğrenci No", "Ad Soyad", "Y1", "Y2", "PROJE"]
        hesaplama_sutunlari = ["Hesaplanan Performans", "Ortalama", "SONUÇ"]
        gorunecek_sutunlar = [col for col in temel_sutunlar if col in self.df.columns]
        gorunecek_sutunlar += [col for col in hesaplama_sutunlari if col in self.df.columns]

        mevcut_kriter_adlari = list(self.kriter_entry_widgets.keys()) # Sağ paneldeki aktif kriterler
        for kriter_adi in mevcut_kriter_adlari:
             if kriter_adi in self.df.columns and kriter_adi not in gorunecek_sutunlar:
                  gorunecek_sutunlar.append(kriter_adi)

        self.tree["columns"] = gorunecek_sutunlar
        self.tree["displaycolumns"] = gorunecek_sutunlar

        # Sütun başlıkları ve ayarları
        self.tree.heading("#0", text="", anchor='center')
        self.tree.column("#0", width=0, stretch=tk.NO)
        for col in gorunecek_sutunlar:
            self.tree.heading(col, text=col, anchor='center')
            width = 100
            if col == "Ad Soyad": width = 180
            elif col == "Öğrenci No": width = 80
            elif col == "SONUÇ": width = 70
            elif col in ["Ortalama", "Hesaplanan Performans"]: width = 90
            elif col in ["Y1", "Y2", "PROJE"] or col in mevcut_kriter_adlari: width = 65
            self.tree.column(col, anchor='center', width=width, minwidth=40, stretch=True)

        # Verileri ekle
        print(f"{len(self.df)} öğrenci Treeview'e ekleniyor...")
        for index, row in self.df.iterrows():
            values_to_insert = []
            for col in gorunecek_sutunlar:
                value = row.get(col, '')
                if pd.isna(value): value = ''
                elif isinstance(value, float) and col in ["Ortalama", "Hesaplanan Performans"]: value = f"{value:.2f}"
                elif isinstance(value, (int, float)): value = int(value) # Diğerlerini tamsayı yap
                values_to_insert.append(value)
            try:
                 self.tree.insert(parent='', index='end', iid=index, text="", values=values_to_insert)
            except Exception as insert_e:
                 print(f"HATA: Treeview ekleme (Index: {index}): {insert_e}")
        print("Treeview doldurma tamamlandı.")

    # --- Öğrenci Seçme ---
    def ogrenci_secildi(self, event=None) -> None:
        """Treeview'de öğrenci seçildiğinde sağ paneli doldurur."""
        selected_items = self.tree.selection()
        if not selected_items:
            self.edit_alanlarini_temizle()
            return

        try:
            selected_iid_str = selected_items[0]
            self.secili_ogrenci_index = int(selected_iid_str)
            print(f"Öğrenci seçildi. Index: {self.secili_ogrenci_index}")

            if self.secili_ogrenci_index not in self.df.index:
                 messagebox.showerror("Hata", "Seçilen öğrenci index'i geçersiz.")
                 self.edit_alanlarini_temizle()
                 return

            ogrenci_veri = self.df.loc[self.secili_ogrenci_index]

            self.no_etiket.config(text=ogrenci_veri.get("Öğrenci No", "-"))
            self.ad_etiket.config(text=ogrenci_veri.get("Ad Soyad", "-"))

            # Notları Entry'lere doldur
            for col, widget in [("Y1", self.y1_entry), ("Y2", self.y2_entry), ("PROJE", self.proje_entry)]:
                 widget.delete(0, tk.END)
                 val = ogrenci_veri.get(col)
                 widget.insert(0, str(int(val)) if pd.notna(val) else '')

            # Kriter notlarını doldur
            for kriter_adi, widget in self.kriter_entry_widgets.items():
                 widget.delete(0, tk.END)
                 val = ogrenci_veri.get(kriter_adi)
                 widget.insert(0, str(int(val)) if pd.notna(val) else '')

            self.kaydet_buton.config(state="normal")
            print("Düzenleme alanları dolduruldu.")

        except Exception as e:
            messagebox.showerror("Hata", f"Öğrenci bilgileri yüklenirken hata oluştu:\n{e}")
            print(f"HATA (ogrenci_secildi): {e}")
            import traceback
            traceback.print_exc()
            self.edit_alanlarini_temizle()

    # --- Düzenleme Alanlarını Temizleme ---
    def edit_alanlarini_temizle(self) -> None:
        """Sağ paneldeki düzenleme alanlarını temizler."""
        print("Düzenleme alanları temizleniyor.")
        self.no_etiket.config(text="-")
        self.ad_etiket.config(text="-")
        self.y1_entry.delete(0, tk.END)
        self.y2_entry.delete(0, tk.END)
        self.proje_entry.delete(0, tk.END)
        for widget in self.kriter_entry_widgets.values():
            widget.delete(0, tk.END)
        self.kaydet_buton.config(state="disabled")
        self.secili_ogrenci_index = None
        selection = self.tree.selection()
        if selection: self.tree.selection_remove(selection)

    # --- Hesaplama ve Kaydetme ---
    def hesapla_ve_kaydet(self) -> None:
        """Girilen notları DataFrame'e kaydeder ve hesaplamaları yapar."""
        # Kontroller
        if self.secili_ogrenci_index is None or self.secili_ogrenci_index not in self.df.index:
            messagebox.showwarning("Uyarı", "Lütfen önce geçerli bir öğrenci seçin.")
            return
        if not self.mevcut_ders:
            messagebox.showwarning("Uyarı", "Lütfen bir ders seçin.")
            return

        print(f"Hesapla ve Kaydet başlatıldı. Index: {self.secili_ogrenci_index}, Ders: {self.mevcut_ders}")
        try:
            # Girilen değerleri al ve doğrula
            girilen_notlar = {}
            not_alanlari = {"Y1": self.y1_entry, "Y2": self.y2_entry, "PROJE": self.proje_entry}
            not_alanlari.update(self.kriter_entry_widgets) # Kriterleri de ekle

            for ad, widget in not_alanlari.items():
                try:
                    val_str = widget.get().strip()
                    val_int = int(val_str) if val_str else 0 # Boşsa 0
                    if not (0 <= val_int <= 100):
                        raise ValueError("Not 0-100 arasında olmalıdır.")
                    girilen_notlar[ad] = val_int
                except ValueError:
                    messagebox.showerror("Geçersiz Giriş", f"'{ad}' notu geçersiz (0-100 tam sayı olmalı).")
                    widget.focus()
                    return

            # Eksik kriter sütunlarını DF'ye ekle
            for kriter_adi in self.kriter_entry_widgets.keys():
                if kriter_adi not in self.df.columns:
                    print(f"'{kriter_adi}' sütunu DataFrame'e ekleniyor...")
                    eksik_veri_degeri = self.ayarlar.get("genel_ayarlar", {}).get("eksik_veri_degeri", 0)
                    self.df[kriter_adi] = eksik_veri_degeri
                    self.df[kriter_adi] = self.df[kriter_adi].astype(int)

            # Değerleri DataFrame'e yaz
            print(f"DataFrame'e yazılıyor (Index: {self.secili_ogrenci_index}): {girilen_notlar}")
            for sutun, deger in girilen_notlar.items():
                self.df.loc[self.secili_ogrenci_index, sutun] = deger

            # Hesaplamaları yap
            print("Hesaplamalar yapılıyor...")
            try:
                # hesaplamalar.py'daki güncel fonksiyonu kullan
                self.df = hesaplamalar.tum_veriyi_hesapla(self.df, self.ayarlar, self.mevcut_ders)
                print("Hesaplamalar tamamlandı.")
            except hesaplamalar.AyarHatasi as e:
                messagebox.showerror("Hesaplama Hatası", f"Hesaplama yapılamadı (Ayar Hatası):\n{e}")
                return
            except Exception as e:
                messagebox.showerror("Hesaplama Hatası", f"Hesaplama sırasında beklenmedik hata:\n{e}")
                import traceback
                traceback.print_exc()
                return

            # Treeview'i güncelle
            print("Treeview güncelleniyor...")
            # Seçili olan index'i sakla, doldurmadan sonra tekrar seç
            kaydedilen_index = self.secili_ogrenci_index
            self.treeview_doldur()

            # Öğrenciyi tekrar seç
            try:
                if kaydedilen_index in self.df.index: # Hala geçerliyse
                    self.tree.selection_set(kaydedilen_index)
                    self.tree.focus(kaydedilen_index)
                    self.tree.see(kaydedilen_index)
                    print(f"Öğrenci (index={kaydedilen_index}) tekrar seçildi.")
            except Exception as e:
                print(f"Öğrenci tekrar seçilemedi (önemsiz): {e}")

            messagebox.showinfo("Başarılı", "Değişiklikler kaydedildi ve sonuçlar güncellendi.")

        except Exception as e:
            messagebox.showerror("Beklenmedik Hata", f"Kaydetme/Hesaplama sırasında genel hata:\n{e}")
            import traceback
            traceback.print_exc()

    # --- Veriyi Dışa Aktarma ---
    def veriyi_disa_aktar(self) -> None:
        """Mevcut DataFrame'i yeni bir Excel dosyasına kaydeder."""
        if self.df.empty:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak veri yok.")
            return

        # Dosya adı önerisi oluşturma
        try:
            s_adi = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in self.mevcut_sinif_adi) if self.mevcut_sinif_adi else "Sinif"
            d_adi = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in self.mevcut_ders) if self.mevcut_ders else "Ders"
            varsayilan_ad = f"{s_adi}_{d_adi}_Hesaplanmis.xlsx"
        except: varsayilan_ad = "hesaplanmis_notlar.xlsx"

        dosya_yolu = filedialog.asksaveasfilename(
            title="İşlenmiş Veriyi Kaydet", defaultextension=".xlsx", initialfile=varsayilan_ad,
            filetypes=[("Excel Dosyaları", "*.xlsx"), ("Tüm Dosyalar", "*.*")]
        )
        if not dosya_yolu: return # İptal

        print(f"Veri dışa aktarılıyor: {dosya_yolu}")
        try:
            self.df.to_excel(dosya_yolu, index=False, engine='openpyxl')
            messagebox.showinfo("Başarılı", f"Veri başarıyla '{os.path.basename(dosya_yolu)}' dosyasına kaydedildi.")
        except Exception as e:
            messagebox.showerror("Kaydetme Hatası", f"Dosya kaydedilirken hata oluştu:\n{e}")

    # --- Ayarlar Penceresi ---
    def ayarlari_duzenle_ui(self) -> None:
        """Ayarları düzenlemek için pencere açar (Entegre Edilmiş)."""
        print("Ayarlar penceresi açılıyor...")
        self.gecici_ayarlar = copy.deepcopy(self.ayarlar)

        top = Toplevel(self.root)
        top.title("Ayarları Düzenle")
        top.geometry("700x600") # Boyut ayarlandı
        top.resizable(True, True)
        top.minsize(550, 450)
        top.grab_set()
        top.transient(self.root)

        notebook = ttk.Notebook(top)
        notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- Sekme 1: Genel Ayarlar ---
        genel_frame = ttk.Frame(notebook, padding="10")
        notebook.add(genel_frame, text=' Genel Ayarlar ')
        genel_frame.columnconfigure(1, weight=1)
        # Grid yöneticisi için satır sayacı
        row_genel = 0

        # Başarı Sınırı
        ttk.Label(genel_frame, text="Başarı Sınırı:").grid(row=row_genel, column=0, padx=5, pady=5, sticky="w")
        self.basari_siniri_entry = ttk.Entry(genel_frame, width=10)
        self.basari_siniri_entry.grid(row=row_genel, column=1, padx=5, pady=5, sticky="w")
        self.basari_siniri_entry.insert(0, self.gecici_ayarlar.get("genel_ayarlar", {}).get("basari_siniri", 50))
        row_genel += 1

        # Eksik Veri Değeri
        ttk.Label(genel_frame, text="Eksik Veri Değeri:").grid(row=row_genel, column=0, padx=5, pady=5, sticky="w")
        self.eksik_veri_entry = ttk.Entry(genel_frame, width=10)
        self.eksik_veri_entry.grid(row=row_genel, column=1, padx=5, pady=5, sticky="w")
        self.eksik_veri_entry.insert(0, self.gecici_ayarlar.get("genel_ayarlar", {}).get("eksik_veri_degeri", 0))
        row_genel += 1

        # Yazılı Ağırlığı
        ttk.Label(genel_frame, text="Yazılı Ağırlığı (%):").grid(row=row_genel, column=0, padx=5, pady=5, sticky="w")
        self.yazili_agirlik_entry = ttk.Entry(genel_frame, width=10)
        self.yazili_agirlik_entry.grid(row=row_genel, column=1, padx=5, pady=5, sticky="w")
        # Değeri 0-1 aralığından %'ye çevirip int yap
        yazili_agirlik_val = self.gecici_ayarlar.get("genel_ayarlar", {}).get("yazili_agirlik", 0.6)
        self.yazili_agirlik_entry.insert(0, int(yazili_agirlik_val * 100))
        row_genel += 1

        # Proje Ağırlığı
        ttk.Label(genel_frame, text="Proje Ağırlığı (%):").grid(row=row_genel, column=0, padx=5, pady=5, sticky="w")
        self.proje_agirlik_entry = ttk.Entry(genel_frame, width=10)
        self.proje_agirlik_entry.grid(row=row_genel, column=1, padx=5, pady=5, sticky="w")
        proje_agirlik_val = self.gecici_ayarlar.get("genel_ayarlar", {}).get("proje_agirlik", 0.2)
        self.proje_agirlik_entry.insert(0, int(proje_agirlik_val * 100))
        row_genel += 1

        # Not: Performans ağırlığı, (100 - yazili - proje) olarak hesaplanacak.

        # --- Sekme 2: Arayüz Ayarları ---
        gui_frame = ttk.Frame(notebook, padding="10")
        notebook.add(gui_frame, text=' Arayüz Ayarları ')
        gui_frame.columnconfigure(1, weight=1)
        row_gui = 0

        # Tema Seçimi
        ttk.Label(gui_frame, text="Tema:").grid(row=row_gui, column=0, padx=5, pady=5, sticky="w")
        available_themes = sorted(self.style.theme_names())
        self.tema_combobox = ttk.Combobox(gui_frame, values=available_themes, state="readonly", width=25)
        self.tema_combobox.grid(row=row_gui, column=1, padx=5, pady=5, sticky="ew")
        current_theme = self.gecici_ayarlar.get("gui_ayarlari", {}).get("tema", "clam")
        if current_theme in available_themes:
            self.tema_combobox.set(current_theme)
        elif available_themes:
            self.tema_combobox.current(0) # İlk temayı seç
        row_gui += 1

        # Pencere Boyutu
        ttk.Label(gui_frame, text="Pencere Boyutu (örn: 1200x700):").grid(row=row_gui, column=0, padx=5, pady=5, sticky="w")
        self.pencere_boyutu_entry = ttk.Entry(gui_frame, width=28)
        self.pencere_boyutu_entry.grid(row=row_gui, column=1, padx=5, pady=5, sticky="ew")
        self.pencere_boyutu_entry.insert(0, self.gecici_ayarlar.get("gui_ayarlari", {}).get("pencere_boyutu", "1200x700"))
        row_gui += 1

        # Pencere Başlığı
        ttk.Label(gui_frame, text="Pencere Başlığı:").grid(row=row_gui, column=0, padx=5, pady=5, sticky="w")
        self.baslik_entry = ttk.Entry(gui_frame, width=28)
        self.baslik_entry.grid(row=row_gui, column=1, padx=5, pady=5, sticky="ew")
        self.baslik_entry.insert(0, self.gecici_ayarlar.get("gui_ayarlari", {}).get("baslik", "Performans Değerlendirme Sistemi"))
        row_gui += 1


        # --- Sekme 3: Dersler ve Kriterler ---
        dersler_tab_frame = ttk.Frame(notebook, padding="5") # Padding azaltıldı
        notebook.add(dersler_tab_frame, text=' Dersler ve Kriterler ')

        # Ders listesi için kaydırılabilir alan
        ders_canvas = Canvas(dersler_tab_frame)
        ders_scrollbar = ttk.Scrollbar(dersler_tab_frame, orient="vertical", command=ders_canvas.yview)
        # Derslerin listeleneceği çerçeve (Canvas içine)
        self.ders_scrollable_frame = ttk.Frame(ders_canvas, padding=(10,0)) # Sadece soldan padding

        # Scrollable frame'i Canvas'a bağla
        self.ders_scrollable_frame.bind(
            "<Configure>", lambda e: ders_canvas.configure(scrollregion=ders_canvas.bbox("all"))
        )
        ders_canvas_window = ders_canvas.create_window((0, 0), window=self.ders_scrollable_frame, anchor="nw")
        ders_canvas.configure(yscrollcommand=ders_scrollbar.set)

        # Canvas ve Scrollbar'ı yerleştir
        ders_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Ders Scrollable Frame'in genişliğini Canvas'a uydur
        def _on_canvas_configure(event):
            canvas_width = event.width
            ders_canvas.itemconfigure(ders_canvas_window, width=canvas_width)
        ders_canvas.bind("<Configure>", _on_canvas_configure)

        # Mevcut dersleri listelemek için fonksiyonu çağır
        self.ders_widgets.clear() # Önceki widget referanslarını temizle
        self.render_ders_ayarlari(self.ders_scrollable_frame)

        # Ders Ekle Butonu (Sekmenin altına, kaydırmanın dışına)
        ders_ekle_button = ttk.Button(dersler_tab_frame, text="+ Yeni Ders Ekle", width=15,
                                      command=lambda sf=self.ders_scrollable_frame: self.yeni_ders_ekle_ui(sf))
        ders_ekle_button.pack(pady=10, side=tk.BOTTOM, anchor="w", padx=10)


        # --- Kaydet / Kapat Butonları (Toplevel Penceresinin Altında) ---
        button_panel = ttk.Frame(top)
        button_panel.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)

        kaydet_button = ttk.Button(button_panel, text="Ayarları Kaydet ve Kapat",
                                   command=lambda t=top: self.ayarlari_kaydet_ve_kapat(t))
        # Kaydet butonunu sağa yasla
        kaydet_button.pack(side=tk.RIGHT, padx=5)

        kapat_button = ttk.Button(button_panel, text="Kapat", command=top.destroy)
        kapat_button.pack(side=tk.RIGHT, padx=5)

        # Pencere açıldığında ilk sekmeye odaklan
        notebook.select(0)


    # --- Ayarlar: Dersleri Listeleme ---
    def render_ders_ayarlari(self, parent_frame: ttk.Frame) -> None:
        """ Geçici ayarlardaki dersleri ayarlar penceresinde listeler. """
        print("Ayarlar: Dersler listeleniyor...")
        # Önce mevcutları temizle
        for widget in parent_frame.winfo_children():
            widget.destroy()
        self.ders_widgets.clear() # Widget referanslarını temizle

        dersler = self.gecici_ayarlar.get("ders_ayarlari", {})
        if not dersler:
             ttk.Label(parent_frame, text="Henüz ders eklenmemiş.").pack(padx=10, pady=10)
             return

        row_num = 0
        # Dersleri alfabetik sırala
        for ders_adi in sorted(dersler.keys()):
            # Her ders için bir çerçeve
            ders_cerceve = ttk.Frame(parent_frame, borderwidth=1, relief="groove")
            # Grid yerine pack kullanalım, daha basit olabilir
            ders_cerceve.pack(fill=tk.X, padx=5, pady=3)

            # Ders adı (düzenlenemez)
            ttk.Label(ders_cerceve, text=ders_adi, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10, pady=5)

            # Sil Butonu (Sağa yaslı)
            ders_sil_button = ttk.Button(ders_cerceve, text="Sil", width=5, style="Danger.TButton",
                                         command=lambda d=ders_adi, pf=parent_frame: self.dersi_sil_ui(d, pf))
            ders_sil_button.pack(side=tk.RIGHT, padx=5, pady=5)

            # Kriter Düzenle Butonu (Sağa yaslı, Sil'den önce)
            kriter_duzenle_button = ttk.Button(ders_cerceve, text="Kriterleri Düzenle", width=15,
                                               command=lambda d=ders_adi: self.kriter_duzenle(d))
            kriter_duzenle_button.pack(side=tk.RIGHT, padx=5, pady=5)

            # Widget referanslarını sakla (ileride gerekirse)
            self.ders_widgets[ders_adi] = {
                "frame": ders_cerceve,
                "duzenle_btn": kriter_duzenle_button,
                "sil_btn": ders_sil_button
            }
        # Tehlikeli Eylem Stili (Sil butonu için kırmızı)
        try:
            if "Danger.TButton" not in self.style.element_names():
                 # Stil yoksa ttk.Button stilini kopyala ve rengini değiştir
                 self.style.configure("Danger.TButton", foreground="red", font=('Arial', 9, 'bold'))
                 # Stil var olan bir temadan miras alınabilir, bu daha güvenli olabilir:
                 # self.style.map("Danger.TButton", foreground = [('active', 'red'), ('!disabled', 'red')])

        except tk.TclError:
            print("Uyarı: 'Danger.TButton' stili oluşturulamadı.")
            pass # Stil yoksa veya hata verirse normal buton görünür


    # --- Ayarlar: Yeni Ders Ekleme (UI) ---
    def yeni_ders_ekle_ui(self, parent_frame: ttk.Frame) -> None:
        """ Yeni ders eklemek için kullanıcıdan isim alır ve geçici ayarlara ekler. """
        print("Yeni ders ekleme işlemi...")
        # Kullanıcıdan yeni ders adını al
        yeni_ders_adi = simpledialog.askstring("Yeni Ders", "Yeni dersin adını girin:", parent=parent_frame.winfo_toplevel())

        if not yeni_ders_adi or not yeni_ders_adi.strip():
            print("Yeni ders adı girilmedi veya boş.")
            return # İsim girilmezse veya boşsa işlem yapma

        yeni_ders_adi = yeni_ders_adi.strip() # Başındaki/sonundaki boşlukları temizle

        # Mevcut ders adlarıyla çakışma kontrolü
        mevcut_dersler = self.gecici_ayarlar.get("ders_ayarlari", {})
        if yeni_ders_adi in mevcut_dersler:
            messagebox.showwarning("Çakışma", f"'{yeni_ders_adi}' adında bir ders zaten mevcut!", parent=parent_frame.winfo_toplevel())
            return

        # Yeni dersi boş kriter listesiyle geçici ayarlara ekle
        mevcut_dersler[yeni_ders_adi] = {"kriterler": []}
        self.gecici_ayarlar["ders_ayarlari"] = mevcut_dersler # Güncellenmiş sözlüğü ata
        print(f"Yeni ders '{yeni_ders_adi}' geçici ayarlara eklendi.")

        # Ders listesini UI'da yeniden çiz/güncelle
        self.render_ders_ayarlari(parent_frame)

        # İsteğe bağlı: Yeni eklenen dersin kriterlerini düzenleme penceresini otomatik aç
        # self.kriter_duzenle(yeni_ders_adi)


    # --- Ayarlar: Dersi Silme (UI) ---
    def dersi_sil_ui(self, ders_adi: str, parent_frame: ttk.Frame) -> None:
        """ Kullanıcıdan onay alarak dersi geçici ayarlardan siler ve UI'ı günceller. """
        print(f"'{ders_adi}' dersini silme işlemi...")
        # Onay iste
        emin_misin = messagebox.askyesno(
            "Ders Silme Onayı",
            f"'{ders_adi}' dersini ve tüm kriterlerini silmek istediğinize emin misiniz?\nBu işlem geri alınamaz.",
            icon='warning',
            parent=parent_frame.winfo_toplevel() # Mesaj kutusunu ayarlar penceresine bağla
        )

        if emin_misin:
            # Geçici ayarlardan dersi sil
            if "ders_ayarlari" in self.gecici_ayarlar and ders_adi in self.gecici_ayarlar["ders_ayarlari"]:
                del self.gecici_ayarlar["ders_ayarlari"][ders_adi]
                print(f"'{ders_adi}' dersi geçici ayarlardan silindi.")
                # Ders listesini UI'da yeniden çiz
                self.render_ders_ayarlari(parent_frame)
            else:
                # Bu normalde olmamalı ama kontrol edelim
                messagebox.showerror("Hata", f"'{ders_adi}' dersi ayarlarda bulunamadı.", parent=parent_frame.winfo_toplevel())
        else:
            print("Ders silme işlemi iptal edildi.")


    # --- Ayarlar: Kriter Düzenleme Penceresi ---
    def kriter_duzenle(self, ders_adi: str) -> None:
        """Belirli bir dersin kriterlerini düzenlemek için pencere açar."""
        print(f"'{ders_adi}' dersi için kriter düzenleme penceresi açılıyor...")
        # Geçici ayarlardan ilgili dersin kriterlerini al (kopya üzerinde çalış)
        # Eğer ders adı geçici ayarlarda yoksa (teorik olarak olmamalı) boş liste al
        self.gecici_kriterler = copy.deepcopy(
            self.gecici_ayarlar.get("ders_ayarlari", {}).get(ders_adi, {}).get("kriterler", [])
        )

        # Yeni Toplevel pencere oluştur
        top_kriter = Toplevel(self.root) # Ana pencereye bağlı
        top_kriter.title(f"'{ders_adi}' Dersi Kriterleri")
        top_kriter.geometry("550x450")
        top_kriter.resizable(True, True)
        top_kriter.minsize(450, 350)
        top_kriter.grab_set() # Diğer pencereleri etkileşimsiz yap
        top_kriter.transient(self.root) # Ana pencerenin üzerinde kal

        # Başlık
        ttk.Label(top_kriter, text=f"'{ders_adi}' dersi için kriterler ve ağırlıkları:", font=("Arial", 12)).pack(pady=(10,5))
        ttk.Label(top_kriter, text="Ağırlıkların toplamının %100 olması önerilir.", font=("Arial", 9, "italic")).pack(pady=(0,10))


        # Kriterler için kaydırılabilir alan
        kriter_ana_frame = ttk.Frame(top_kriter)
        kriter_ana_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        kriter_canvas = Canvas(kriter_ana_frame)
        kriter_scrollbar = ttk.Scrollbar(kriter_ana_frame, orient="vertical", command=kriter_canvas.yview)
        # Kriterlerin listeleneceği çerçeve (Canvas içine)
        self.kriter_scrollable_frame = ttk.Frame(kriter_canvas)

        self.kriter_scrollable_frame.bind(
            "<Configure>", lambda e: kriter_canvas.configure(scrollregion=kriter_canvas.bbox("all"))
        )
        kriter_canvas_window = kriter_canvas.create_window((0, 0), window=self.kriter_scrollable_frame, anchor="nw")
        kriter_canvas.configure(yscrollcommand=kriter_scrollbar.set)

        # Canvas ve Scrollbar'ı yerleştir
        kriter_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kriter_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Kriter Scrollable Frame'in genişliğini Canvas'a uydur
        def _on_kriter_canvas_configure(event):
            canvas_width = event.width
            kriter_canvas.itemconfigure(kriter_canvas_window, width=canvas_width)
        kriter_canvas.bind("<Configure>", _on_kriter_canvas_configure)


        # Mevcut kriterleri listelemek için fonksiyonu çağır
        self.kriter_widgets.clear() # Önceki widget referanslarını temizle
        self.render_kriterler(self.kriter_scrollable_frame, ders_adi)

        # Alt Buton Paneli
        kriter_button_panel = ttk.Frame(top_kriter)
        kriter_button_panel.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)

        # Yeni Kriter Ekle Butonu (Sola yaslı)
        yeni_kriter_button = ttk.Button(kriter_button_panel, text="+ Yeni Kriter Ekle", width=15,
                                        command=lambda sf=self.kriter_scrollable_frame, d=ders_adi: self.yeni_kriter_ekle_ui(sf, d))
        yeni_kriter_button.pack(side=tk.LEFT, padx=5)

        # Kaydet Butonu (Sağa yaslı)
        kriter_kaydet_button = ttk.Button(kriter_button_panel, text="Kriterleri Kaydet", width=15,
                                   command=lambda t=top_kriter, d=ders_adi: self.kriterleri_kaydet_ve_kapat(t, d))
        kriter_kaydet_button.pack(side=tk.RIGHT, padx=5)

        # Kapat Butonu (Sağa yaslı, Kaydet'ten önce)
        kriter_kapat_button = ttk.Button(kriter_button_panel, text="Kapat", width=10, command=top_kriter.destroy)
        kriter_kapat_button.pack(side=tk.RIGHT, padx=5)


    # --- Ayarlar: Kriterleri Listeleme ---
    def render_kriterler(self, parent_frame: ttk.Frame, ders_adi: str) -> None:
        """ Geçici kriter listesini kriter düzenleme penceresinde gösterir. """
        print(f"'{ders_adi}' için kriterler render ediliyor...")
        # Önce mevcutları temizle
        for widget in parent_frame.winfo_children():
            widget.destroy()
        self.kriter_widgets.clear() # Widget referanslarını temizle

        # Başlık Satırı
        header_frame = ttk.Frame(parent_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Label(header_frame, text="Kriter Adı", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        ttk.Label(header_frame, text="Ağırlık (%)", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, sticky="w")
        # Sütun genişliklerini ayarla
        header_frame.columnconfigure(0, weight=3) # Ad sütunu geniş
        header_frame.columnconfigure(1, weight=1) # Ağırlık dar
        header_frame.columnconfigure(2, weight=0) # Sil butonu sabit

        # Kriterleri Listele
        if not self.gecici_kriterler:
             ttk.Label(parent_frame, text="Henüz kriter eklenmemiş.").pack(pady=10)
             return

        for i, kriter in enumerate(self.gecici_kriterler):
            # Her kriter için ayrı bir çerçeve
            kriter_satir_frame = ttk.Frame(parent_frame)
            kriter_satir_frame.pack(fill=tk.X, padx=5, pady=1)
            kriter_satir_frame.columnconfigure(0, weight=3)
            kriter_satir_frame.columnconfigure(1, weight=1)
            kriter_satir_frame.columnconfigure(2, weight=0)

            # Kriter Adı Girişi
            ad_entry = ttk.Entry(kriter_satir_frame)
            ad_entry.insert(0, kriter.get("ad", ""))
            ad_entry.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

            # Ağırlık Girişi
            agirlik_entry = ttk.Entry(kriter_satir_frame, width=10)
            # Ağırlığı 0-1 arasından %'ye çevirip int yap
            agirlik_val = kriter.get("agirlik", 0.0)
            agirlik_entry.insert(0, str(int(agirlik_val * 100)))
            agirlik_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

            # Sil Butonu
            sil_button = ttk.Button(kriter_satir_frame, text="Sil", style="Danger.TButton", width=5,
                                    # Lambda'da index'i ve parent'ı doğru aktar
                                    command=lambda idx=i, pf=parent_frame, da=ders_adi: self.kriteri_sil_ui(idx, pf, da))
            sil_button.grid(row=0, column=2, padx=(5,0), pady=2)

            # Widget referanslarını sakla (Kaydetme işlemi için)
            self.kriter_widgets.append({
                "frame": kriter_satir_frame,
                "ad_entry": ad_entry,
                "agirlik_entry": agirlik_entry,
                "sil_btn": sil_button
            })
        print(f"{len(self.kriter_widgets)} kriter listelendi.")


    # --- Ayarlar: Yeni Kriter Ekleme (UI) ---
    def yeni_kriter_ekle_ui(self, parent_frame: ttk.Frame, ders_adi: str) -> None:
        """ Geçici kriter listesine boş bir kriter ekler ve UI'ı günceller. """
        print("Yeni kriter satırı ekleniyor...")
        # Geçici listeye boş bir kriter ekle
        self.gecici_kriterler.append({"ad": "", "agirlik": 0.0})
        # Kriter listesini UI'da yeniden çiz
        self.render_kriterler(parent_frame, ders_adi)
        # Yeni eklenen satırdaki ad entry'sine odaklan (varsa)
        if self.kriter_widgets:
            self.kriter_widgets[-1]["ad_entry"].focus_set()


    # --- Ayarlar: Kriter Silme (UI) ---
    def kriteri_sil_ui(self, index: int, parent_frame: ttk.Frame, ders_adi: str) -> None:
        """ Belirtilen index'teki kriteri geçici listeden siler ve UI'ı günceller. """
        print(f"{index}. index'teki kriter siliniyor...")
        try:
            # Index geçerli mi kontrol et
            if 0 <= index < len(self.gecici_kriterler):
                # Listeden sil
                del self.gecici_kriterler[index]
                print("Kriter geçici listeden silindi.")
                # Kriter listesini UI'da yeniden çiz
                self.render_kriterler(parent_frame, ders_adi)
            else:
                 print(f"Hata: Geçersiz kriter index'i: {index}")
                 messagebox.showerror("Hata", "Silinecek kriter bulunamadı (Geçersiz index).", parent=parent_frame.winfo_toplevel())
        except Exception as e:
             print(f"Kriter silinirken hata: {e}")
             messagebox.showerror("Hata", f"Kriter silinirken bir hata oluştu:\n{e}", parent=parent_frame.winfo_toplevel())


    # --- Ayarlar: Kriterleri Kaydetme ---
    def kriterleri_kaydet_ve_kapat(self, toplevel_window: tk.Toplevel, ders_adi: str) -> None:
        """ Kriter penceresindeki değişiklikleri geçici ayarlara kaydeder ve pencereyi kapatır."""
        print(f"'{ders_adi}' için kriterler kaydediliyor...")
        try:
            yeni_kriter_listesi = []
            toplam_agirlik_yuzde = 0
            # Widget listesinden verileri oku
            for i, widgets in enumerate(self.kriter_widgets):
                ad = widgets["ad_entry"].get().strip()
                agirlik_str = widgets["agirlik_entry"].get().strip()

                # Kriter adı boşsa bu satırı atla (veya hata ver)
                if not ad:
                    # Boş isimli kriterleri sessizce atlayalım
                    print(f"Uyarı: {i+1}. kriterin adı boş, atlanıyor.")
                    continue
                    # Veya hata ver: raise ValueError(f"{i+1}. kriterin adı boş olamaz.")

                # Ağırlığı doğrula
                try:
                    agirlik_yuzde = int(agirlik_str) if agirlik_str else 0 # Boşsa 0
                    if not (0 <= agirlik_yuzde <= 100):
                        raise ValueError("Ağırlık 0 ile 100 arasında olmalıdır.")
                except ValueError:
                    raise ValueError(f"'{ad}' kriteri için geçersiz ağırlık: '{agirlik_str}'. Lütfen 0-100 arası tam sayı girin.")

                # Ağırlığı 0-1 arasına çevir
                agirlik_float = agirlik_yuzde / 100.0
                yeni_kriter_listesi.append({"ad": ad, "agirlik": agirlik_float})
                toplam_agirlik_yuzde += agirlik_yuzde

            # Ağırlık Toplamı Kontrolü
            # Küçük ondalık hataları için tolerans (örn: 99.9 ile 100.1 arası kabul)
            if not (99.9 < toplam_agirlik_yuzde < 100.1) and yeni_kriter_listesi: # Liste boş değilse kontrol et
                 # Kullanıcıyı uyaralım ama kaydetmesine izin verelim (belki bilerek yapıyorlar)
                 uyari_mesaji = (f"'{ders_adi}' dersi için girilen kriter ağırlıklarının toplamı %{toplam_agirlik_yuzde:.1f}.\n"
                                 f"Toplamın %100 olması beklenir.\n\nYine de bu şekilde kaydetmek istiyor musunuz?")
                 if not messagebox.askyesno("Ağırlık Uyarısı", uyari_mesaji, icon='warning', parent=toplevel_window):
                      print("Kriter kaydetme iptal edildi (ağırlık toplamı uyarısı).")
                      return # Kaydetmeden çık

            # Geçici ayarlardaki ilgili dersin kriterlerini güncelle
            if "ders_ayarlari" in self.gecici_ayarlar and ders_adi in self.gecici_ayarlar["ders_ayarlari"]:
                self.gecici_ayarlar["ders_ayarlari"][ders_adi]["kriterler"] = yeni_kriter_listesi
                print(f"'{ders_adi}' için {len(yeni_kriter_listesi)} kriter geçici ayarlara kaydedildi.")
                # Ana ayarlar penceresine bilgi ver (kaydetme orada yapılacak)
                messagebox.showinfo("Bilgi", f"'{ders_adi}' kriterleri güncellendi.\nDeğişikliklerin kalıcı olması için ana 'Ayarları Kaydet ve Kapat' butonuna basın.", parent=toplevel_window)
                toplevel_window.destroy() # Kriter penceresini kapat
            else:
                 # Bu hata normalde olmamalı
                 raise ValueError(f"'{ders_adi}' dersi geçici ayarlarda bulunamadı (kaydetme sırasında).")

        except ValueError as e:
            # Kullanıcıya gösterilecek doğrulama hataları
            messagebox.showerror("Geçersiz Değer", f"Kriterler kaydedilemedi:\n{e}", parent=toplevel_window)
        except Exception as e:
            # Beklenmedik hatalar
            messagebox.showerror("Hata", f"Kriterler kaydedilirken bir hata oluştu:\n{e}", parent=toplevel_window)
            print(f"HATA (kriterleri_kaydet): {e}")
            import traceback
            traceback.print_exc()


    # --- Ayarlar: Tüm Ayarları Kaydetme ve Kapatma ---
    def ayarlari_kaydet_ve_kapat(self, toplevel_window: tk.Toplevel) -> None:
        """ Ayarlar penceresindeki tüm değişiklikleri ana ayarlara kaydeder ve pencereyi kapatır."""
        print("Ayarlar kaydediliyor...")
        try:
            # --- 1. Genel Ayarları Oku ve Doğrula ---
            try:
                basari_siniri = int(self.basari_siniri_entry.get())
                eksik_veri = int(self.eksik_veri_entry.get())
                yazili_agirlik_yuzde = int(self.yazili_agirlik_entry.get())
                proje_agirlik_yuzde = int(self.proje_agirlik_entry.get())

                if not (0 <= basari_siniri <= 100): raise ValueError("Başarı sınırı 0-100 arası olmalı.")
                # Eksik veri değeri herhangi bir int olabilir.
                if not (0 <= yazili_agirlik_yuzde <= 100): raise ValueError("Yazılı ağırlığı 0-100 arası olmalı.")
                if not (0 <= proje_agirlik_yuzde <= 100): raise ValueError("Proje ağırlığı 0-100 arası olmalı.")
                if yazili_agirlik_yuzde + proje_agirlik_yuzde > 100:
                     raise ValueError("Yazılı ve Proje ağırlıkları toplamı 100'ü geçemez (Performansa yer kalmalı).")

                # Geçici ayarlara yaz (0-1 aralığında)
                self.gecici_ayarlar["genel_ayarlar"]["basari_siniri"] = basari_siniri
                self.gecici_ayarlar["genel_ayarlar"]["eksik_veri_degeri"] = eksik_veri
                self.gecici_ayarlar["genel_ayarlar"]["yazili_agirlik"] = yazili_agirlik_yuzde / 100.0
                self.gecici_ayarlar["genel_ayarlar"]["proje_agirlik"] = proje_agirlik_yuzde / 100.0
                print("Genel ayarlar okundu ve doğrulandı.")
            except ValueError as e:
                raise ValueError(f"Genel Ayarlar sekmesinde geçersiz değer: {e}")

            # --- 2. GUI Ayarlarını Oku ve Doğrula ---
            try:
                tema = self.tema_combobox.get()
                pencere_boyutu = self.pencere_boyutu_entry.get().strip()
                baslik = self.baslik_entry.get().strip()

                # Boyut formatını basitçe kontrol et (örn: RakamxRakam)
                if not pencere_boyutu or 'x' not in pencere_boyutu or not all(p.isdigit() for p in pencere_boyutu.split('x')):
                    raise ValueError("Pencere boyutu 'GenişlikxYükseklik' formatında olmalıdır (örn: 1200x700).")
                if not baslik: raise ValueError("Pencere başlığı boş olamaz.")

                # Geçici ayarlara yaz
                self.gecici_ayarlar["gui_ayarlari"]["tema"] = tema
                self.gecici_ayarlar["gui_ayarlari"]["pencere_boyutu"] = pencere_boyutu
                self.gecici_ayarlar["gui_ayarlari"]["baslik"] = baslik
                print("Arayüz ayarları okundu ve doğrulandı.")
            except ValueError as e:
                raise ValueError(f"Arayüz Ayarları sekmesinde geçersiz değer: {e}")

            # --- 3. Ders Ayarları (Zaten geçici ayarlarda güncellendi) ---
            # Sadece ders adlarının geçerli olup olmadığını son bir kez kontrol edelim
            if "ders_ayarlari" in self.gecici_ayarlar:
                 for ders_adi in self.gecici_ayarlar["ders_ayarlari"]:
                      if not ders_adi: # Boş ders adı olamaz (teorik olarak eklenmemeli ama kontrol edelim)
                           raise ValueError("Kaydedilecek dersler arasında adı boş olan var!")
            print("Ders ayarları kontrol edildi.")


            # --- 4. Geçici Ayarları Ana Ayarlara ve Dosyaya Kaydet ---
            # Ana ayarları güncelle (artık geçerli veriler içeriyor)
            self.ayarlar = copy.deepcopy(self.gecici_ayarlar) # Derin kopya önemli olabilir
            print("Ana ayarlar güncellendi.")

            # Dosyaya kaydet (veri_isleme modülünden)
            if veri_isleme.save_settings(self.ayarlar):
                 print("Ayarlar dosyaya başarıyla kaydedildi.")
                 messagebox.showinfo("Başarılı", "Ayarlar başarıyla kaydedildi.", parent=toplevel_window)

                 # --- 5. Ana Arayüzü Güncelle ---
                 print("Ana arayüz güncelleniyor...")
                 # Başlık
                 self.root.title(self.ayarlar["gui_ayarlari"]["baslik"])
                 # Boyut (Ancak yeniden başlatma gerekebilir tam etki için)
                 try: self.root.geometry(self.ayarlar["gui_ayarlari"]["pencere_boyutu"])
                 except tk.TclError: print("Uyarı: Pencere boyutu ayarlanamadı.")
                 # Tema
                 try:
                      self.style.theme_use(self.ayarlar["gui_ayarlari"]["tema"])
                      print(f"Ana arayüz teması güncellendi: {self.ayarlar['gui_ayarlari']['tema']}")
                 except tk.TclError: print(f"Uyarı: Tema '{self.ayarlar['gui_ayarlari']['tema']}' uygulanamadı.")

                 # Ders combobox'ını güncelle
                 dersler = list(self.ayarlar.get("ders_ayarlari", {}).keys())
                 mevcut_secim = self.ders_combobox.get() # Kaydetmeden önceki seçim
                 self.ders_combobox['values'] = dersler
                 if not dersler: # Hiç ders kalmadıysa
                      self.ders_combobox.set("")
                      self.ders_combobox.config(state="disabled")
                      self.mevcut_ders = None
                      self.kriter_alanlarini_guncelle() # Kriter alanlarını temizle
                      self.treeview_doldur() # Treeview'i temizle/güncelle
                 elif mevcut_secim in dersler: # Önceki seçim hala geçerliyse
                      self.ders_combobox.set(mevcut_secim)
                      # Seçim değişmese bile kriterler değişmiş olabilir
                      self.kriter_alanlarini_guncelle()
                      self.treeview_doldur() # Treeview başlıkları/sütunları değişebilir
                 else: # Önceki seçim silinmişse veya hiç yoktuysa
                      self.ders_combobox.set(dersler[0]) # İlk dersi seç
                      self.ders_degisti(None) # Değişikliği ve güncellemeleri tetikle

                 print("Ana arayüz güncelleme tamamlandı.")
                 toplevel_window.destroy() # Ayarlar penceresini kapat
            else:
                 # Dosyaya kaydetme başarısız olduysa
                 messagebox.showerror("Hata", "Ayarlar dosyaya kaydedilemedi. Konsolu kontrol edin.", parent=toplevel_window)

        except ValueError as e: # Ayarları okurken/doğrularken oluşan hata
            messagebox.showerror("Geçersiz Değer", f"Ayarlar kaydedilemedi:\n{e}", parent=toplevel_window)
        except Exception as e: # Diğer beklenmedik hatalar
            messagebox.showerror("Beklenmedik Hata", f"Ayarlar kaydedilirken bir hata oluştu:\n{e}", parent=toplevel_window)
            print(f"HATA (ayarlari_kaydet_ve_kapat): {e}")
            import traceback
            traceback.print_exc()


# --- Uygulamayı Başlatma Fonksiyonu ---
def baslat():
    """Tkinter ana döngüsünü başlatır."""
    root = tk.Tk()
    # Font ayarı (isteğe bağlı, sistem fontlarını kullanmak daha iyi olabilir)
    # try: root.option_add('*font', 'Arial 10')
    # except tk.TclError: pass
    print("Uygulama başlatılıyor...")
    try:
        app = PerformansYonetimApp(root)
        # Eğer __init__ hata vermeden bittiyse mainloop'u başlat
        if app and getattr(app, 'root', None) and app.root.winfo_exists():
             print("Ana döngü (mainloop) başlatılıyor.")
             root.mainloop()
        else:
             print("Uygulama başlatılamadı (__init__ sonrası).")
    except Exception as app_err:
         # Uygulama başlatılırken oluşabilecek genel hatalar
         print(f"Uygulama başlatılırken kritik hata: {app_err}")
         import traceback
         traceback.print_exc()
         messagebox.showerror("Başlatma Hatası", f"Uygulama başlatılamadı:\n{app_err}")
         try: root.destroy() # Hata penceresi sonrası kapatmayı dene
         except: pass


# --- Doğrudan Çalıştırma Bloğu ---
if __name__ == "__main__":
    # Bu script doğrudan çalıştırıldığında baslat() fonksiyonunu çağır
    print("main bloğu çalıştırıldı, baslat() çağrılıyor...")
    baslat()
