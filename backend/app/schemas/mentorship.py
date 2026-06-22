from pydantic import BaseModel, Field


class MentorshipTopic(BaseModel):
    topic_area: str
    learning_objectives: str
    practical_exercise: str


class MentorshipModule(BaseModel):
    title: str
    description: str
    topics: list[MentorshipTopic] = Field(default_factory=list)


class MentorshipStage(BaseModel):
    title: str
    weeks: str
    description: str
    modules: list[MentorshipModule] = Field(default_factory=list)


class MentorshipContent(BaseModel):
    title: str
    subtitle: str = "Floor Plan"
    prepared_for: str = ""
    prepared_by: str = ""
    target_audience: str = ""
    curriculum_source: str = ""
    introduction: str
    stages: list[MentorshipStage] = Field(default_factory=list)
    conclusion: str = ""
    assessment: str = ""
    published: bool = True
