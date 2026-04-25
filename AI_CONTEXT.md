# AI_CONTEXT.md
# GNX STUDIO (AutoShorts)

## PROJECT
GNX STUDIO adalah aplikasi desktop Python untuk automation konten video, termasuk upload, AI workflow, social media integration, dan pipeline publishing.

## GOAL
- clean architecture
- scalable system
- modern UI/UX
- siap integrasi AI & automation
- mudah dipahami user awam
- siap di-upgrade ke web/cloud

---

## STRUKTUR PROYEK

- `core/` → business logic, use case, viewmodel, validation, rules
- `core/ui_blueprint/` → navigation schema, page specs, component rules, UX states
- `core/dashboard/` → dashboard viewmodel / dashboard use case
- `core/accounts/` → account overview, connect account use case
- `core/generate/` → generate flow, input validation
- `core/queue/` → queue overview / queue logic
- `core/publish/` → publish summary / publish logic
- `core/projects/` → project overview / project logic

- `services/` → external API / third-party integration
- `services/youtube/` → YouTube auth / YouTube integration
- `services/social/` → social account integration
- `services/content/` → publishing service / content delivery

- `ui/components/` → reusable UI components
- `ui/pages/` → page rendering, page layout, event binding
- `ui/theme/` → design tokens, colors, typography, visual system

- `worker/` → background processing, queue, async task
- `config/` → konfigurasi
- `data/` → logs, tokens, cache, local storage
- `scripts/` → tools / helper scripts
- `main.py` → entry point / app bootstrap

---

## FLOW ARSITEKTUR

UI (user action)  
↓  
core (process logic / use case / viewmodel)  
↓  
services (API call / external integration)  
↓  
result kembali ke UI  

---

## RULE WAJIB

### 1. Pemisahan tanggung jawab
- UI **tidak boleh** mengandung business logic berat
- UI **tidak boleh** akses file langsung
- UI **tidak boleh** API call langsung
- Semua business logic **harus** di `core/`
- Semua external API / integration **harus** di `services/`
- `worker/` hanya untuk background processing
- `ui/pages/` hanya untuk page rendering dan event ringan
- `ui/components/` harus reusable dan tidak berisi business logic
- `ui/theme/` menjadi sumber style bersama
- keputusan bisnis **jangan** diletakkan di UI

### 2. Scope kerja
- Fokus hanya pada task yang diminta
- Jangan refactor di luar scope
- Jangan ubah struktur besar tanpa alasan kuat
- Jangan tambah fitur di task DEBUG atau REFACTOR jika tidak diminta
- Jika task besar, pecah jadi langkah yang masuk akal

### 3. Standar hasil
- clean
- modular
- readable
- scalable
- hindari duplikasi
- gunakan fungsi kecil dan jelas
- hasil harus siap tempel / siap pakai
- prioritaskan struktur yang mudah dipahami user dan developer

---

## POLA ARSITEKTUR YANG DIUTAMAKAN

Jika relevan, gunakan pola berikut:
- `core/*` untuk use case, validator, viewmodel builder, state builder
- `services/*` untuk adapter API / auth / publish / network
- `ui/components/*` untuk komponen reusable
- `ui/pages/*` untuk menyusun page dari komponen dan menghubungkan event ke core
- `ui/theme/*` untuk warna, typography, spacing, token visual

Utamakan:
- viewmodel/usecase pattern
- reusable components
- shared theme system
- UX state yang jelas: loading, empty, success, error

---

## MODE OPERASI

### DEBUG
Gunakan mode ini jika:
- ada error
- ada traceback
- ada import gagal
- login / auth gagal
- data tidak muncul
- callback macet
- behavior salah
- hasil UI tidak sesuai

Aturan DEBUG:
- fokus ke penyebab error
- beri fix paling simpel
- ubah sesedikit mungkin
- jangan refactor besar
- pertahankan arsitektur `core / services / ui`
- jangan ubah behavior lain di luar masalah utama

Output DEBUG wajib:
1. penyebab singkat
2. lokasi file
3. fix langsung
4. langkah test singkat

---

### FEATURE
Gunakan mode ini jika:
- membuat fitur baru
- menambah modul baru
- menambah integrasi baru
- menambah flow baru
- mendesain ulang UX/UI
- menambah reusable component
- menambah page baru

Aturan FEATURE:
- buat struktur file yang benar
- business logic di `core/`
- API di `services/`
- reusable UI di `ui/components/`
- halaman di `ui/pages/`
- style system di `ui/theme/`
- UI hanya integrasi dan event handler
- hasil harus scalable dan mudah dikembangkan
- jika relevan, gunakan pola use case / viewmodel / validator

