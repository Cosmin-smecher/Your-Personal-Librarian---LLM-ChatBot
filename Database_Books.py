#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creează o bază de date SQLite "book_summaries.db" cu 20 de cărți.
Tabel: book_summaries(id, title, author, year, language, summary, themes)
- summary: 3–5 rânduri (separate prin newline) cu un rezumat scurt, fără spoilere majore
- themes: listă separată prin virgulă (ex: "prietenie, aventură, maturizare")
Rulare: python create_book_summaries_db.py
După rulare, fișierul DB se află în ./book_summaries.db
"""

import sqlite3
from pathlib import Path

DB_NAME = "book_summaries.db"

BOOKS = [
    {
        "title": "1984",
        "author": "George Orwell",
        "year": 1949,
        "language": "ro",
        "summary": (
            "Într-un stat totalitar, Partidul controlează fiecare aspect al vieții.\n"
            "Winston Smith începe să se îndoiască de propaganda oficială și caută adevărul.\n"
            "O relație interzisă îi dă curajul să sfideze sistemul.\n"
            "Lupta pentru libertate îl pune față în față cu supravegherea și manipularea."
        ),
        "themes": "totalitarism, supraveghere, libertate, manipulare"
    },
    {
        "title": "Hobbitul",
        "author": "J.R.R. Tolkien",
        "year": 1937,
        "language": "ro",
        "summary": (
            "Bilbo Baggins pornește într-o călătorie neașteptată alături de treisprezece pitici.\n"
            "Drumul îi dezvăluie curajul ascuns și lumea vastă dincolo de Comitat.\n"
            "Întâlnește creaturi periculoase și descoperă un inel misterios.\n"
            "Aventura îl transformă dintr-un hobbit comod într-un erou ingenios."
        ),
        "themes": "aventură, curaj, auto-descoperire, prietenie"
    },
    {
        "title": "Să ucizi o pasăre cântătoare",
        "author": "Harper Lee",
        "year": 1960,
        "language": "ro",
        "summary": (
            "În sudul Segregat al SUA, Scout Finch observă nedreptatea prin ochii copilăriei.\n"
            "Tatăl ei, Atticus, apără un bărbat de culoare acuzat pe nedrept.\n"
            "Procesul expune prejudecăți adânc înrădăcinate în comunitate.\n"
            "Familia învață ce înseamnă empatia și curajul moral."
        ),
        "themes": "justiție, rasism, empatie, familie"
    },
    {
        "title": "Mândrie și prejudecată",
        "author": "Jane Austen",
        "year": 1813,
        "language": "ro",
        "summary": (
            "Elizabeth Bennet și domnul Darcy se confruntă cu prime impresii înșelătoare.\n"
            "Normele sociale și așteptările de clasă complică relațiile.\n"
            "În timp, sinceritatea și autocunoașterea schimbă perspectivele.\n"
            "Dragostea se conturează prin depășirea mândriei și prejudecăților."
        ),
        "themes": "dragoste, clasă socială, maturizare, familie"
    },
    {
        "title": "De veghe în lanul de secară",
        "author": "J.D. Salinger",
        "year": 1951,
        "language": "ro",
        "summary": (
            "Holden Caulfield rătăcește prin New York după ce părăsește internatul.\n"
            "Își caută sensul într-o lume pe care o percepe ca falsă.\n"
            "Întâlnirile îl dezvăluie vulnerabil și cinic deopotrivă.\n"
            "Legătura cu sora lui îi oferă o ancoră de sinceritate."
        ),
        "themes": "alienare, identitate, maturizare, familie"
    },
    {
        "title": "Marele Gatsby",
        "author": "F. Scott Fitzgerald",
        "year": 1925,
        "language": "ro",
        "summary": (
            "În epoca jazzului, Jay Gatsby își urmărește visul și o iubire imposibilă.\n"
            "Petrecerile somptuoase ascund dorințe și iluzii fragile.\n"
            "Narațiunea lui Nick Carraway dezvăluie ipocrizia clasei înstărite.\n"
            "Visul american capătă nuanțe de nostalgie și deziluzie."
        ),
        "themes": "visul american, iubire, clasă socială, iluzie"
    },
    {
        "title": "Moby-Dick",
        "author": "Herman Melville",
        "year": 1851,
        "language": "ro",
        "summary": (
            "Căpitanul Ahab pornește într-o urmărire obsesivă a balenei albe.\n"
            "Echipajul corăbiei Pequod trăiește frica și fascinația oceanului.\n"
            "Povestea îmbină aventură nautică, filozofie și mit.\n"
            "Obsesia conduce către un deznodământ inevitabil."
        ),
        "themes": "obsesie, destin, natură, aventură"
    },
    {
        "title": "Crimă și pedeapsă",
        "author": "Fiodor Dostoievski",
        "year": 1866,
        "language": "ro",
        "summary": (
            "Raskolnikov comite o crimă, convins că scopul îi justifică fapta.\n"
            "Conștiința îl macină între vinovăție și justificare intelectuală.\n"
            "Întâlnirile cu Sonia deschid calea spre compasiune.\n"
            "Mântuirea devine posibilă prin recunoaștere și suferință."
        ),
        "themes": "vinovăție, morală, mântuire, psihologie"
    },
    {
        "title": "Război și pace",
        "author": "Lev Tolstoi",
        "year": 1869,
        "language": "ro",
        "summary": (
            "Roman panoramic al Rusiei în timpul invaziilor napoleoniene.\n"
            "Destinele familiilor Rostov, Bolkonski și Bezuhov se împletesc.\n"
            "Bătăliile alternează cu reflecții despre istorie și liber arbitru.\n"
            "Iubirea și datoria capătă sens în mijlocul haosului."
        ),
        "themes": "istorie, familie, iubire, soartă"
    },
    {
        "title": "Stăpânul Inelelor: Frăția Inelului",
        "author": "J.R.R. Tolkien",
        "year": 1954,
        "language": "ro",
        "summary": (
            "Frodo moștenește Inelul Puterii și misiunea de a-l distruge.\n"
            "O frăție diversă îl însoțește prin Ținutul de Mijloc.\n"
            "Răul crește în umbră, iar prietenia este pusă la încercare.\n"
            "Călătoria începe cu speranță, teamă și hotărâre."
        ),
        "themes": "aventură, prietenie, sacrificiu, bine vs. rău"
    },
    {
        "title": "Harry Potter și Piatra Filozofală",
        "author": "J.K. Rowling",
        "year": 1997,
        "language": "ro",
        "summary": (
            "Un băiat descoperă că este vrăjitor și ajunge la Hogwarts.\n"
            "Noi prieteni și secrete ale lumii magice îi schimbă viața.\n"
            "Misterul Pietrei Filozofale îi pune curajul la încercare.\n"
            "Descoperă puterea prieteniei și a alegerilor."
        ),
        "themes": "prietenie, curaj, descoperire de sine, magie"
    },
    {
        "title": "Alchimistul",
        "author": "Paulo Coelho",
        "year": 1988,
        "language": "ro",
        "summary": (
            "Păstorul Santiago pornește spre Egipt în căutarea comorii sale.\n"
            "Întâlnirile devin lecții despre semne și destin personal.\n"
            "Călătoria exterioară reflectă transformarea interioară.\n"
            "Visurile capătă sens când îți asculți inima."
        ),
        "themes": "destin, sensul vieții, spiritualitate, călătorie"
    },
    {
        "title": "Micul Prinț",
        "author": "Antoine de Saint-Exupéry",
        "year": 1943,
        "language": "ro",
        "summary": (
            "Un pilot rătăcit în deșert întâlnește un băiat venit de pe o planetă mică.\n"
            "Poveștile sale dezvăluie esența prieteniei și a responsabilității.\n"
            "Simplicitatea aparentă ascunde reflecții profunde despre iubire.\n"
            "„Esentialul este invizibil pentru ochi” devine lecția centrală."
        ),
        "themes": "prietenie, inocență, responsabilitate, iubire"
    },
    {
        "title": "Minunata lume nouă",
        "author": "Aldous Huxley",
        "year": 1932,
        "language": "ro",
        "summary": (
            "O societate futuristă reglează fericirea prin control și condiționare.\n"
            "Bernard și John „Sălbaticul” pun sub semnul întrebării stabilitatea.\n"
            "Plăcerea standardizată intră în conflict cu libertatea autentică.\n"
            "Progresul devine ambiguu când exclude umanitatea."
        ),
        "themes": "distopie, libertate, tehnologie, conformism"
    },
    {
        "title": "Fahrenheit 451",
        "author": "Ray Bradbury",
        "year": 1953,
        "language": "ro",
        "summary": (
            "Cărturarul Montag trăiește într-o lume unde cărțile sunt arse.\n"
            "O întâlnire îi trezește curiozitatea și sete de cunoaștere.\n"
            "Începe să pună întrebări periculoase despre libertatea de gândire.\n"
            "Rebeliunea sa aprinde scânteia schimbării."
        ),
        "themes": "cenzură, cunoaștere, libertate, conformism"
    },
    {
        "title": "Numele trandafirului",
        "author": "Umberto Eco",
        "year": 1980,
        "language": "ro",
        "summary": (
            "Într-o mănăstire medievală, o serie de morți misterioase tulbură ordinea.\n"
            "Călugărul William de Baskerville investighează cu logică și erudiție.\n"
            "Biblioteca ascunde secrete periculoase despre puterea cunoașterii.\n"
            "Adevărul se împletește cu simboluri, interdicții și frică."
        ),
        "themes": "mister, cunoaștere, religie, putere"
    },
    {
        "title": "Un veac de singurătate",
        "author": "Gabriel García Márquez",
        "year": 1967,
        "language": "ro",
        "summary": (
            "Saga familiei Buendía urmărește destinul orașului Macondo.\n"
            "Magicul și cotidianul conviețuiesc într-o istorie ciclică.\n"
            "Iubirile, dorințele și singurătățile se repetă între generații.\n"
            "Timpul pare un cerc, nu o linie."
        ),
        "themes": "realism magic, familie, destin, timp"
    },
    {
        "title": "Vânătorii de zmeie",
        "author": "Khaled Hosseini",
        "year": 2003,
        "language": "ro",
        "summary": (
            "Amir și Hassan cresc în Kabul, legați de o prietenie complexă.\n"
            "O trădare din copilărie lasă răni adânci și nevoia de iertare.\n"
            "Războiul schimbă țara și destinele lor pentru totdeauna.\n"
            "Curajul de a repara trecutul devine miza vieții adulte."
        ),
        "themes": "prietenie, vinovăție, iertare, război"
    },
    {
        "title": "Fata cu un dragon tatuat",
        "author": "Stieg Larsson",
        "year": 2005,
        "language": "ro",
        "summary": (
            "Jurnalistul Blomkvist investighează dispariția unei tinere dintr-o familie influentă.\n"
            "Hackerul Lisbeth Salander aduce geniu și neconvențional în anchetă.\n"
            "Secrete vechi ies la iveală, amenințând vieți și reputații.\n"
            "Adevărul dezvăluie o rețea de corupție și violență."
        ),
        "themes": "mister, corupție, justiție, abuz"
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "year": 1965,
        "language": "ro",
        "summary": (
            "Pe planeta-deșert Arrakis, miza este controlul mirodeniei.\n"
            "Paul Atreides supraviețuiește trădării și se aliază cu fremenii.\n"
            "Ecologia planetei și profețiile modelează viitorul politic.\n"
            "Puterea se câștigă prin viziune, sacrificiu și adaptare."
        ),
        "themes": "politică, ecologie, destin, putere"
    },
    {
        "title": "Mândria oricărei biblioteci: Micul Prinț (ediție pentru copii)",
        "author": "Antoine de Saint-Exupéry",
        "year": 1943,
        "language": "ro",
        "summary": (
            "O versiune pentru copii care păstrează mesajele-cheie.\n"
            "Accent pe prietenie, imaginație și responsabilitate.\n"
            "Ilustrațiile și limbajul accesibil oferă o nouă intrare în univers.\n"
            "Invită la dialog între copii și părinți."
        ),
        "themes": "prietenie, familie, educație, imaginație"
    },
]

def init_db(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS book_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            author TEXT,
            year INTEGER,
            language TEXT DEFAULT 'ro',
            summary TEXT NOT NULL,
            themes TEXT
        );
        """
    )
    conn.commit()

def upsert_books(conn, books):
    cur = conn.cursor()
    for b in books:
        cur.execute(
            """
            INSERT INTO book_summaries (title, author, year, language, summary, themes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(title) DO UPDATE SET
                author=excluded.author,
                year=excluded.year,
                language=excluded.language,
                summary=excluded.summary,
                themes=excluded.themes;
            """,
            (b["title"], b.get("author"), b.get("year"), b.get("language", "ro"), b["summary"], b.get("themes"))
        )
    conn.commit()

def main():
    path = Path(DB_NAME)
    with sqlite3.connect(path) as conn:
        init_db(conn)
        upsert_books(conn, BOOKS)
    print(f"OK: {len(BOOKS)} cărți inserate/actualizate în {path.resolve()}")
    # Exemplu de interogare:
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT title, substr(summary,1,60)||'…' as preview, themes FROM book_summaries ORDER BY title LIMIT 5;")
        for row in cur.fetchall():
            print(row)

if __name__ == "__main__":
    main()
