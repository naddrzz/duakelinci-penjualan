# Research: Telegram Paste Formatting & Keterbacaan Bahasa Indonesia untuk Briefing Eksekutif

Date: 2026-11-24  
Scope: Evaluasi empiris hasil *paste* nyata `telegram_summary()` di **Telegram Desktop** dan **Telegram Android**, riset sumber primer mekanisme *formatting* & *clipboard paste* klien resmi Telegram, serta kaidah keterbacaan **EYD Edisi V**, **kalimat efektif (Badan Bahasa / Narabahasa)**, dan **UX Writing Bahasa Indonesia** untuk layar sempit.

---

## 1. Diagnosis Visual Hasil Paste Saat Ini (Mengapa Belum Enak Dibaca)

Berdasarkan inspeksi langsung pada tangkapan layar *chat bubble* Telegram Desktop (gelap) dan Telegram Android (ungu):

1. **Nol hierarki tipografi (*flat weight*)**:
   - Seluruh ~1.750 karakter tampil dalam satu ketebalan huruf reguler (`font-weight: 400`). Judul utama, subjudul bagian (`Penjualan tertinggi & terendah:`, `Evaluasi penurunan...`), nama toko, dan angka kemerosotan menyatu tanpa titik jangkar mata (*visual anchor*).
2. **Patah baris yatim (*orphaned currency & unit breaks*)**:
   - Di Telegram Desktop: `...Palembang (Sumatera) — Rp` patah di ujung baris dan `9,2 jt` jatuh ke baris bawah; `Kurnia −Rp` terpisah dari `2,3 jt`.
   - Di Telegram Android: `Bekasi Rp 78,0` patah dan menyisakan kata `jt` sendirian di baris baru; judul `Ringkasan Penjualan Dua Kelinci —` patah menyisakan `Sep–Okt 2026`.
   - **Akar teknis**: penulisan spasi biasa (`U+0020`) setelah `Rp` (`Rp 9,2 jt`) dan sebelum satuan (`jt`, `rb`, `miliar`) mengizinkan algoritma *line-breaking* memotong nilai uang tepat di tengah nominal.
3. **Tembok daftar rapat tanpa ruang napas (*17-line wall of text*)**:
   - Kelima butir `1.` s.d. `5.` pada evaluasi penurunan masing-masing membentang 3–4 baris di ponsel **tanpa baris kosong (`\n\n`) antarbutir**, menghasilkan 17 baris rapat berturut-turut.
4. **Polusi 7 simbol baca dalam satu baris (*symbol soup*)**:
   - Satu butir menggabungkan `[kurung siku]`, `(kurung lengkung)`, `—` (*em dash*), `→` (panah), `·` (titik tengah), `↳` (panah belok), dan `:` sekaligus:
     `1. [OUT1043] Minimarket Sido Muncul, Palembang (Sumatera) — Rp 9,2 jt → Rp 2,9 jt (−69% · −Rp 6,3 jt)` (103 karakter dalam satu baris logis, padahal lebar gelembung pesan ponsel hanya **32–38 karakter/baris**).
5. **Diksi terjemahan kaku (*translationese*) & pengulangan kata mubazir**:
   - Frasa nominal kaku seperti *"Salesman kontraksi terdalam"*, campur kode *"drop utama Zaki"*, label meta *"Perbandingan:"*, duplikasi `Tangerang Rp 249,0 jt` dua baris berturut-turut, serta pengulangan *"dari total"* memakan lebar baris tanpa menambah informasi.

---

## 2. Mekanisme Teknis Formatting & Clipboard Paste di Klien Resmi Telegram

Temuan dari dokumentasi resmi MTProto/Bot API dan kode sumber klien resmi Telegram (`telegramdesktop/tdesktop`, `TelegramMessenger/Telegram-iOS`, dan pelacak isu `bugs.telegram.org`):

