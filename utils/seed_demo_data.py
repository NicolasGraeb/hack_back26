"""
Czyści tabele demo i wstawia 10 użytkowników, firm, kategorie, powiązania M:N oraz ogłoszenia.

  python utils/seed_demo_data.py

Wymaga wcześniej utworzonych tabel (utils/create_tables.py).
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_UTILS = Path(__file__).resolve().parent
if str(_UTILS) not in sys.path:
    sys.path.insert(0, str(_UTILS))

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Announcement, Category, Company, User

PITCHES: dict[int, str] = {
    1: """Cloudara (Edge AI & Quantum Security)
Cloudara to zdecentralizowana platforma chmurowa nowej generacji, oparta na architekturze Edge Computing i algorytmach odpornych na komputery kwantowe (Quantum-Safe). Zamiast centralizować dane, Cloudara wykorzystuje moc obliczeniową urządzeń końcowych (IoT), co redukuje opóźnienia do zera i gwarantuje absolutną prywatność. To infrastruktura gotowa na erę Web3 i maszyn autonomicznych.""",
    2: """Digmio (Autonomiczne Roje Górnicze)
Digmio nie produkuje wierteł — tworzy autonomiczne, zrobotyzowane roje (swarms) do bezzałogowego wydobycia surowców krytycznych. Wykorzystując fuzję danych z czujników lidarowych i AI, mikromaszyny Digmio potrafią mapować i eksploatować złoża w miejscach niedostępnych dla ludzi, minimalizując degradację środowiska na powierzchni o 90%.""",
    3: """Polionix (Decentralized Rendering Network)
Polionix to sieć rozproszonego renderowania dla metaverse i gamingu AAA. Zamiast stawiać własne serwery, algorytm Polionix w czasie rzeczywistym skupuje niewykorzystaną moc obliczeniową z kart graficznych użytkowników na całym świecie i przekierowuje ją do renderowania zaawansowanych symulacji fizycznych w grach. To Airbnb dla mocy obliczeniowej z ultra-niskimi opóźnieniami.""",
    4: """Reviver (AED) — predykcja kardiologiczna i drony ratunkowe
Reviver tworzy zintegrowany system ratowania życia: medyczne urządzenia ubieralne (wearables), które z 24-godzinnym wyprzedzeniem przewidują nagłe zatrzymanie krążenia dzięki analizie biomarkerów przez AI. Przy wykryciu zagrożenia system automatycznie dysponuje autonomicznego drona z miniaturowym, inteligentnym defibrylatorem, zanim pacjent straci przytomność.""",
    5: """Zentatez (Biomimetyczne Drony Wodne)
Zentatez to startup inżynierii środowiskowej projektujący biomimetyczne drony nawodne. Maszyny z biodegradowalnych kompozytów z recyklingu pływają po rzekach i jeziorach 24/7. Dzięki wizji komputerowej autonomicznie wyłapują mikroplastik i toksyny, mapując stan zanieczyszczenia akwenów w czasie rzeczywistym dla instytucji publicznych.""",
    6: """Innovacini (Smart Money & Programowalne Finanse)
Innovacini to infrastruktura dla „pieniądza programowalnego” (Smart Money) i walut cyfrowych banków centralnych (CBDC). Firmy tworzą mikrokontrakty, w których płatność uwalnia się krok po kroku na podstawie danych z zewnętrznych API (np. po fizycznym przekroczeniu granicy przez ciężarówkę). Eliminuje to zatory płatnicze w gospodarce.""",
    7: """Magnerin (Personalizowana Neuro-Nutrycja)
Magnerin to biotechnologia i dietetyka: zamiast uniwersalnych pigułek — nanoboty i mikrokapsułki uwalniające magnez i nootropiki dokładnie tam, gdzie układ nerwowy wykazuje deficyty. Skład generuje AI na podstawie cotygodniowego, domowego sekwencjonowania mikrobiomu jelitowego.""",
    8: """Bully (Syntetyczna Hydratacja)
