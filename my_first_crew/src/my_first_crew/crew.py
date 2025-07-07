from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# 從 crewai_tools 引入我們需要的所有工具
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

# 建立工具實例
# 注意：這些工具會使用您在 .env 檔案中設定的環境變數
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class MyFirstCrew():
    """MyFirstCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    def __init__(self) -> None:
        self.serper_tool = SerperDevTool()
        self.scrape_tool = ScrapeWebsiteTool()
        # 初始化一個乾淨的檔案寫入工具，不安裝任何預設值

    @agent
    def expert_travel_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['expert_travel_agent'],
            tools=[search_tool], # 這個 Agent 專注於搜尋
            verbose=True
        )

    @agent
    def local_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['local_expert'],
            tools=[search_tool, scrape_tool], # 這個 Agent 同時具備搜尋和讀取網站的能力
            verbose=True
        )

    @agent
    def travel_concierge(self) -> Agent:
        return Agent(
            config=self.agents_config['travel_concierge'],
            verbose=True
        )

    @task
    def identify_flights_and_hotels(self) -> Task:
        return Task(
            config=self.tasks_config['identify_flights_and_hotels'],
            agent=self.expert_travel_agent()
        )

    @task
    def plan_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config['plan_itinerary'],
            agent=self.local_expert(),
            context=[self.identify_flights_and_hotels()]
        )

    @task
    def create_travel_guide(self) -> Task:
        return Task(
            config=self.tasks_config['create_travel_guide'],
            agent=self.travel_concierge(),
            context=[self.plan_itinerary(), self.identify_flights_and_hotels()],
            output_file='output/旅遊手冊.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the MyFirstCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
