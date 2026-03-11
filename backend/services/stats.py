import sqlite3

conn = sqlite3.connect('arbitro.db')
cursor = conn.cursor()

# ZMIEŃ TO NA SWOJE DANE (dokładnie tak jak w PZPN24)
MOJE_NAZWISKO = "Martowicz Jan"

print(f"📊 STATYSTYKI DLA: {MOJE_NAZWISKO}\n" + "="*40)

# --- PYTANIE 1: W ilu meczach łącznie brałem udział? ---
cursor.execute('''
SELECT COUNT(*) 
FROM obsady 
JOIN sedziowie ON obsady.sedzia_id = sedziowie.id 
WHERE sedziowie.imie_nazwisko = ?
''', (MOJE_NAZWISKO,))

ile_meczy = cursor.fetchone()[0]
print(f"🏟️ Łączna liczba meczów w bazie: {ile_meczy}")


# --- PYTANIE 2: Jakie role pełniłem najczęściej? ---
cursor.execute('''
SELECT obsady.rola, COUNT(*) 
FROM obsady
JOIN sedziowie ON obsady.sedzia_id = sedziowie.id
WHERE sedziowie.imie_nazwisko = ?
GROUP BY obsady.rola
ORDER BY COUNT(*) DESC
''', (MOJE_NAZWISKO,))

print("\n🎭 Moje role w meczach:")
for rola, ilosc in cursor.fetchall():
    print(f"  - {rola}: {ilosc} razy")


# --- PYTANIE 3: Z kim z głównych najczęściej biegałem na linii? ---
# To jest tzw. zapytanie zaawansowane (szuka Ciebie jako asystenta i kogoś innego jako głównego w TYM SAMYM meczu)
cursor.execute('''
SELECT s_glowny.imie_nazwisko, COUNT(*) as ilosc_wspolnych
FROM obsady o_ja
JOIN sedziowie s_ja ON o_ja.sedzia_id = s_ja.id
JOIN mecze m ON o_ja.mecz_id = m.mecz_id
JOIN obsady o_glowny ON m.mecz_id = o_glowny.mecz_id
JOIN sedziowie s_glowny ON o_glowny.sedzia_id = s_glowny.id
WHERE s_ja.imie_nazwisko = ? 
  AND (o_ja.rola = 'First assistant referee' OR o_ja.rola = 'Second assistant referee')
  AND o_glowny.rola = 'Main judge'
GROUP BY s_glowny.imie_nazwisko
ORDER BY ilosc_wspolnych DESC
LIMIT 5
''', (MOJE_NAZWISKO,))

print("\n🤝 Sędziowie główni, którym najczęściej asystowałem (Top 5):")
for glowny, ilosc in cursor.fetchall():
    print(f"  - {glowny}: {ilosc} wspólnych meczów")

# --- PYTANIE 5: Kto najczęściej mi asystował, gdy ja byłem Sędzią głównym? ---
cursor.execute('''
SELECT s_asystent.imie_nazwisko, COUNT(*) as ilosc_asyst
FROM obsady o_ja
JOIN sedziowie s_ja ON o_ja.sedzia_id = s_ja.id
JOIN mecze m ON o_ja.mecz_id = m.mecz_id
JOIN obsady o_asystent ON m.mecz_id = o_asystent.mecz_id
JOIN sedziowie s_asystent ON o_asystent.sedzia_id = s_asystent.id
WHERE s_ja.imie_nazwisko = ? 
  AND o_ja.rola = 'Main judge' 
  AND (o_asystent.rola = 'First assistant referee' OR o_asystent.rola = 'Second assistant referee')
GROUP BY s_asystent.imie_nazwisko
ORDER BY ilosc_asyst DESC
LIMIT 5
''', (MOJE_NAZWISKO,))

print("\n🚩 Asystenci, którzy najczęściej biegali na moich liniach (Top 5):")
for asystent, ilosc in cursor.fetchall():
    print(f"  - {asystent}: {ilosc} wspólnych meczów jako mój asystent")


# --- PYTANIE 4: Z kim ze wszystkich sędziów spotykałem się na meczach najczęściej? ---
# Niezależnie od ról - po prostu sprawdzamy, kto był w tej samej obsadzie co Ty.
cursor.execute('''
SELECT s_inny.imie_nazwisko, COUNT(*) as liczba_wspolnych_meczow
FROM obsady o_ja
JOIN sedziowie s_ja ON o_ja.sedzia_id = s_ja.id
JOIN obsady o_inny ON o_ja.mecz_id = o_inny.mecz_id
JOIN sedziowie s_inny ON o_inny.sedzia_id = s_inny.id
WHERE s_ja.imie_nazwisko = ? 
  AND s_inny.imie_nazwisko != ? -- Wykluczamy Ciebie z wyników, żebyś nie był na 1 miejscu!
GROUP BY s_inny.imie_nazwisko
ORDER BY liczba_wspolnych_meczow DESC
LIMIT 10
''', (MOJE_NAZWISKO, MOJE_NAZWISKO))

print("\n👥 Top 10 sędziów, z którymi najczęściej sędziowałem (dowolna rola):")
for sedzia, ilosc in cursor.fetchall():
    print(f"  - {sedzia}: {ilosc} wspólnych meczów")

    
conn.close()