### 2.1 Arsitektur `MessageEntity` & Perbedaan Sintaks Bot API vs Klien Pengguna
- Di lapisan protokol MTProto (`core.telegram.org/api/entities/`, `core.telegram.org/type/MessageEntity.md`), pesan Telegram **tidak** menyimpan HTML atau Markdown, melainkan teks UTF-16 polos beserta daftar *offset/length* entitas (`messageEntityBold`, `messageEntityItalic`, `messageEntityCode`, `messageEntityPre`, `messageEntityBlockquote`).
- **Perbedaan krusial sintaks komposer manusia vs Bot API**:
  - `MarkdownV2` milik Bot API memakai satu bintang `*bold*`, **tetapi komposer input pengguna di aplikasi Telegram memakai dua bintang `**bold**`**.
  - Kode sumber **Telegram Desktop** (`Telegram/SourceFiles/ui/widgets/input_fields.cpp` & `message_field.cpp`):
    - `InputField::kTagBold = qsl("**")` → dikonversi menjadi `EntityType::Bold` oleh `PrepareRichFromPlain` / `TextParseMarkdown` saat pesan dikirim.
    - `InputField::kTagItalic = qsl("__")` → `EntityType::Italic` *(catatan: di Telegram Web K 2.2 terdapat isu regresi interpretasi `__` vs `*` pada Okt 2026 di `bugs.telegram.org/c/66641`, sehingga `__` sebaiknya dihindari untuk lintas-klien; gunakan `**tebal**` dan `` `kode` `` yang konsisten penuh di Desktop, Android, iOS, macOS, dan CommonMark)*.
    - `InputField::kTagCode = qsl("`")` → `EntityType::Code` (teks *monospace* sebaris).
  - Kode sumber **Telegram iOS** (`TelegramMessenger/Telegram-iOS/blob/master/docs/richtext-composer.md`, §7 *Markdown on paste*):
    - `chatInputContentFromPastedMarkdown(context:plainText:keepsBlankLines:)` di `PastedMarkdownConversion.swift` otomatis mengubah teks *clipboard* yang mengandung `**bold**` dan `` `code` `` menjadi *rich entities* **seketika saat ditempel (`paste`)**, dengan mode `lineBreaks: .keep` (satu `\n` tetap ganti baris, `\n\n` tetap menjadi pemisah paragraf kosong).
  - **Mengapa tidak mengandalkan `ClipboardItem` `text/html` semata?**
    - Berdasarkan isu `telegramdesktop/tdesktop#5795` dan pengujian API Clipboard browser (`stackoverflow.com/q/74692836`), klien Telegram Desktop historis menggunakan target internal `application/x-td-field-tags` dan mengabaikan `text/html` murni dari browser saat ditempel ke kolom *chat*. Sebaliknya, sintaks `**tebal**` dan `` `monospace` `` di dalam `text/plain` diproses secara konsisten oleh komposer Telegram iOS (saat *paste*) serta Telegram Desktop & Android (saat *send*).

### 2.2 Fitur *Tap-to-Copy* pada Entitas `` `Monospace` `` (`messageEntityCode`)
- Pada seluruh klien Telegram (Android, iOS, Desktop — terkonfirmasi di `core.telegram.org/api/entities/` dan `bugs.telegram.org/c/5742`), mengetuk teks berformat `` `kode` `` (`messageEntityCode`) di dalam gelembung pesan **langsung menyalin kode tersebut ke papan klip** (*"Text copied to clipboard"*).
- **Implikasi produk**: Mengubah `[OUT1043]` menjadi `` `OUT1043` `` bukan sekadar membersihkan tanda kurung siku `[ ]`, melainkan mengubah setiap kode *outlet* di Telegram menjadi **tombol salin satu ketuk** agar Sales Manager dapat langsung menempelkannya ke kolom pencarian dasbor web.

