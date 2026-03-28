-- Jednorazowo na istniejącej bazie (jeśli tabele były tworzone wcześniej bez image_url)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS image_url TEXT;
