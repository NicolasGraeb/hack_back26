RAG_ROLE = """Jesteś ekspertem od funduszy europejskich. Przeanalizuj KONTEKST i dopasuj go do PROFILU FIRMY na podstawie PYTANIA."""

OUTPUT_RULES = """Twoim zadaniem jest zwrócenie wyników WYŁĄCZNIE w formacie JSON, bez żadnego dodatkowego tekstu na początku ani na końcu (żadnych powitań czy formatowania markdown typu ```json).

Użyj dokładnie poniższej struktury:"""

JSON_SHAPE = """
{
  "rekomendacje": [
    {
      "nazwa_programu": "Pełna nazwa programu z bazy",
      "dopasowanie": "Wysokie, Srednie lub Niskie",
      "uzasadnienie": "Krótkie wyjaśnienie (1-2 zdania), dlaczego ten program pasuje do firmy",
      "na_co_mozna_wydac": ["lista", "kwalifikowalnych", "kosztow", "znalezionych", "w", "kontekscie"]
    }
  ],
  "braki_w_bazie": "Jeśli firma szuka czegoś, czego nie ma w kontekście, opisz to krótko tutaj. Jeśli baza pokrywa wszystko, zostaw null."
}
"""


CHAT_SYSTEM = """Jesteś Asystentem Finansowań w mStartup. Odpowiadasz po polsku, na tematy: granty, inwestycje, runway, rozmowy z inwestorem, budżet startupu.
Nie wymyślaj konkretnych kwot ani nazw programów „na pewno” — jeśli nie masz pewności, napisz to w polu sources_line.
Zawsze uwzględniaj opis firmy poniżej; rozmawiasz z przedstawicielem tej firmy — nie pytaj „o jaką firmę chodzi”.

KRYTYCZNE — FORMAT WYJŚCIA:
Zwróć WYŁĄCZNIE jeden obiekt JSON (UTF-8). Żadnego tekstu przed ani po, żadnych ```markdown```, żadnych komentarzy.
Wartości w JSON mają być zwykłym tekstem (bez **bold**, bez numerowanych list w stringu — listy tylko w tablicach bullets).
Pisz zwięźle: krótkie zdania, mało słów na punkt."""


# Stały kontekst czatu (hackathon / demo) — docelowo z /me lub konfiguracji.
CHAT_FIXED_COMPANY_PROFILE = """Cloudara — moja firma

Cloudara to zdecentralizowana platforma chmurowa nowej generacji, oparta na architekturze Edge Computing i algorytmach odpornych na komputery kwantowe (Quantum-Safe). Zamiast centralizować dane, Cloudara wykorzystuje moc obliczeniową urządzeń końcowych (IoT), co redukuje opóźnienia do zera i gwarantuje absolutną prywatność. To infrastruktura gotowa na erę Web3 i maszyn autonomicznych."""


CHAT_JSON_SHAPE = """
{
  "headline": "Krótki nagłówek (np. typ projektu / segment, max ~80 znaków)",
  "lead": "1–2 zdania sedna odpowiedzi",
  "tracks": [
    {
      "id": "grant|vc|partner|accelerator|other",
      "label": "Krótka etykieta kierunku (np. Granty B+R)",
      "summary": "Jedno zdanie — dlaczego to pasuje do firmy",
      "bullets": ["Konkret 1", "Konkret 2", "Konkret 3"]
    }
  ],
  "sources_line": "Gdzie sprawdzić terminy (np. NCBR, PARP, Funding & Tenders) — jedna linia",
  "follow_up": "Jedno krótkie pytanie kontynuujące albo null"
}
"""

CHAT_JSON_RULES = """Wymagania do treści JSON:
- "tracks": od 2 do 5 elementów; każdy ma 2–4 bullets (krótkie frazy lub zdania, bez powtórzeń między ścieżkami).
- Nie pisz „ścian tekstu” w jednym polu — rozbij na tracks i bullets.
- "follow_up": null jeśli pytanie użytkownika było zamknięte i nie ma sensownej kontynuacji."""


def build_chat_prompt(transcript: str) -> str:
    return "\n\n".join(
        [
            CHAT_SYSTEM,
            "",
            "Struktura JSON (dokładnie te klucze; tracks to tablica obiektów):",
            CHAT_JSON_SHAPE.strip(),
            "",
            CHAT_JSON_RULES.strip(),
            "",
            "OPIS MOJEJ FIRMY (kontekst obowiązkowy):",
            CHAT_FIXED_COMPANY_PROFILE.strip(),
            "",
            "Rozmowa:",
            transcript,
            "",
            "Odpowiedz na ostatnią wypowiedź użytkownika. Zwróć TYLKO JSON zgodny ze strukturą powyżej.",
        ]
    )


def build_rag_prompt(context: str, company_profile: str, question: str) -> str:
    return "\n".join(
        [
            RAG_ROLE,
            "",
            OUTPUT_RULES,
            JSON_SHAPE.strip(),
            "",
            "KONTEKST Z BAZY:",
            context,
            "",
            "PROFIL FIRMY:",
            company_profile,
            "",
            "PYTANIE:",
            question,
        ]
    )
