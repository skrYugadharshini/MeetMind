import os
from meetmind_core import MeetMind

mm = MeetMind(os.getenv("GROQ_API_KEY"))

with open("sample_meeting.mp3", "rb") as f:
    mm.transcribe("sample_meeting.mp3", f.read(), hints="Priya, Kevin, Nimal")
print(f"✅ Transcribed: {len(mm.segments)} segments\n")

result = mm.analyze()
notes = result["notes"]

print("📋 SUMMARY\n", notes["summary"])
print("\n🎯 DECISIONS")
for d in notes["decisions"]:
    print(" -", d)
print("\n✅ ACTION ITEMS")
for a in notes["action_items"]:
    print(f" - {a['owner']}: {a['task']} (due: {a['due']}) [{a['timestamp']}]")
print(f"\n🔍 Checker passes: {result['attempts']} | issues left: {result['issues']}")
print("\n📧 EMAIL\n", result["email"])