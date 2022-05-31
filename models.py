from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Use(str, Enum):
    admission_test = "Test de positionnement"
    validation_test = "Test de validation"
    total_bootcamp = "Total Bootcamp"


class Subject(str, Enum):
    database = "BDD"
    distributed_systems = "Systèmes distribués"
    streaming = "Streaming de données"
    docker = "Docker"
    classification = "Classification"
    data_science = "Data Science"
    machine_learning = "Machine Learning"
    automation = "Automation"


class Question(BaseModel):
    question: str
    subject: Optional[Subject]
    use: Optional[Use]
    correct: Optional[str]
    responseA: str
    responseB: str
    responseC: Optional[str]
    responseD: Optional[str]
    remark: Optional[str]
