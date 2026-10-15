import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from langchain_community.tools import DuckDuckGoSearchRun
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from pydantic import Field

# rp-demo: console logging only, opt-in via CREW_LOG=1 (off by default).
# No file logging -> safe for the read-only AgentCore runtime container.
# When enabled, console output is captured by AgentCore and shipped to CloudWatch.
_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
logger = logging.getLogger("research_crew")
if os.environ.get("CREW_LOG") == "1":
    logging.basicConfig(
        level=logging.INFO,
        format=_LOG_FORMAT,
        handlers=[logging.StreamHandler()],
    )
else:
    logger.addHandler(logging.NullHandler())


class SearchTool(BaseTool):
     name: str = "Search"
     description: str = "Useful for searching the web for information."
     search: DuckDuckGoSearchRun = Field(default_factory=DuckDuckGoSearchRun)

     def _run(self, query: str) -> str:
         """Execute the search query and return results"""
         logger.info("SearchTool query: %s", query)
         try:
             return self.search.invoke(query)
         except Exception as e:
             logger.exception("SearchTool failed for query: %s", query)
             return f"Error performing search: {str(e)}"

@CrewBase
class ResearchCrew():
    """Research crew for comprehensive topic analysis and reporting"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            verbose=True,
            tools=[
                #SerperDevTool()
                SearchTool()
                ]
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'], # type: ignore[index]
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'] # type: ignore[index]
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'], # type: ignore[index]
            #output_file='output/report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        logger.info("Building research crew (agents=%d, tasks=%d)", len(self.agents), len(self.tasks))
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
