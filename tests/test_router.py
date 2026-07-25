from ai.intent_router import IntentRouter

router = IntentRouter()

questions = [
    "How many incidents happened today?",
    "Show latest helmet violations",
    "Explain repeated PPE violations",
    "What is PPE?",
]

for q in questions:
    print(q)
    print(router.route(q))
    print("-" * 40)