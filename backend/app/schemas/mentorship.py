from typing import Literal

from pydantic import BaseModel, Field


class MentorshipTopic(BaseModel):
    topic_area: str
    learning_objectives: str
    practical_exercise: str


class QuizQuestion(BaseModel):
    prompt: str
    question_type: Literal["mcq"] = "mcq"
    options: list[str] = Field(default_factory=list)
    correct_index: int = 0


class ModuleQuiz(BaseModel):
    enabled: bool = True
    pass_percent: int = Field(default=70, ge=0, le=100)
    award_points: int = Field(default=10, ge=0)
    questions: list[QuizQuestion] = Field(default_factory=list)


class MentorshipModule(BaseModel):
    title: str
    description: str
    reading: str = ""
    topics: list[MentorshipTopic] = Field(default_factory=list)
    quiz: ModuleQuiz = Field(default_factory=ModuleQuiz)


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
