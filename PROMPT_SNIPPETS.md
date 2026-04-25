# PROMPT_SNIPPETS.md
# GNX STUDIO Prompt Snippets

## MASTER
​
Gunakan konteks GNX STUDIO: aplikasi desktop Python untuk automation konten video dengan clean architecture; UI ringan, semua logic di core, semua API di services, output singkat, jelas, dan siap pakai.

---

## DEBUG
​
Gunakan konteks GNX STUDIO.
MODE: DEBUG
Cari penyebab, sebutkan lokasi file, dan beri fix langsung paling kecil tanpa refactor besar.
Error:
(paste error)
Kode:
(paste kode)

### DEBUG 1 BARIS
​
MODE: DEBUG — cari penyebab, lokasi file, dan fix langsung paling kecil tanpa refactor besar.

---

## REFACTOR
​
Gunakan konteks GNX STUDIO.
MODE: REFACTOR
Pisahkan UI dan logic, pindahkan logic ke core, API tetap di services, jangan ubah behavior.
File:
(paste file)

### REFACTOR 1 BARIS
​
MODE: REFACTOR — pisahkan UI dan logic, pindahkan logic ke core, API tetap di services, jangan ubah behavior.

---

## FEATURE
​
Gunakan konteks GNX STUDIO.
MODE: FEATURE
Buat struktur file yang benar, logic di core, API di services, UI hanya integrasi dan event handler.
Fitur:
(jelaskan fitur)
Konteks tambahan:
(paste file terkait jika ada)

### FEATURE 1 BARIS
​
MODE: FEATURE — buat struktur file yang benar, logic di core, API di services, UI hanya integrasi dan event handler.

---

## QUICK START

### Mulai chat DEBUG
​
Gunakan konteks GNX STUDIO: aplikasi desktop Python untuk automation konten video dengan clean architecture; UI ringan, semua logic di core, semua API di services, output singkat, jelas, dan siap pakai.
MODE: DEBUG
Cari penyebab, sebutkan lokasi file, dan beri fix langsung paling kecil tanpa refactor besar.
Error:
...
Kode:
...

### Mulai chat REFACTOR
​
Gunakan konteks GNX STUDIO: aplikasi desktop Python untuk automation konten video dengan clean architecture; UI ringan, semua logic di core, semua API di services, output singkat, jelas, dan siap pakai.
MODE: REFACTOR
Pisahkan UI dan logic, pindahkan logic ke core, API tetap di services, jangan ubah behavior.
File:
...

### Mulai chat FEATURE
​
Gunakan konteks GNX STUDIO: aplikasi desktop Python untuk automation konten video dengan clean architecture; UI ringan, semua logic di core, semua API di services, output singkat, jelas, dan siap pakai.
MODE: FEATURE
Buat struktur file yang benar, logic di core, API di services, UI hanya integrasi dan event handler.
Fitur:
...
Konteks tambahan:
...

---

## RULE CEPAT
​
Kalau belum jalan → DEBUG
Kalau sudah jalan tapi belum rapi → REFACTOR
Kalau mau tambah kemampuan → FEATURE