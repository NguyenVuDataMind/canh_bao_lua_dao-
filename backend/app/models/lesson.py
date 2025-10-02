from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class LessonStatus(str, enum.Enum):
    DRAFT = "draft"


class QuizMode(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    TRUE_FALSE = "true_false"


class Lesson(Base):
    __tablename__ = "lessons"

    lesson_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    status = Column(Enum(LessonStatus), default=LessonStatus.DRAFT, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    created_by_user = relationship("User", back_populates="lessons")
    lesson_cases = relationship("LessonCase", back_populates="lesson", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")


class LessonCase(Base):
    __tablename__ = "lesson_cases"

    lesson_id = Column(Integer, ForeignKey("lessons.lesson_id"), nullable=False, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, primary_key=True)
    role = Column(String)

    # Relationships
    lesson = relationship("Lesson", back_populates="lesson_cases")
    case = relationship("Case", back_populates="lesson_cases")


class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.lesson_id"), nullable=False)
    title = Column(String)
    mode = Column(Enum(QuizMode))

    # Relationships
    lesson = relationship("Lesson", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    question_id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.quiz_id"), nullable=False)
    order_no = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")


class QuizOption(Base):
    __tablename__ = "quiz_options"

    option_id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.question_id"), nullable=False)
    order_no = Column(Integer, nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Integer, default=0, nullable=False)

    # Relationships
    question = relationship("QuizQuestion", back_populates="options")


class Dataset(Base):
    __tablename__ = "datasets"

    dataset_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    split = Column(String, nullable=False)
    input_ref = Column(String)
    target_ref = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text)

    # Relationships
    case = relationship("Case", back_populates="datasets")