### 2.3 Pengendalian Patah Baris dengan *Non-Breaking Space* (`U+00A0`) & Batas Lebar Baris
- Standar W3C Internationalization (*Approaches to Line Breaking*, `U+00A0 NO-BREAK SPACE`) dan pedoman tipografi (*Butterick's Practical Typography*; *OneKitly CLDR Number Formatting*) menetapkan penggunaan `U+00A0` sebagai "perekat tak-kasatmata" di antara angka dan satuan singkat (`Rp847,5\u00A0jt`, `Rp564\u00A0rb`, `Rp1,73\u00A0miliar`, `3\u00A0faktur`).
- Gelembung pesan (*chat bubble*) Telegram di ponsel berlebar `360px–390px` memiliki margin avatar/sisi sekitar `72px–88px`, menyisakan ruang teks efektif sekitar **`275px–300px` (~34–40 karakter proporsional per baris)**.
- Studi keterbacaan *Nielsen Norman Group* (Kate Moran, 2016; Hoa Loranger, 2017) dan *Chrome Modern Web Typography Guide* menyimpulkan:
  1. **Batasi penekanan tebal (*bold*) hanya pada jangkar pemindaian** (judul bagian, nama entitas utama, atau angka kunci) — jika terlalu banyak kata ditebalkan, efek kontras hilang.
  2. **Pecah informasi bertingkat ke baris pendek mandiri** (`<= 38–42` karakter) alih-alih menyambungnya dengan deretan *em dash* panjang.
  3. **Beri satu baris kosong (`\n\n`) di antara item daftar multi-baris** agar mata dapat memisahkan 5 *outlet* tanpa tersesat (*gestalt proximity*).

---

## 3. Kaidah Keterbacaan, EYD Edisi V, & UX Writing Bahasa Indonesia

Temuan dari sumber primer **SK Kepala Badan Bahasa No. 0424/I/BS.00.01/2022 (EYD Edisi V)**, **Seri Penyuluhan Kalimat Efektif (Sasangka, 2019)**, **Ivan Lanin / Narabahasa**, serta **Pedoman UX Writing Indonesia (Telkom Legion, INA Digital / GovTech, Gojek, Tokopedia, Microsoft Localization Style Guide)**:

### 3.1 Ejaan Angka, Mata Uang `Rp`, Persen, dan Tanda Baca (EYD V)
1. **`Rp` ditulis serangkai tanpa spasi dan tanpa titik** (`EYD V Bab II.F.5 & II.G.3`; Ivan Lanin, *Penulisan Rupiah #481*, 2024):
   - Benar: `Rp1,73 miliar`, `Rp847,5 jt`, `Rp564 rb`, `−Rp6,3 jt`.
   - Salah: `Rp 1,73 miliar` (berjarak spasi, yang juga memicu patah baris yatim `Rp` di ujung baris).
   - Singkatan kompak `jt` dan `rb` diizinkan untuk ruang sempit/UI (*Microsoft Indonesian Style Guide* §4.1.1; Ivan Lanin, 2024) tanpa tanda titik dan diikat dengan `U+00A0` (`Rp847,5\u00A0jt`).
2. **Persen (`%`) dan desimal koma (`,`)**:
   - Lambang `%` melekat rapat tanpa spasi (`+3,6%`, `−69%`, `28,7%`).
3. **Rentang vs Perbandingan Berurutan**:
   - Rentang akumulasi bulan menggunakan tanda pisah tanpa spasi (`Sep–Okt 2026`), tidak dicampur dengan kata *dari* atau *antara*.
   - Perbandingan arah perubahan bulan menggunakan panah (`Sep → Okt`) atau kata kerja langsung (`turun dari Sep`), serta **tidak** menyalahgunakan *em dash* (`—`) bertumpuk di dalam satu kalimat.

### 3.2 Karakteristik Panjang Kata Bahasa Indonesia di Layar Ponsel
- Berbeda dengan bahasa Inggris (~5 karakter/kata), Bahasa Indonesia bersifat **aglutinatif** (berimbuhan `me-...-kan`, `pe-...-an`, `ke-...-an`), sehingga rata-rata panjang kata laporan mencapai **~7,3 karakter/kata** dan menghasilkan ekspansi panjang teks **+15% s.d. +30%** dibanding bahasa Inggris (*SEAtongue Localization Guide*; *IBM/W3C*; Ivan Lanin pada *Bedah Laporan BPKD*, 2026).
- **Standar Telkom Legion Design System (*Writing Guideline*) & Narabahasa (pelatihan *detik Network*)**:
  - Satu baris pindai cepat di ponsel idealnya **<= 40 karakter** (hanya ~5–6 kata Bahasa Indonesia) dan satu butir maksimal **2–3 baris pendek**.
  - Satu blok/paragraf di layar ponsel maksimal **1–2 kalimat** (<= 8–12 kata per kalimat).

### 3.3 Lima Aturan Bahasa Indonesia yang Enak Dibaca (*Anti-Kaku*)
1. **Ganti tumpukan nomina & jargon terjemahan (*translationese*) dengan verba aktif sehari-hari** (Sasangka, 2019; Yasa dkk., Undiksha):
   - ❌ `Salesman kontraksi terdalam` → ✅ `Sales turun terdalam`
   - ❌ `Evaluasi penurunan — 5 outlet melemah terdalam` → ✅ `5 Outlet Turun Terdalam`
   - ❌ `drop utama Zaki −Rp 6,8 jt (−96%)` → ✅ `Zaki turun Rp6,8 jt (−96%)`
2. **Hapus label meta (*meta-labels*) yang mubazir** (INA Digital; Gojek UX Writing):
   - ❌ `• Perbandingan: Sep Rp 847,5 jt → Okt Rp 878,4 jt` → ✅ `Sep Rp847,5 jt → Okt Rp878,4 jt` (angka & panah sudah menjelaskan perbandingan tanpa kata `"Perbandingan:"`).
3. **Pangkas repetisi `"dari total"` dan wilayah berulang**:
   - ❌ `Rp 495,8 jt (28,7% dari total)` diulang berkali-kali → ✅ `Rp495,8 jt (28,7%)`.
   - ❌ Menyebut `Tangerang Rp 249,0 jt` pada sub-baris `Cabang kota` lalu mengulang lagi `• Cabang tertinggi: Tangerang (Jabodetabek) — Rp 249,0 jt` tepat di bawahnya → cukup sebutkan sekali dengan jernih atau hanya tampilkan `Cabang #1` bila berasal dari wilayah berbeda.
   - ❌ Menulis provinsi/wilayah di dalam tanda kurung pada setiap toko `Palembang (Sumatera)`, `Semarang (Jawa Tengah)`, `Jakarta Barat (Jabodetabek)` → nama kota cabang (`Palembang`, `Semarang`, `Jakarta Barat`) sudah spesifik dan menghemat **10–15 karakter per baris**! (Wilayah hanya perlu ditampilkan bila nama cabang tidak lazim atau sama).
4. **Sejajarkan pola tiap butir (*paralelisme*)**:
   - Setiap butir pada *5 Outlet Turun Terdalam* wajib mengikuti pola identik 3 baris mikro:
     - **Baris 1 (Toko, ID & Kota)**: `1. **Nama Toko** `ID` · Kota`
     - **Baris 2 (Angka Penurunan)**: `   RpAwal → RpAkhir (**−XX%** · −RpSelisih)`
     - **Baris 3 (Aktivitas & PIC Sales)**: `   X→Y faktur · Sales A, B (pemicu utama)`
5. **Ragam Konsultatif–Lugas ("Baku Tak Mesti Kaku" — Ivan Lanin)**:
   - Tetap sopan, akurat, dan profesional untuk level Manajer Komersial/Direksi, namun lincah dipindai dalam 5–10 detik saat sedang bergerak di lapangan.

---

## 4. Rancangan Format Baru Briefing Telegram (Sebelum vs Sesudah)

### 4.1 Sebelum (Tampilan Saat Ini — ~1.750 karakter, padat & patah baris)
```text
Ringkasan Penjualan Dua Kelinci — Sep–Okt 2026

Total penjualan bersih: Rp 1,73 miliar (naik 3,6%)
• Perbandingan: Sep Rp 847,5 jt → Okt Rp 878,4 jt
• Wilayah terbaik: Jabodetabek — Rp 495,8 jt (28,7% dari total)
  ↳ Cabang kota: Tangerang Rp 249,0 jt · Jakarta Barat Rp 168,8 jt · Bekasi Rp 78,0 jt
• Cabang tertinggi: Tangerang (Jabodetabek) — Rp 249,0 jt (14,4%)
• Merek terbaik: Kacang Dua Kelinci — Rp 739,8 jt (42,9% dari total)
• Salesman tertinggi: Citra (Tangerang, Jabodetabek) — Rp 136,6 jt · +17%
...
1. [OUT1043] Minimarket Sido Muncul, Palembang (Sumatera) — Rp 9,2 jt → Rp 2,9 jt (−69% · −Rp 6,3 jt)
   5→3 faktur · Sales: Zaki, Yudi — drop utama Zaki −Rp 6,8 jt (−96%)
2. [OUT1022] Toko Bintang, Semarang (Jawa Tengah) — Rp 8,8 jt → Rp 3,2 jt (−63% · −Rp 5,5 jt)
   6→4 faktur · Sales: Kurnia, Lestari — Lestari −Rp 3,3 jt, Kurnia −Rp 2,3 jt
```

### 4.2 Sesudah (Rekomendasi Hasil Riset — Hierarki Tebal, Monospace *Tap-to-Copy*, Anti-Patah `U+00A0`, Bahasa Lugas)

*(Catatan: `**...**` otomatis berubah menjadi **huruf tebal** dan `` `OUTxxxx` `` otomatis menjadi lencana **monospace tap-to-copy** di Telegram tanpa menampilkan tanda bintang/backtick; seluruh spasi di antara angka dan `jt`/`rb`/`miliar` memakai `U+00A0` agar tidak pernah patah yatim di ponsel.)*

```text
**Laporan Penjualan Dua Kelinci**
Periode Sep–Okt 2026

**Capaian Utama**
Omzet bersih **Rp1,73 miliar** (naik 3,6%)
Sep Rp847,5 jt → Okt Rp878,4 jt

• Wilayah #1: **Jabodetabek** · Rp495,8 jt (28,7%)
  Tangerang Rp249,0 jt · Jakarta Barat Rp168,8 jt · Bekasi Rp78,0 jt
• Merek #1: **Kacang Dua Kelinci** · Rp739,8 jt (42,9%)
• Sales #1: **Citra** (Tangerang) · Rp136,6 jt (+17%)

**Rentang Tertinggi & Terendah**
• Toko tertinggi: **Grosir Harapan Baru** `OUT1007` (Tangerang) · Rp190,5 jt — Sales Citra, Dedi
• Toko terendah: **Toko Sinar Abadi** `OUT1003` (Jakarta Barat) · Rp564 rb — Sales Andi, Budi
• Wilayah & kota terendah: Kalimantan (Rp144,2 jt) · Banjarmasin (Rp32,0 jt)
• Merek & sales terendah: Roni (Rp34,4 jt) · Bayu, Banjarmasin (Rp13,1 jt)

**5 Outlet Turun Terdalam (Sep → Okt)**

1. **Minimarket Sido Muncul** `OUT1043` · Palembang
   Rp9,2 jt → Rp2,9 jt (**−69%** · −Rp6,3 jt)
   5→3 faktur · Sales Zaki, Yudi (Zaki turun Rp6,8 jt)

2. **Toko Bintang** `OUT1022` · Semarang
   Rp8,8 jt → Rp3,2 jt (**−63%** · −Rp5,5 jt)
   6→4 faktur · Sales Kurnia, Lestari (Lestari −Rp3,3 jt, Kurnia −Rp2,3 jt)

3. **Toko Anugerah** `OUT1041` · Palembang
   Rp12,5 jt → Rp5,9 jt (**−53%** · −Rp6,6 jt)
   12→6 faktur · Sales Zaki, Yudi (Yudi −Rp3,4 jt, Zaki −Rp3,2 jt)

4. **Toko Mekar** `OUT1048` · Banjarmasin
   Rp5,1 jt → Rp2,5 jt (**−52%** · −Rp2,7 jt)
   5→3 faktur · Sales Bayu, Agus (Agus berhenti order dari Rp1,5 jt)

5. **Toko Sinar Abadi** `OUT1001` · Jakarta Barat
   Rp6,9 jt → Rp3,6 jt (**−48%** · −Rp3,4 jt)
   6→3 faktur · Sales Andi, Budi (Andi turun Rp3,0 jt)

**Akun Besar Turun Rupiah Terbesar**
• **Grosir Sentosa** `OUT1014` · Bandung · **−Rp31,6 jt** (−33%)
  12→9 faktur · Sales Gita, Hendra (Gita turun Rp37,6 jt)
• **Grosir Sumber Alam** `OUT1025` · Solo · **−Rp24,3 jt** (−31%)
  10→7 faktur · Sales Wahyu, Sari (Wahyu turun Rp14,8 jt)
• Sales turun terdalam: **Teguh**, Medan (**−44%** · −Rp27,5 jt)
```

*(Catatan UX dasbor web: agar pratinjau di halaman web tidak terlihat dipenuhi tanda bintang `**`, dasbor web dapat menampilkan pratinjau terformat yang bersih di layar sekaligus menyalin format Telegram `**bold**` + `` `kode` `` saat tombol **Salin briefing Telegram** ditekan.)*

---

## 5. Daftar Pustaka & Sumber Primer

1. **Telegram Core Protocol & Bot API Specifications**:
   - *Styled Text with Message Entities*: https://core.telegram.org/api/entities/
   - *MessageEntity TL Schema*: https://core.telegram.org/type/MessageEntity.md
   - *Bot API Formatting Options*: https://core.telegram.org/bots/api/formatting.md
   - *Telegram Official Blog — Collapsible Quotes & Compact Messaging (May 2024)*: https://www.telegram.org/blog/message-effects-and-more
   - *Telegram Official Blog — Quote Formatting (Oct 2023)*: https://www.telegram.org/blog/reply-revolution
2. **Kode Sumber Resmi Klien Telegram & Issue Tracker**:
   - *Telegram Desktop (`tdesktop`) — `InputField::kTagBold` (`**`), `kTagCode` (`` ` ``), & `PrepareRichFromPlain`*: `Telegram/SourceFiles/ui/widgets/input_fields.cpp` & `Telegram/SourceFiles/chat_helpers/message_field.cpp` (`https://github.com/telegramdesktop/tdesktop`)
   - *Telegram Desktop Clipboard Behavior*: https://github.com/telegramdesktop/tdesktop/issues/5795
   - *Telegram iOS — `richtext-composer.md` §7 (Markdown on Paste & `lineBreaks: .keep`)*: https://github.com/TelegramMessenger/Telegram-iOS/blob/master/docs/richtext-composer.md
   - *Telegram Monospace Tap-to-Copy & Web K Markdown Tracking*: https://bugs.telegram.org/c/5742 & https://bugs.telegram.org/c/66641
3. **Tipografi Layar Sempit, *Line-Breaking*, & Keterbacaan Pesan**:
   - *W3C Internationalization — Approaches to Line Breaking (`U+00A0 NO-BREAK SPACE`)*: https://www.w3.org/International/articles/typography/linebreak.en
   - *Matthew Butterick — Practical Typography: Nonbreaking Spaces*: https://practicaltypography.com/public/nonbreaking-spaces.html
   - *Google Chrome Developers — Modern Web Typography & Readability Guidelines*: https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/typography
   - *Slack Design Blog (2025) — Designing and Formatting Scannable Messages*: https://slack.com/blog/collaboration/designing-and-formatting-messages-in-slack
   - *Kate Moran (2016, NN/g) — Reading Content on Mobile Devices*: https://www.nngroup.com/articles/mobile-content/
   - *Hoa Loranger (2017, NN/g) — 7 Tips for Presenting Bulleted Lists*: https://www.nngroup.com/articles/presenting-bulleted-lists/
4. **Kaidah Resmi Bahasa Indonesia (EYD Edisi V & Badan Bahasa)**:
   - *SK Kepala Badan Pengembangan dan Pembinaan Bahasa No. 0424/I/BS.00.01/2022 tentang EYD Edisi V*: https://ejaan.kemdikbud.go.id/ & https://badanbahasa.kemdikbud.go.id/resource/doc/files/SK_EYD_Edisi_V_16082022.pdf
   - *EYD V — Angka dan Bilangan (`Rp` tanpa spasi, `%` rapat)*: https://ejaan.kemdikbud.go.id/eyd/penulisan-kata/angka-dan-bilangan/
   - *EYD V — Tanda Pisah (`—`)*: https://ejaan.kemdikbud.go.id/eyd/penggunaan-tanda-baca/tanda-pisah/
   - *S.S.T. Wisnu Sasangka (2019), Kalimat: Seri Penyuluhan Bahasa Indonesia (5 Ciri Kalimat Efektif)*: https://badanbahasa.kemendikdasmen.go.id/resource/doc/files/Buku_Seri_Penyuluhan_2019_Kalimat.pdf
   - *Sriyanto dkk. (2025), Seri Penyuluhan Bahasa Indonesia: Ejaan*: https://badanbahasa.kemendikdasmen.go.id/resource/doc/files/Seri_Penyuluhan_Bahasa_Indonesia_Ejaan2.pdf
5. **Narabahasa (Ivan Lanin) & UX Writing Bahasa Indonesia**:
   - *Ivan Lanin (2024) — Penulisan Rupiah (#481)*: https://ivanlanin.medium.com/penulisan-rupiah-6e976bdbea55
   - *Ivan Lanin (2023) — Apa Ciri Kalimat Efektif? (#43)*: https://ivanlanin.medium.com/apa-ciri-kalimat-efektif-41408c40837a
   - *Narabahasa (2022 & 2026) — Kiat Penulisan Efektif Layar Ponsel (detik Network) & Bedah Laporan BPKD*: https://narabahasa.id/berita/ivan-lanin-berbagi-kiat-penulisan-efektif-kepada-detik-network/ & https://narabahasa.id/berita/ivan-lanin-bedah-kesalahan-kaidah-di-laporan-bpkd/
   - *Sabariah, Lanin, & Yasmine (2024) — Analisis Kesalahan Berbahasa Laporan Bisnis (KOLITA 22)*: https://doi.org/10.25170/kolita.22.5967
   - *Telkom Indonesia — Legion Design System Writing Guideline (`<= 40` karakter & `<= 3` baris)*: https://legion.digitaltelkom.id/content/writing-guideline
   - *INA Digital / GovTech Indonesia — Panduan Desain: Fondasi Penulisan*: https://design.inadigital.go.id/foundation/writing/
   - *Gojek UX Writing — Language No Bar: How We Localise UX Copies at Gojek*: https://www.gojek.io/blog/language-no-bar-how-we-localise-ux-copies-at-gojek
   - *Microsoft Indonesian Localization Style Guide (§4.1.1 Currency, Abbreviations & Non-breaking Spaces)*: https://download.microsoft.com/download/c/2/8/c2804555-f6ed-4db9-9e3b-ddf754159bd3/ind-idn-StyleGuide.pdf
   - *SEAtongue (2026) — Indonesian Localization Guide (Affixation & Text Expansion)*: https://seatongue.com/resources/language-center/indonesian-localization-guide/
