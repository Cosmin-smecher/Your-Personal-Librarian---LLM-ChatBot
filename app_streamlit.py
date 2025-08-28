#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Book RAG Chatbot — Voice + TTS + Image Gen (v5, Theming)
- Temă completă: Dark / Light / Custom (paletă de culori)
- Sugestii dinamice (3 din 20)
- Reordonare potriviri: prima = recomandarea din răspuns
- TTS (răspuns + rezumate) & Image Gen
"""
import os, re, difflib, unicodedata
from pathlib import Path
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from tts_utils import tts_bytes
from img_gen_utils import generate_book_image
from profanity_filter import is_inappropriate

# -------------------- Page Config --------------------
st.set_page_config(page_title="Your Personal Librarian", page_icon="🎨", layout="centered")

# Init session_state
defaults = {
    "results": None,
    "query_inp": "",
    "ui_suggestions": None,
    "theme_choice": "Dark",
    "theme_custom": {
        "primary": "#6C63FF",
        "accent": "#2EC4B6",
        "bg": "#0f1216",
        "card": "#171a1f",
        "text": "#e5e7eb",
        "subtext": "#9ca3af",
        "bar_bg": "#2a2f3a",
    }
}
for k,v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------- Sidebar (settings) --------------------
with st.sidebar:
    st.subheader("⚙️ Setări")
    theme = st.radio("Temă", ["Dark", "Light", "Custom"], index=["Dark","Light","Custom"].index(st.session_state["theme_choice"]), horizontal=True)
    st.session_state["theme_choice"] = theme

    # Custom palette controls
    if theme == "Custom":
        st.caption("Alege-ți paleta de culori:")
        c = st.session_state["theme_custom"]
        colA, colB = st.columns(2)
        c["primary"] = colA.color_picker("Primary", c["primary"])
        c["accent"]  = colB.color_picker("Accent",  c["accent"])
        c["bg"]      = colA.color_picker("Background", c["bg"])
        c["card"]    = colB.color_picker("Card", c["card"])
        c["text"]    = colA.color_picker("Text", c["text"])
        c["subtext"] = colB.color_picker("Subtext", c["subtext"])
        c["bar_bg"]  = st.color_picker("Bars / Inputs BG", c["bar_bg"])
        st.session_state["theme_custom"] = c
        st.markdown("<hr/>", unsafe_allow_html=True)

    persist = Path(st.text_input("Chroma persist dir", "./chroma_book_summaries"))
    k = st.slider("Numarul de recomandari afisate", 1, 50, 5)
    show_all = st.checkbox("Afișează toate potrivirile (semantic)", value=False)
    search_mode = st.radio("Mod căutare", ["Context liber", "După temă (hint)", "Titlu (exact)", "Titlu (conține)"], index=0)
    model = st.selectbox("Model GPT", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"], index=0)
    tts_voice = st.selectbox("Voce TTS", ["alloy", "verse", "aria", "ballad"], index=0)
    auto_title = st.checkbox("🔎 Detectează automat căutările de titlu", value=True)
    st.markdown("<hr/>", unsafe_allow_html=True)
    st.subheader("🖼️ Generare imagine")
    img_style = st.selectbox("Stil", ["copertă minimală", "scenă cinematică", "ilustrație acquarela", "poster vintage"], index=0)
    img_size = st.selectbox("Dimensiune", ["1024x1024", "1024x1536", "1536x1024", "512x512"], index=0)
    st.caption("💡 Poți întreba natural; poți genera audio și imagini pentru rezultat.")

# -------------------- Theming (CSS) --------------------
def _theme_tokens(theme:str):
    if theme == "Dark":
        return dict(primary="#6C63FF", accent="#2EC4B6", bg="#0f1216", card="#171a1f",
                    text="#e5e7eb", subtext="#9ca3af", bar_bg="#2a2f3a")
    if theme == "Light":
        return dict(primary="#4F46E5", accent="#14B8A6", bg="#f6f7fb", card="#ffffff",
                    text="#111827", subtext="#6b7280", bar_bg="#e6e8ef")
    # Custom
    return st.session_state["theme_custom"]

TOK = _theme_tokens(theme)

st.markdown(f"""
<style>
:root {{
  --bg: {TOK['bg']};
  --card: {TOK['card']};
  --text: {TOK['text']};
  --subtext: {TOK['subtext']};
  --primary: {TOK['primary']};
  --accent: {TOK['accent']};
  --barbg: {TOK['bar_bg']};
}}
/* Page + Sidebar backgrounds */
[data-testid="stAppViewContainer"], body {{
  background: var(--bg) !important; color: var(--text) !important;
}}
section[data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
  background: var(--bg) !important; color: var(--text) !important;
}}
/* Remove default header bg */
header[data-testid="stHeader"] {{ background: transparent; }}
/* General text */
html, body, [data-testid="stAppViewContainer"] {{ color: var(--text); }}