Bully to inteligentna hydratacja oparta na „Smart Bottle”. Użytkownik nie kupuje gotowego napoju — butelka z mikro-laboratorium syntetyzuje wodę z profilami aminokwasów i stymulantów wg tętna, stresu (smartwatch) i zapotrzebowania. Zero plastiku, pełna personalizacja.""",
    9: """Reviver Gaming — BCI i haptyka
Dział gaming porzuca tradycyjne kontrolery na rzecz interfejsów mózg–komputer (BCI) i kombinezonów haptycznych. Intencje ruchowe z kory mózgowej trafiają do gry z zerowym opóźnieniem (zero-latency neural input), a haptyka symuluje temperaturę, opór i teksturę wirtualnego świata na skórze gracza.""",
    10: """Lynkers (Lab-Grown Pet Nutrition)
Lynkers to food-tech redukujący ślad węglowy karmy dla zwierząt: pełnowartościowe mięso hodowane komórkowo (in vitro) w bioreaktorach, bez uboju. Technologia „programuje” profil białkowy pod wady genetyczne i choroby konkretnych ras psów i kotów.""",
}

# Nazwy kategorii (unikalne)
CATEGORY_NAMES = [
    "Edge AI, Web3 i quantum-safe",
    "Robotyka i autonomiczne systemy",
    "Rendering rozproszony i GPU",
    "Medtech, wearables i drony",
    "Środowisko, wody i biomimetyka",
    "FinTech, CBDC i smart money",
    "Biotech i neuro-nutrycja",
    "Food-tech i personalizacja napojów",
    "Gaming, BCI i interfejsy haptyczne",
    "Pet-tech i mięso in vitro",
]

# company_index 0..9 → lista nazw kategorii
COMPANY_CATEGORIES: list[list[str]] = [
    ["Edge AI, Web3 i quantum-safe", "Robotyka i autonomiczne systemy"],
    ["Robotyka i autonomiczne systemy", "Rendering rozproszony i GPU"],
    ["Rendering rozproszony i GPU"],
    ["Medtech, wearables i drony"],
    ["Środowisko, wody i biomimetyka", "Robotyka i autonomiczne systemy"],
    ["FinTech, CBDC i smart money"],
    ["Biotech i neuro-nutrycja"],
    ["Food-tech i personalizacja napojów", "Medtech, wearables i drony"],
    ["Gaming, BCI i interfejsy haptyczne"],
    ["Pet-tech i mięso in vitro", "Biotech i neuro-nutrycja"],
]

USERS_SEED = [
    ("Anna", "Nowak", "cloudara@demo.hackathon"),
    ("Bartosz", "Zieliński", "digmio@demo.hackathon"),
    ("Celina", "Kaczmarek", "polionix@demo.hackathon"),
    ("Damian", "Lewandowski", "reviver.aed@demo.hackathon"),
    ("Elżbieta", "Mazur", "zentatez@demo.hackathon"),
    ("Filip", "Woźniak", "innovacini@demo.hackathon"),
    ("Gabriela", "Krawczyk", "magnerin@demo.hackathon"),
    ("Hubert", "Pawlak", "bully@demo.hackathon"),
    ("Igor", "Sikora", "reviver.gaming@demo.hackathon"),
    ("Julia", "Ostrowska", "lynkers@demo.hackathon"),
]

COMPANIES_SEED = [
    ("Cloudara Sp. z o.o.", "5270004101", "ul. Edge 1, 50-001 Wrocław"),
    ("Digmio Sp. z o.o.", "5270004102", "ul. Górnicza 22, 40-001 Katowice"),
    ("Polionix Sp. z o.o.", "5270004103", "ul. Render 7, 00-001 Warszawa"),
    ("Reviver (AED) Sp. z o.o.", "5270004104", "ul. Ratunkowa 9, 31-001 Kraków"),
    ("Zentatez Sp. z o.o.", "5270004105", "ul. Nadrzeczna 4, 80-001 Gdańsk"),
    ("Innovacini Sp. z o.o.", "5270004106", "ul. Ledger 15, 90-001 Łódź"),
    ("Magnerin Sp. z o.o.", "5270004107", "ul. Neuronowa 3, 60-001 Poznań"),
    ("Bully Sp. z o.o.", "5270004108", "ul. Butelkowa 8, 20-001 Lublin"),
    ("Reviver Gaming Sp. z o.o.", "5270004109", "ul. Haptyczna 11, 15-001 Białystok"),
    ("Lynkers Sp. z o.o.", "5270004110", "ul. Bioreaktorowa 6, 35-001 Rzeszów"),
]

# Demo — fikcyjny kontakt (nie prawdziwe dane)
COMPANY_CONTACTS: list[tuple[str, str]] = [
    ("+48 22 555 01 01", "kontakt@cloudara.demo"),
    ("+48 32 555 02 02", "biuro@digmio.demo"),
    ("+48 22 555 03 03", "hello@polionix.demo"),
    ("+48 12 555 04 04", "aed@reviver.demo"),
    ("+48 58 555 05 05", "kontakt@zentatez.demo"),
    ("+48 42 555 06 06", "team@innovacini.demo"),
    ("+48 61 555 07 07", "lab@magnerin.demo"),
    ("+48 81 555 08 08", "hey@bully.demo"),
    ("+48 85 555 09 09", "gaming@reviver.demo"),
    ("+48 17 555 10 10", "pets@lynkers.demo"),
]

# Widełki w PLN (opcjonalnie) — co druga firma bez widełek
ANNOUNCEMENT_SALARIES: list[tuple[Decimal | None, Decimal | None]] = [
    (Decimal("12000"), Decimal("18000")),
    (None, None),
    (Decimal("15000"), Decimal("22000")),
    (None, None),
    (Decimal("9000"), Decimal("14000")),
    (Decimal("20000"), Decimal("28000")),
    (None, None),
    (Decimal("8500"), Decimal("12000")),
    (Decimal("11000"), Decimal("16000")),
    (None, None),
]


def _truncate(session: Session) -> None:
    session.execute(
        text(
            "TRUNCATE announcements, company_categories, companies, categories, users "
            "RESTART IDENTITY CASCADE"
        )
    )
    session.commit()


def run_seed(*, truncate: bool = True) -> None:
    with SessionLocal() as session:
        if truncate:
            _truncate(session)

        for name in CATEGORY_NAMES:
            session.add(Category(name=name))
        session.flush()

        cats = {
            c.name: c
            for c in session.scalars(select(Category)).all()
        }

        users: list[User] = []
        for fn, sn, em in USERS_SEED:
            u = User(name=fn, surname=sn, email=em)
            session.add(u)
            users.append(u)
        session.flush()

        companies: list[Company] = []
        for i, (cname, nip, addr) in enumerate(COMPANIES_SEED):
            phone, email = COMPANY_CONTACTS[i]
            co = Company(
                name=cname,
                nip_krs=nip,
                user_id=users[i].id,
                address=addr,
                image_url=None,
                contact_phone=phone,
                contact_email=email,
            )
            session.add(co)
            companies.append(co)
        session.flush()

        for i, co in enumerate(companies):
            for cat_name in COMPANY_CATEGORIES[i]:
                co.categories.append(cats[cat_name])

            smin, smax = ANNOUNCEMENT_SALARIES[i]
            session.add(
                Announcement(
                    company_id=co.id,
                    salary_min=smin,
                    salary_max=smax,
                    description=PITCHES[co.id],
                )
            )

        session.commit()
        print(
            f"OK: {len(users)} użytkowników, {len(companies)} firm, "
            f"{len(CATEGORY_NAMES)} kategorii, ogłoszenia + powiązania M:N."
        )


def main() -> None:
    run_seed(truncate=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}", file=sys.stderr)
        raise SystemExit(1) from e
