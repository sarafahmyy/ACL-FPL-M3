from llm_factory import LLMFactory, ModelCatalogue



user_message="who is liverpool's top scorer?"

system_message="""
You are chatbot for Fantasy Premier League that responds to user questions """ \

factory1 = LLMFactory(ModelCatalogue.LLAMA_70B)
factory1.set_system_message(system_message)

#let's assume we retrieved these chunks from the knowledge graph and vectored database
example_chunks=[
          "Ian Rush: 30 goals",
          "Roger Hunt: 28 goals",
          "Mohamed Salah: 32 goals",
          "Gordon Hodgson: 28 goals",
          "Ahmed Ashraf: 75 goals"
          ]

prompt=f""" given the following user question: {user_message}
and the following context chunks from the knowledge base:
{example_chunks}
Provide a concise answer to the user question based on the context chunks.
If the answer is not found in the context, respond with 'I don't know'.
do not fabricate any information or make up answers or respond from your own knowledge."""

response = factory1.send_to_llm(prompt)
print(response)