/* Inputs */
input, textarea, .stTextInput>div>div, .stTextArea>div>div, .stSelectbox>div, .stNumberInput>div {{
  background: var(--card) !important; color: var(--text) !important; border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
}}
/* Buttons */
.stButton>button {{
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: white !important; border: 0 !important; border-radius: 12px !important;
  padding: 0.6rem 1rem; font-weight: 600;
}}
/* Cards */
.card {{
  background: var(--card); border-radius:16px; padding:14px 16px;
  border:1px solid rgba(0,0,0,.06); box-shadow:0 6px 18px rgba(0,0,0,.06); margin-bottom:10px;
}}
/* Badges */
.badge {{
  display:inline-block; padding:4px 10px; margin:2px; border-radius:999px;
  background: var(--accent); color:white; font-weight:600; font-size:.8rem;
}}
/* Bars */
.scorebar {{ height:10px; width:100%; background: var(--barbg); border-radius:999px; box-shadow: inset 0 0 6px rgba(0,0,0,.25); }}
.scorebar > div {{ height:100%; border-radius:999px; background: linear-gradient(90deg, var(--primary), var(--accent)); }}

/* Header block */
.app-header {{
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 60%);
  padding:20px 28px; border-radius:18px; color:white; box-shadow:0 6px 20px rgba(0,0,0,.15);
}}
.small {{ opacity:.9; font-size:.92rem; }}
.sep {{ height:1px; background:linear-gradient(90deg, transparent, rgba(255,255,255,.25), transparent); margin:10px 0 6px; border-radius:1px; }}
.footer-note {{ color: var(--subtext); font-size:.85rem; }}
.reco-badge {{ display:inline-block; margin-left:8px; padding:2px 8px; background:#22c55e; color:white; border-radius:999px; font-size:.75rem; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
  <h1 style="margin-bottom:6px;">Your personal librarian.</h1>
  <div class="small">Cauta orice carte , iar asistentul inteligent iti va oferi detalii despre aceasta!</div>
</div>
""", unsafe_allow_html=True)

# -------------------- Chroma helpers --------------------
def get_collection(persist_dir: Path, collection_name: str = "books"):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY lipsește. Adaugă-l în .env sau în variabilele de mediu.")
        st.stop()
    client = chromadb.PersistentClient(path=str(persist_dir))
    embedder = embedding_functions.OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-3-small")
    return client.get_or_create_collection(name=collection_name, embedding_function=embedder)

def _normalize(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[\W_]+", " ", s)
    return " ".join(s.split())

def _best_title_index(norm_q: str, titles_norm: list[str]) -> int | None:
    if not norm_q: return None
    if norm_q in titles_norm: return titles_norm.index(norm_q)
    best_idx, best_score = None, 0.0
    for i, t in enumerate(titles_norm):
        ratio = difflib.SequenceMatcher(None, norm_q, t).ratio()
        bonus = (0.25 if norm_q in t else 0.0) + (0.15 if t.startswith(norm_q) else 0.0)
        gap = abs(len(t) - len(norm_q)); penalty = min(0.25, gap * 0.005)
        score = ratio + bonus - penalty
        if score > best_score: best_idx, best_score = i, score
    return best_idx if (best_idx is not None and best_score >= 0.60) else None

def _build_item_from_meta_doc(_id, meta, doc, dist=None):
    themes_val = meta.get("themes", "")
    themes_str = ", ".join(themes_val) if isinstance(themes_val, list) else str(themes_val)
    score = max(0.0, 1.0 - float(dist)) if dist is not None else 1.0
    return {
        "id": _id, "title": meta.get("title"), "author": meta.get("author"), "year": meta.get("year"),
        "themes": themes_str, "summary": doc.split("Rezumat:", 1)[-1].strip() if isinstance(doc, str) else "", "score": score,
    }

def retrieve_semantic(query: str, k: int, persist_dir: Path, show_all: bool):
    col = get_collection(persist_dir)
    if show_all: k = int(col.count())
    res = col.query(query_texts=[query], n_results=k, include=["documents","metadatas","distances"])
    items: List[Dict] = []
    for _id, doc, meta, dist in zip(res.get("ids", [[]])[0], res.get("documents", [[]])[0], res.get("metadatas", [[]])[0], res.get("distances", [[]])[0]):
        items.append(_build_item_from_meta_doc(_id, meta, doc, dist))
    return items

def retrieve_title_exact(title: str, persist_dir: Path):
    tnorm = _normalize(title); col = get_collection(persist_dir)
    try:
        data = col.get(where={"title": title}, include=["metadatas","documents"])
        out = []
        for _id, meta, doc in zip(data.get("ids", []), data.get("metadatas", []), data.get("documents", [])):
            if _normalize(meta.get("title")) == tnorm:
                out.append(_build_item_from_meta_doc(_id, meta, doc))
        if out: return out
    except Exception: pass
    data = col.get(limit=int(col.count()), include=["metadatas","documents"])
    return [_build_item_from_meta_doc(_id, meta, doc) for _id, meta, doc in zip(data["ids"], data["metadatas"], data["documents"]) if _normalize(meta.get("title")) == tnorm]

def retrieve_title_contains(title_substring: str, persist_dir: Path):
    sub = _normalize(title_substring); col = get_collection(persist_dir)
    data = col.get(limit=int(col.count()), include=["metadatas","documents"])
    return [_build_item_from_meta_doc(_id, meta, doc) for _id, meta, doc in zip(data["ids"], data["metadatas"], data["documents"]) if sub in _normalize(meta.get("title"))]

def llm_recommend(user_query: str, retrieved: List[Dict], model: str = "gpt-4o-mini") -> str:
    client = OpenAI()
    ctx = "\n".join([f"[Cand#{i}] Titlu:{it['title']} | Autor:{it['author']} | An:{it['year']} | Teme:{it['themes']}\nRezumat:{it['summary']}" for i,it in enumerate(retrieved,1)]) or "Nicio potrivire."
    system = ("Ești un asistent pentru recomandări de cărți. Răspunde în română, clar și prietenos. "
              "Fă recomandări NUMAI folosind candidații furnizați. "
              "Dacă alegi o carte anume, menționeaz-o clar și EXACT cu titlul ei în text.")
    msg = client.chat.completions.create(model=model, temperature=0.35, messages=[{"role":"system","content":system},{"role":"user","content":f"Cererea: {user_query}\n\nCandidați:\n{ctx}"}])
    return msg.choices[0].message.content

def _extract_recommended_title(answer: str, items: List[Dict]) -> int | None:
    """Returnează indexul item-ului al cărui titlu apare în answer (fuzzy, fără diacritice)."""
    if not answer or not items:
        return None
    ans_norm = _normalize(answer)
    best_idx, best_len = None, 0
    for i, it in enumerate(items):
        t = _normalize(it.get("title", ""))
        if t and t in ans_norm and len(t) > best_len:
            best_idx, best_len = i, len(t)
    return best_idx

# -------------------- Dynamic suggestions --------------------
st.markdown("##### Încearcă un exemplu:")
import random
SUGGESTIONS_POOL = [
    "Vreau o carte despre prietenie și magie",
    "Caut o poveste SF cu explorare spațială",
    "Recomandă-mi un thriller psihologic intens",
    "Vreau o carte scurtă și amuzantă",
    "Caut o carte clasică despre dragoste",
    "Vreau o aventură epică cu lumi fantastice",
    "O carte despre război și strategie",
    "Ceva motivațional și de dezvoltare personală",
    "Biografie a unui inovator faimos",
    "Mister într-un orășel liniștit",
    "Distopie despre controlul societății",
    "Roman istoric despre Roma antică",
    "Cartea perfectă pentru adolescenți",
    "Nonficțiune despre știință ușor de înțeles",
    "Romance contemporan cu umor",
    "O carte cu dezbateri etice și filozofie",
    "Poveste cu prietenie între animale",
    "Fantasy cu dragoni și magie întunecată",
    "Cyberpunk cu inteligență artificială",
    "Cărți care seamănă cu Hobbitul",
]
if st.session_state["ui_suggestions"] is None:
    st.session_state["ui_suggestions"] = random.sample(SUGGESTIONS_POOL, 3)
cols = st.columns(3)
for c, p in zip(cols, st.session_state["ui_suggestions"]):
    if c.button("✨ " + p, use_container_width=True):
        st.session_state["query_inp"] = p

# -------------------- Query form --------------------
query_default = st.session_state.get("query_inp", "")
with st.form("search_form", clear_on_submit=False):
    user_query = st.text_input("Caută o carte:", value=query_default, placeholder="Ex: Hobbitul 1937 / Vreau o carte de aventură")
    do_search = st.form_submit_button("🔎 Caută și recomandă")

# -------------------- Compute --------------------
def compute_results(user_q: str) -> Dict:
    blocked, _ = is_inappropriate(user_q)
    if blocked:
        return {"blocked": True, "msg": "Hai să păstrăm conversația prietenoasă 😊. Te rog reformulează fără limbaj ofensator."}
    if search_mode in ["Context liber", "După temă (hint)"]:
        if auto_title:
            norm_q = _normalize(user_q)
            col = get_collection(persist)
            data = col.get(include=["metadatas","documents"], limit=int(col.count()))
            titles = [m.get("title") for m in data.get("metadatas", [])]
            idx = _best_title_index(norm_q, [_normalize(t) for t in titles])
            if idx is not None:
                items = [_build_item_from_meta_doc(data["ids"][idx], data["metadatas"][idx], data["documents"][idx])]
            else:
                q = user_q if search_mode == "Context liber" else f"cărți cu tema {user_q}; recomandări pe această temă"
                items = retrieve_semantic(q, k, persist, show_all=show_all)
        else:
            q = user_q if search_mode == "Context liber" else f"cărți cu tema {user_q}; recomandări pe această temă"
            items = retrieve_semantic(q, k, persist, show_all=show_all)
    elif search_mode == "Titlu (exact)":
        exact = retrieve_title_exact(user_q, persist); items = exact[:1] if exact else []
    else:
        items = retrieve_title_contains(user_q, persist)
    answer = llm_recommend(user_q, items, model=model)
    idx = _extract_recommended_title(answer, items)
    if idx is not None and idx != 0:
        items = [items[idx]] + items[:idx] + items[idx+1:]
    return {"blocked": False, "items": items, "answer": answer, "query": user_q}

if do_search and user_query.strip():
    with st.spinner("🔍 Caut potriviri din colecție..."):
        st.session_state["results"] = compute_results(user_query)
    st.rerun()

# -------------------- Render --------------------
st.markdown("""
<div class="app-header" style="margin-top:14px;">
  <div class="small">Rezultate</div>
</div>
""", unsafe_allow_html=True)

res = st.session_state.get("results")
if res:
    if res.get("blocked"):
        st.warning(res["msg"])
    else:
        st.markdown("### Răspuns")
        st.success(res["answer"])
        if st.button("🔊 Ascultă răspunsul", key="tts-answer", use_container_width=True):
            audio, mime = tts_bytes(res["answer"], voice=tts_voice)
            if audio: st.audio(audio, format=mime)
            else: st.warning("Nu am putut genera audio.")
        st.markdown('<div class="sep"></div>', unsafe_allow_html=True)

        st.markdown("### Potriviri")
        st.caption("Prima carte este recomandarea principală; apoi continuă potrivirile după relevanță.")
        items = res.get("items", [])
        if not items:
            st.info("Nu am găsit potriviri. Verifică ortografia sau încearcă alt mod de căutare.")
        else:
            for j, it in enumerate(items):
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    reco = " <span class='reco-badge'>Recomandare</span>" if j == 0 else ""
                    st.markdown(f"**{it['title']}** — { it['author']} {reco}  \n*({it['year']})*", unsafe_allow_html=True)
                    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="scorebar"><div style="width:{int(it["score"]*100)}%"></div></div>', unsafe_allow_html=True)
                    badges = "".join([f'<span class="badge">{t.strip()}</span>' for t in it["themes"].split(",") if t.strip()])
                    if badges: st.markdown(badges, unsafe_allow_html=True)

                    with st.expander("Rezumat"):
                        st.write(it["summary"])
                        if st.button("🔊 Citește rezumatul", key=f"tts-sum-{it['id']}"):
                            audio, mime = tts_bytes(it["summary"], voice=tts_voice)
                            if audio: st.audio(audio, format=mime)
                            else: st.warning("Nu am putut genera audio pentru rezumat.")

                    if st.button("🖼️ Generează imagine", key=f"gen-img-{it['id']}"):
                        with st.spinner("Generez imaginea..."):
                            img_bytes, mime, used_prompt = generate_book_image(
                                title=it["title"], author=it["author"], themes=it["themes"], summary=it["summary"],
                                style=img_style, size=img_size
                            )
                        if img_bytes:
                            st.image(img_bytes, caption=f"Imagine generată pentru „{it['title']}” ({img_style})")
                            def _slug(s):
                                import re
                                return re.sub(r"[^a-z0-9]+","-", (s or '').lower()).strip("-") or "imagine-carte"
                            st.download_button("⬇️ Descarcă PNG", data=img_bytes, file_name=f"{_slug(it['title'])}.png", mime=mime)
                        else:
                            st.warning("Nu am putut genera imaginea. Verifică OPENAI_API_KEY sau încearcă alt stil.")
                    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br/><div class='footer-note'>RAG: ChromaDB + OpenAI · TTS · Image Gen · Custom Theme</div>", unsafe_allow_html=True)
