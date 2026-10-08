from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import re
import requests
from pathlib import Path
from pypdf import PdfReader
from pydantic import BaseModel
import gradio as gr


load_dotenv(override=True)

ME_DIR = Path(__file__).parent / "me"
MAX_EVAL_RETRIES = 1
WELCOME_MESSAGE = (
    "I'm Vania's Digital Twin. Ask me about anything professional on my resume, "
    "LinkedIn, experience, projects, or skills!"
)
CONTACT_INFO = {
    "email": "vanialim12@gmail.com",
    "linkedin": "https://www.linkedin.com/in/vania-halim/",
    "portfolio": "https://vaniahalim.github.io",
    "github": "https://github.com/vaniahalim",
    "location": "Zurich, Switzerland",
    "digital_twin": "https://huggingface.co/spaces/vaniacrystal/career_conversation",
}
FALLBACK_REPLY = (
    "I want to answer accurately, but I'm not confident my last response met my quality bar. "
    "Please try rephrasing your question, or reach Vania directly at vanialim12@gmail.com "
    "or https://www.linkedin.com/in/vania-halim/."
)


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        },
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""):
        return {"recorded": "error", "message": "Please provide a valid email address."}
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Unknown question: {question}")
    return {"recorded": "ok"}


def get_contact_info():
    return CONTACT_INFO


