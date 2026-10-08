# Digital Twin

An AI chatbot that answers questions about Vania Halim's background, experience, projects and interests in AI, policy and technology. It is embedded on [vaniahalim.github.io](https://vaniahalim.github.io).

Live app: https://huggingface.co/spaces/vaniacrystal/career_conversation

## How it works
- `app.py`: Gradio chat app. It builds a system prompt from the files in `me/`, answers with OpenAI (`gpt-4o-mini`), checks each reply with an evaluator, and logs unanswered questions through a Pushover notification.
- `me/`: the knowledge base (summary, experience, projects, skills, FAQ, voice notes and the resume PDF). Edit these to change what the twin knows.

## Run locally
```
pip install -r requirements.txt
cp .env.example .env   # then add your keys
python app.py
```
Required environment variables: `OPENAI_API_KEY`. Optional: `PUSHOVER_TOKEN`, `PUSHOVER_USER`.

## Deploying
This repo is the source of truth. Every push to `main` runs `.github/workflows/deploy-space.yml`, which publishes `app.py`, `requirements.txt` and `me/` to the Hugging Face Space. Edit here, not on Hugging Face (edits made on the Space are overwritten on the next deploy).
