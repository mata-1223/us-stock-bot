import os
from crewai import Agent, Task, Crew, Process, LLM  # [수정] LLM 클래스 추가
from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

load_dotenv()

# --- 1. Ollama LLM 설정 (여기가 핵심!) ---
# 문자열 대신 명시적인 객체를 만듭니다.
# base_url은 Ollama 기본 주소입니다.
my_llm = LLM(
    model="ollama/llama3",
    base_url="http://localhost:11434"
)

# --- 2. 도구(Tool) 설정 ---
class SearchTool(BaseTool):
    name: str = "Internet Search"
    description: str = "최신 주식 뉴스와 정보를 인터넷에서 검색합니다."

    def _run(self, query: str) -> str:
        search = DuckDuckGoSearchRun()
        return search.run(query)

search_tool = SearchTool()

# --- 3. 요원(Agent) 채용 ---

# 리서치 담당
researcher = Agent(
    role='Stock Market Researcher',
    goal='최신 주식 뉴스를 검색하여 핵심 정보를 수집한다',
    backstory='당신은 월스트리트에서 가장 정보력이 빠른 리서치 전문가입니다.',
    verbose=True,
    allow_delegation=False,
    tools=[search_tool], 
    llm=my_llm  # [수정] 문자열 대신 객체 전달
)

# 분석 담당
writer = Agent(
    role='Stock Analyst Writer',
    goal='수집된 정보를 바탕으로 한국어 투자 보고서를 작성한다',
    backstory='당신은 복잡한 금융 정보를 쉽게 설명하는 베스트셀러 작가입니다.',
    verbose=True,
    allow_delegation=False,
    llm=my_llm  # [수정] 문자열 대신 객체 전달
)

# --- 4. 임무(Task) 하달 ---

task1 = Task(
    description='애플(AAPL)의 2024년, 2025년 최신 혁신 제품이나 뉴스 3가지를 검색하세요.',
    agent=researcher,
    expected_output='주요 뉴스 3가지 요약 리스트'
)

task2 = Task(
    description='위에서 조사한 내용을 바탕으로, 애플 주가에 미칠 영향을 분석하는 짧은 한국어 블로그 글을 쓰세요.',
    agent=writer,
    expected_output='3문단 이내의 한국어 블로그 포스팅',
    context=[task1]
)=

# --- 5. 팀(Crew) 결성 및 실행 ---

stock_crew = Crew(
    agents=[researcher, writer],
    tasks=[task1, task2],
    process=Process.sequential,
    verbose=True
)

print("🚀 CrewAI 팀 출동!")
result = stock_crew.kickoff()

print("\n\n########################")
print("## 최종 결과물 (Result) ##")
print("########################\n")
print(result)