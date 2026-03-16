from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

# --- Topic Explorer ---
class TopicGenerateRequest(BaseModel):
    topics: List[str]
    domains: List[str]
    level: str = "intermediate"
    article_style_id: str = "economist"
    article_length: int = 400
    db_word_count: int = 8
    new_word_count: int = 5
    target_range_id: str = "cet6"
    db_words: List[str] = Field(default_factory=list)

class NewWord(BaseModel):
    word: str
    definition_zh: str
    in_sentence: str

class TermDef(BaseModel):
    term: str
    zh: str
    example: str

class TopicGenerateResponse(BaseModel):
    result_text: str
    db_words_used: List[str]
    new_words: List[NewWord]
    terms: List[TermDef]
    notes: List[str]
    confidence_hint: str

# --- Article Lab ---
class ArticleAnalyzeRequest(BaseModel):
    source_text: str
    analysis_mode: str = "plain"  # plain, legal_focus
    grounded: bool = False
    top_k: int = 4

class ParagraphAnalysis(BaseModel):
    original: str
    explanation: str

class KeySentence(BaseModel):
    text: str
    reason: str

class ArticleAnalyzeResponse(BaseModel):
    paragraphs: List[ParagraphAnalysis]
    terms: List[TermDef]
    key_sentences: List[KeySentence]


class RagIngestRequest(BaseModel):
    source_id: str
    source_type: str = "custom"
    title: str
    source_url: Optional[str] = None
    content: str
    metadata: dict = Field(default_factory=dict)


class RagQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RagCitation(BaseModel):
    id: str
    title: str
    url: str = ""


class RagQueryResponse(BaseModel):
    answer: str
    citations: List[RagCitation]
    chunks: List[str]

# --- Translation Studio ---
class TranslationRequest(BaseModel):
    source_text: str
    direction: str = "zh_to_en" # zh_to_en, en_to_zh
    style: List[str] = Field(default_factory=lambda: ["literal", "legal", "plain"])
    user_translation: Optional[str] = ""

class TranslationVariant(BaseModel):
    style: str
    label: str
    text: str

class Improvement(BaseModel):
    original: str
    suggested: str
    reason: str

class Critique(BaseModel):
    score: str
    feedback: str
    improvements: List[Improvement]

class TermSimple(BaseModel):
    term: str
    definition_zh: str

class TranslationResponse(BaseModel):
    variants: List[TranslationVariant]
    terms: List[TermSimple]
    notes: List[str]
    common_errors: List[str] = Field(default_factory=list)
    confidence_hint: str
    critique: Optional[Critique] = None