record_user_details_json = {
    "name": "record_user_details",
    "description": "Record when a visitor wants to stay in touch and provides a valid email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The visitor's email address",
            },
            "name": {
                "type": "string",
                "description": "The visitor's name, if provided",
            },
            "notes": {
                "type": "string",
                "description": "Brief context from the conversation worth saving",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Record any professional question you cannot answer from the provided materials",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that could not be answered",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

get_contact_info_json = {
    "name": "get_contact_info",
    "description": "Return Vania's official contact links when someone asks how to reach her",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
    {"type": "function", "function": get_contact_info_json},
]


def load_text_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def load_linkedin_pdf(path: Path) -> str:
    if not path.exists():
        return ""
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text.strip()


def load_knowledge_base() -> dict[str, str]:
    return {
        "summary": load_text_file(ME_DIR / "summary.txt"),
        "experience": load_text_file(ME_DIR / "experience.md"),
        "projects": load_text_file(ME_DIR / "projects.md"),
        "skills": load_text_file(ME_DIR / "skills.md"),
        "faq": load_text_file(ME_DIR / "faq.md"),
        "talking_points": load_text_file(ME_DIR / "talking_points.md"),
        "resume": load_linkedin_pdf(ME_DIR / "resume.pdf"),
    }


def knowledge_base_text(knowledge: dict[str, str]) -> str:
    return f"""### Summary
{knowledge["summary"]}

### Experience
{knowledge["experience"]}

### Projects
{knowledge["projects"]}

### Skills
{knowledge["skills"]}

### FAQ
{knowledge["faq"]}

### Voice & talking points
{knowledge["talking_points"]}

### Resume (extracted, Aug 2026)
{knowledge["resume"]}"""


PORTFOLIO_THEME = (
    gr.themes.Soft(
        primary_hue=gr.themes.colors.rose,
        secondary_hue=gr.themes.colors.purple,
        neutral_hue=gr.themes.colors.gray,
        font=[
            gr.themes.GoogleFont("DM Sans"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif",
        ],
    )
    .set(
        body_background_fill="#FBF7F4",
        background_fill_primary="#FBF7F4",
        background_fill_secondary="#FFFFFF",
        block_background_fill="#FFFFFF",
        block_border_width="1px",
        block_border_color="rgba(45, 42, 38, 0.08)",
        block_radius="16px",
        block_title_text_color="#4A4145",
        body_text_color="#4A4145",
        button_primary_background_fill="#C9929A",
        button_primary_background_fill_hover="#B87F88",
        button_primary_text_color="#FFFFFF",
        button_secondary_background_fill="#F5EDE6",
        button_secondary_text_color="#4A4145",
        link_text_color="#C9929A",
        link_text_color_hover="#9B8AA0",
        color_accent_soft="#F5EDE6",
        input_background_fill="#FFFFFF",
    )
)

GRADIO_CSS = """
.gradio-container {
    font-family: 'DM Sans', sans-serif !important;
    max-width: 960px !important;
    margin: 0 auto !important;
}
h1, .prose h1 {
    font-family: 'Playfair Display', serif !important;
    color: #4A4145 !important;
    font-weight: 600 !important;
}
#description, .prose p {
    color: #7A6F66 !important;
}
.message.bot {
    background: #FFFFFF !important;
    border: 1px solid rgba(45, 42, 38, 0.08) !important;
}
.message.user {
    background: #F5EDE6 !important;
}
footer {
    opacity: 0.6;
}
"""

GRADIO_HEAD = """
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
"""


class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Vania Halim"
        self.knowledge = load_knowledge_base()
        self.knowledge_text = knowledge_base_text(self.knowledge)

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments or "{}")
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def system_prompt(self, extra: str = "") -> str:
        prompt = f"""You are {self.name}'s digital twin on her professional portfolio website.

## Your role
- Speak in first person as Vania's AI representative ("I studied at CMU…").
- Help visitors learn about Vania's background, experience, projects, skills, and interests.
- Audience: recruiters, investors, collaborators, policy peers, and potential clients.

## Rules
- Answer ONLY using the knowledge base below. Do not invent employers, dates, skills, or achievements.
- If information is missing, say you don't have it on record, use record_unknown_question, and offer contact options.
- Stay professional, warm, and concise. Use bullets for long answers.
- Redirect off-topic questions back to professional subjects.
- Do not ask for email on the first message. After a few exchanges, if someone seems interested, invite them to connect via email or LinkedIn and use record_user_details when they share an email.
- When asked how to contact Vania, use get_contact_info.

## Knowledge base
{self.knowledge_text}
"""
        if extra:
            prompt += f"\n{extra}"
        return prompt

    def evaluator_system_prompt(self) -> str:
        return f"""You are a quality evaluator for {self.name}'s digital twin chatbot.

Decide whether the Agent's latest response is acceptable for a public professional portfolio.

Reject the response if it:
- Invents facts not supported by the knowledge base (fake jobs, dates, skills, awards, or projects)
- Uses an unprofessional tone (slang, gimmicks, pig latin, sarcasm, or roleplay)
- Ignores the digital twin framing or speaks as a generic AI assistant
- Claims personal real-time knowledge or actions Vania is doing right now without evidence
- Shares private information not in the knowledge base

Accept the response if it is accurate, professional, grounded in the knowledge base, and appropriately concise.

Knowledge base for fact-checking:
{self.knowledge_text}
"""

    def evaluator_user_prompt(self, reply: str, message: str, history: list) -> str:
        return (
            f"Conversation history:\n{json.dumps(history, indent=2)}\n\n"
            f"Latest user message:\n{message}\n\n"
            f"Latest agent response:\n{reply}\n\n"
            "Evaluate the latest agent response."
        )

    def evaluate(self, reply: str, message: str, history: list) -> Evaluation:
        messages = [
            {"role": "system", "content": self.evaluator_system_prompt()},
            {"role": "user", "content": self.evaluator_user_prompt(reply, message, history)},
        ]
        response = self.openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=Evaluation,
        )
        return response.choices[0].message.parsed

    def generate_reply(self, message: str, history: list, extra_system: str = "") -> str:
        messages = (
            [{"role": "system", "content": self.system_prompt(extra_system)}]
            + history
            + [{"role": "user", "content": message}]
        )
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                results = self.handle_tool_call(assistant_message.tool_calls)
                messages.append(assistant_message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content

    def rerun(self, reply: str, message: str, history: list, feedback: str) -> str:
        extra = (
            "## Previous answer rejected\n"
            "Your previous response failed quality control. Write a better replacement.\n\n"
            f"## Rejected answer:\n{reply}\n\n"
            f"## Reason for rejection:\n{feedback}\n"
        )
        return self.generate_reply(message, history, extra_system=extra)

    def chat(self, message, history):
        reply = self.generate_reply(message, history)

        for attempt in range(MAX_EVAL_RETRIES + 1):
            evaluation = self.evaluate(reply, message, history)
            if evaluation.is_acceptable:
                print("Passed evaluation - returning reply", flush=True)
                return reply

            print(f"Failed evaluation (attempt {attempt + 1}) - {evaluation.feedback}", flush=True)
            if attempt < MAX_EVAL_RETRIES:
                reply = self.rerun(reply, message, history, evaluation.feedback)
            else:
                return FALLBACK_REPLY

        return FALLBACK_REPLY


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(
        me.chat,
        type="messages",
        theme=PORTFOLIO_THEME,
        title="Vania Halim — Digital Twin",
        description=(
            "AI assistant based on Vania's resume, LinkedIn, and portfolio. "
            "Ask about her experience, projects, skills, and interests in AI, policy, and technology. "
            "_For official inquiries, email [vanialim12@gmail.com](mailto:vanialim12@gmail.com)._"
        ),
        examples=[
            "Tell me about your background in AI and policy.",
            "What experience do you have in venture capital?",
            "What projects have you built?",
            "What are you studying at ETH Zurich?",
            "How can I get in touch with you?",
        ],
        css=GRADIO_CSS,
        head=GRADIO_HEAD,
        chatbot=gr.Chatbot(
            value=[{"role": "assistant", "content": WELCOME_MESSAGE}],
            type="messages",
        ),
    ).launch()
