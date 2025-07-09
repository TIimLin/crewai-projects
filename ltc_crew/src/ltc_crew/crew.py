import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI

# Uncomment the following line to use an example of a custom tool
# from ltc_crew.tools.custom_tool import MyCustomTool

# Check our tools folder for tools
from ltc_crew.tools.ltc_search_tool import TaiwanLTCProviderSearchTool

@CrewBase
class LtcCrew():
    """LtcCrew crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self) -> None:
        self.google_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            verbose=True,
            temperature=0.1,
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )

    @agent
    def intake_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config['intake_coordinator'],
            verbose=True
        )

    @agent
    def clinical_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config['clinical_assessor'],
            verbose=True
        )

    @agent
    def care_navigator(self) -> Agent:
        return Agent(
            config=self.agents_config['care_navigator'],
            verbose=True
        )

    @agent
    def local_resource_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['local_resource_specialist'],
            tools=[TaiwanLTCProviderSearchTool()],
            verbose=True
        )

    @agent
    def chief_medical_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['chief_medical_advisor'],
            allow_delegation=True,
            verbose=True
        )

    @agent
    def reporting_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_specialist'],
            verbose=True
        )

    @task
    def profile_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['profile_analysis'],
            agent=self.intake_coordinator()
        )

    @task
    def needs_assessment(self) -> Task:
        return Task(
            config=self.tasks_config['needs_assessment'],
            agent=self.clinical_assessor(),
            context=[self.profile_analysis()]
        )

    @task
    def care_recommendation(self) -> Task:
        return Task(
            config=self.tasks_config['care_recommendation'],
            agent=self.care_navigator(),
            context=[self.needs_assessment()]
        )
    
    @task
    def provider_search(self) -> Task:
        return Task(
            config=self.tasks_config['provider_search'],
            agent=self.local_resource_specialist(),
            context=[self.profile_analysis(), self.care_recommendation()]
        )

    @task
    def comprehensive_report(self) -> Task:
        return Task(
            config=self.tasks_config['comprehensive_report'],
            agent=self.reporting_specialist(),
            context=[
                self.profile_analysis(),
                self.needs_assessment(),
                self.care_recommendation(),
                self.provider_search()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LtcCrew crew"""
        worker_agents = [
            self.intake_coordinator(),
            self.clinical_assessor(),
            self.care_navigator(),
            self.local_resource_specialist(),
            self.reporting_specialist()
        ]
        return Crew(
            agents=worker_agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
