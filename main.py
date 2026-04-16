from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent


# LLM
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, )

@tool
def multiply(a: float, b: float) -> float:
    """Умножает два числа"""
    return a * b

@tool
def divide(a: float, b: float) -> float:
    """Делит два числа"""
    return a / b

tools = [multiply, divide]

agent = create_agent(llm, tools, debug=True)

result = agent.invoke(input={"messages": [{"role": "user", "content": "Привет!"}]})

print(result["messages"][-1].content)