Output FEATURE wajib:
1. struktur file
2. tanggung jawab tiap file
3. kode siap pakai
4. alur integrasi UI → core → services → UI

---

### REFACTOR
Gunakan mode ini jika:
- fitur sudah jalan
- tapi struktur kode berantakan
- UI terlalu banyak logic
- logic harus dipindah ke `core/`
- ada duplikasi komponen UI
- style belum konsisten
- code perlu dirapikan tanpa mengubah hasil

Aturan REFACTOR:
- pisahkan UI dan logic
- pindahkan business logic ke `core/`
- API tetap di `services/`
- ekstrak komponen umum ke `ui/components/`
- samakan styling ke `ui/theme/`
- jangan ubah behavior
- jangan tambah fitur baru
- lakukan perubahan seminimal mungkin

Output REFACTOR wajib:
1. masalah struktur singkat
2. file yang perlu diubah
3. hasil struktur refactor
4. kode final siap pakai per file

---

## RULE PEMILIHAN MODE

Pakai **DEBUG** jika:
- masih error
- masih gagal
- masih stuck
- hasil belum benar

Pakai **REFACTOR** jika:
- sudah jalan
- tapi kodenya belum rapi
- arsitektur belum sesuai
- komponen belum reusable
- styling belum konsisten

Pakai **FEATURE** jika:
- ingin menambah kemampuan baru
- ingin redesign page / UX
- ingin menambah modul / komponen / flow baru

Rule cepat:
- **Kalau belum jalan → DEBUG**
- **Kalau sudah jalan tapi belum rapi → REFACTOR**
- **Kalau mau tambah kemampuan / redesign → FEATURE**

---

## STANDAR UI/UX MODERN GNX STUDIO

Target UI/UX:
- modern
- clean
- mudah dipahami user awam
- visual hierarchy jelas
- minim kebingungan
- action utama mudah ditemukan
- empty state / loading / success / error terlihat jelas

Prinsip UI:
- satu page = satu tujuan utama
- gunakan reusable card, header, status, action bar, form section
- tampilkan status secara jelas
- hindari tampilan terlalu padat
- prioritaskan readability dan alur user

---

## FORMAT JAWABAN YANG DIINGINKAN DARI AI

- singkat
- jelas
- langsung ke inti
- sebutkan lokasi file
- jika memberi kode, harus versi final yang bisa langsung ditempel
- jangan terlalu panjang
- jangan melebar dari task
- tetap ikuti konteks GNX STUDIO

---

## TEMPLATE CEPAT

### MASTER PROMPT
Gunakan konteks GNX STUDIO: aplikasi desktop Python untuk automation konten video dengan clean architecture; business logic di core, API di services, reusable UI di ui/components, halaman di ui/pages, styling bersama di ui/theme, output singkat, jelas, dan siap pakai.

### DEBUG PROMPT
MODE: DEBUG — cari penyebab, sebutkan lokasi file, dan beri fix langsung paling kecil tanpa refactor besar; pertahankan arsitektur core/services/ui.

### FEATURE PROMPT
MODE: FEATURE — buat struktur file yang benar, logic di core, API di services, reusable UI di ui/components, halaman di ui/pages, styling bersama di ui/theme, dan UI hanya integrasi/event handler.

### REFACTOR PROMPT
MODE: REFACTOR — pisahkan UI dan logic, pindahkan business logic ke core, API tetap di services, ekstrak komponen reusable ke ui/components, gunakan ui/theme, jangan ubah behavior.

---

## TEMPLATE PAKAI

### DEBUG
Gunakan konteks GNX STUDIO.

MODE: DEBUG

Error:
(paste error)

Kode:
(paste kode)

Tugas:
- cari penyebab
- sebutkan lokasi file
- beri fix langsung

---

### FEATURE
Gunakan konteks GNX STUDIO.

MODE: FEATURE

Fitur:
(jelaskan fitur)

Tugas:
- buat struktur file
- logic di core
- API di services
- reusable UI di ui/components
- halaman di ui/pages
- styling di ui/theme
- UI integrasi

---

### REFACTOR
Gunakan konteks GNX STUDIO.

MODE: REFACTOR

File:
(paste file)

Tugas:
- pisahkan UI dan logic
- pindahkan business logic ke core
- ekstrak komponen reusable jika perlu
- samakan style ke ui/theme
- jangan ubah behavior