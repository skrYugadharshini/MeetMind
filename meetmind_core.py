"""MeetMind core: the AI brain of the app."""
import json
from typing import List, Optional, TypedDict

from groq import Groq
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

LLM_MODEL = "openai/gpt-oss-120b"
WHISPER_MODEL = "whisper-large-v3"


def fmt(seconds):
    """Turn 75.3 seconds into '01:15'."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


# 🆕 The "forms" the AI must fill in
class ActionItem(BaseModel):
    owner: str
    task: str
    due: Optional[str] = None
    timestamp: Optional[str] = None


class MeetingNotes(BaseModel):
    summary: str
    decisions: List[str]
    action_items: List[ActionItem]


# 🆕 The shared memory all agents read and write
class State(TypedDict):
    transcript: str
    notes: dict
    issues: List[str]
    attempts: int
    email: str


class MeetMind:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = LLM_MODEL
        self.segments = []
        self.transcript = ""
        self.graph = self._build_graph()   # 🆕 build the agents once

    # ---------- Whisper ----------
    def transcribe(self, filename, audio_bytes, hints=""):
        """Send audio to Whisper and store the timestamped transcript."""
        options = dict(
            file=(filename, audio_bytes),
            model=WHISPER_MODEL,
            response_format="verbose_json",
        )
        if hints.strip():
            options["prompt"] = hints.strip()

        result = self.client.audio.transcriptions.create(**options)

        self.segments = [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in result.segments
        ]
        self.transcript = "\n".join(
            f"[{fmt(s['start'])}] {s['text']}" for s in self.segments
        )
        return self.transcript

    # 🆕 ---------- LLM helper ----------
    def llm(self, prompt, temp=0, json_mode=False):
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,
            response_format={"type": "json_object"} if json_mode else None,
        )
        return r.choices[0].message.content

    # 🆕 ---------- Agent 1: notes ----------
    def _notes_agent(self, state):
        feedback = ""
        if state["issues"]:
            feedback = "\nFix these problems from your last attempt:\n- " + "\n- ".join(state["issues"])
        prompt = f"""You are a meeting assistant. Return ONLY JSON with:
"summary" (3-5 sentences), "decisions" (list), "action_items" (list of {{"owner","task","due","timestamp"}}).
Rules:
- When explaining why something changed, give the main cause that forced it, not side benefits.
- "decisions" = only what the team agreed or approved. Do NOT repeat tasks there.
- Only include a due date if it is explicitly stated for that person's task, otherwise null.
- Include tasks people assign to themselves. "I'll do X" belongs to the person speaking.
- "timestamp" must be MM:SS only, with no brackets.{feedback}

Transcript:
{state['transcript']}"""
        notes = MeetingNotes.model_validate_json(self.llm(prompt, json_mode=True))
        return {"notes": notes.model_dump(), "attempts": state["attempts"] + 1}

    # 🆕 ---------- Agent 2: checker ----------
    def _checker_agent(self, state):
        prompt = f"""You are a strict reviewer. Compare the meeting notes with the transcript.
Check the summary (correct causes?), decisions (missing? tasks listed as decisions?)
and action items (wrong owner, invented due dates, missing tasks?).
Return ONLY JSON: {{"issues": ["..."]}} (empty list if everything is correct).

Notes: {json.dumps(state['notes'])}

Transcript:
{state['transcript']}"""
        issues = json.loads(self.llm(prompt, json_mode=True)).get("issues", [])
        return {"issues": issues}

    # 🆕 ---------- Agent 3: email ----------
    def _email_agent(self, state):
        prompt = f"""Write a short professional follow-up email (under 150 words) with a subject line,
key decisions and each person's action items. Only mention due dates that appear in the notes;
never invent deadlines like "ASAP".

Notes: {json.dumps(state['notes'])}"""
        return {"email": self.llm(prompt, temp=0.3)}

    # 🆕 ---------- Loop back or finish? ----------
    @staticmethod
    def _route(state):
        if state["issues"] and state["attempts"] < 2:
            return "fix"
        return "done"

    # 🆕 ---------- Connect the agents ----------
    def _build_graph(self):
        g = StateGraph(State)
        g.add_node("notes", self._notes_agent)
        g.add_node("checker", self._checker_agent)
        g.add_node("email", self._email_agent)
        g.set_entry_point("notes")
        g.add_edge("notes", "checker")
        g.add_conditional_edges("checker", self._route, {"fix": "notes", "done": "email"})
        g.add_edge("email", END)
        return g.compile()

    # 🆕 ---------- One button to run everything ----------
    def analyze(self):
        return self.graph.invoke({
            "transcript": self.transcript,
            "notes": {}, "issues": [], "attempts": 0, "email": "",
        })

        # ---------- Chat with the meeting ----------
    def ask(self, question):
        prompt = f"""Answer the question using ONLY the meeting transcript below.
If asked "why", give the main cause that forced the decision, not side benefits.
Mention the timestamp where it was said, like (at 01:15).
If the answer is not in the transcript, say "This wasn't discussed in the meeting."

Transcript:
{self.transcript}

Question: {question}"""
        return self.llm(prompt)