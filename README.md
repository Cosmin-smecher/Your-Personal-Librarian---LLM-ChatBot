# Your-Personal-Librarian---LLM-ChatBot
A chatbot that recommends books based on the user’s interests, using RAG over ChromaDB. It responds via OpenAI GPT, can read the recommendation/summary in a specific voice (text-to-speech, TTS), supports Dark/Light/Custom themes, and can generate a representative image for the book.

----------------------------------------------------------------------------------------------------------------
## Features

  -> RAG over ChromaDB (embeddings text-embedding-3-small).
  
  -> Search: free-form semantic; by theme (hint); by title (exact / contains).
  
  -> Automatic title detection: if the query looks like a title → return only that specific book.
  
  -> Answer with GPT + Matches list (sorted by relevance); the first book is the recommendation in the answer.
  
  -> TTS (Text-to-Speech): for the answer and for each book’s summary.
  
  -> Image Generation: original illustration for a book (OpenAI Images, with local fallback).
  
  -> Inappropriate language filter: do not send the prompt to the LLM if offensive language is detected.
  
  -> Dynamic suggestions: pool of 20 suggestions, randomly show 3 on each access.
  
  -> Themes: Dark / Light / Custom palette (colors picked from the sidebar).
  
  -> Chroma collection selector in the sidebar + visible document count (avoid empty collections).
  
----------------------------------------------------------------------------------------------------------------
## Project structure

book_summaries.py                 -----> creating 20+ books having the following characteristics : title, author, year, themes, summary

load_to_chroma_and_search.py      -----> CLI for ingest & test searches

app_streamlit                      -----> main app (Streamlit interface + TTS + Images + Theme + Collection Picker)

tts_utils.py                       -----> TTS helper (OpenAI -> pyttsx3 -> gTTS fallback)

img_gen_utils.py                   -----> Image Generation helper (OpenAI Images -> Pillow fallback)

profanity_filter.py                -----> inappropriate language filter (function is_inappropriate)

.env                              -----> where the OpenAI key is defined (OPENAI_API_KEY)


** If you use a voice mode (STT) variant, include a dedicated app that uses streamlit-mic-recorder.

----------------------------------------------------------------------------------------------------------------
## Installation

Python 3.10+ recommended (create a venv).

1. pip install -U pip
   
2. pip install streamlit chromadb openai python-dotenv pillow
   
3. Offline TTS (fallback):
   pip install pyttsx3
   
5. Optional: voice mode (browser recording)
   
6. pip install streamlit-mic-recorder

On Linux you may need: sudo apt-get install espeak (for pyttsx3).

----------------------------------------------------------------------------------------------------------------
## Configuration (.env)

Create a .env file at the project root:

OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXX

 optional:
 
 OPENAI_ORG=...
 
 OPENAI_BASE=...   -> for Azure OpenAI / compatible proxy

----------------------------------------------------------------------------------------------------------------
## Ingest into Chroma

1) Ingest

python load_to_chroma_and_search.py ingest   --persist ./chroma_book_summaries   --input book_summaries.py

2) Semantic test

python load_to_chroma_and_search.py search   --persist ./chroma_book_summaries   --q "vreau o carte de aventură"

3) Title test

python load_to_chroma_and_search.py search-title   --persist ./chroma_book_summaries   --q "hobbitul 1937"


Note: in metadata, themes must be stored as a string (e.g., ", ".join(themes)), not as a list.
----------------------------------------------------------------------------------------------------------------
## Run the app
-> streamlit run app_streamlit

In the sidebar:

-> choose Chroma persist dir and Collection (also see the number of documents);

-> set Number of recommendations, Search mode, GPT model, TTS voice;

-> for Theme: Dark, Light, or Custom (pick the colors);

-> for image: style + size.

----------------------------------------------------------------------------------------------------------------
## Usage

-> Write a natural request (e.g., “I want a book about friendship and magic”).

-> If the query looks like a title, the system returns only that book (case-insensitive + diacritics-insensitive).

-> See the Answer (GPT) + Matches (order = relevance; first = recommendation).

-> You can listen to the answer or the summary of any book (TTS).

-> You can generate an image for any book (choose style/size in the sidebar).

----------------------------------------------------------------------------------------------------------------
## Customization

-> Dynamic suggestions: edit SUGGESTIONS_POOL in the app.

-> Themes: change colors in theme_custom or adjust the injected CSS.

-> Image prompt: see img_gen_utils._build_prompt(...).

-> Language filter: extend rules/regex in profanity_filter.py.

----------------------------------------------------------------------------------------------------------------
## Troubleshooting

-> “OPENAI_API_KEY is missing” → check .env / environment vars.

-> Collection has (0) documents → run ingest or pick another collection in the selector.

-> “metadata must be primitive” in Chroma → themes in metadata must be a string, not a list.

-> TTS produces no sound → check the connection/API key; fallback to pyttsx3 (offline).

-> Image won’t generate → verify access to OpenAI Images; the Pillow fallback will create a generic PNG.

----------------------------------------------------------------------------------------------------------------
## License / content

-> Generated images are original (do not copy real covers/logos).

-> Summaries are brief and for educational/demonstration use.

----------------------------------------------------------------------------------------------------------------
