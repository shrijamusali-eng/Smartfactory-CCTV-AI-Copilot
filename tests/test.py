from ai.llm import llm_manager

llm = llm_manager.get_fast_llm()

response = llm.invoke("Say hello in one sentence.")

print(response.content)