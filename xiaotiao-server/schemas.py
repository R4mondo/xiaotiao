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
    word: str = Field(description="The new vocabulary word")
    definition_zh: str = Field(description="Chinese definition of the word")
    in_sentence: str = Field(description="Example sentence from the article where the word appears")

class TermDef(BaseModel):
    term: str = Field(description="Key term or concept")
    zh: str = Field(description="Chinese translation")
    example: str = Field(description="Example usage or explanation")

class TopicGenerateResponse(BaseModel):
    result_text: str = Field(description="Generated article text in HTML format with <p> tags")
    db_words_used: List[str] = Field(description="List of DB words successfully included in the article")
    new_words: List[NewWord] = Field(description="New domain vocabulary words introduced")
    terms: List[TermDef] = Field(description="Key terms and concepts extracted from the article")
    notes: List[str] = Field(description="Insightful notes about domain expressions or grammar")
    confidence_hint: str = Field(description="Confidence level: high, medium, or low")

# --- Article Lab ---
class ArticleAnalyzeRequest(BaseModel):
    source_text: str
    analysis_mode: str = "plain"  # plain, legal_focus
    grounded: bool = False
    top_k: int = 4

class ParagraphAnalysis(BaseModel):
    original: str = Field(description="Original English paragraph text")
    explanation: str = Field(description="Chinese explanation of the paragraph")

class KeySentence(BaseModel):
    text: str = Field(description="The key English sentence from the text")
    reason: str = Field(description="Why this sentence is important")

class ArticleAnalyzeResponse(BaseModel):
    paragraphs: List[ParagraphAnalysis] = Field(description="Paragraph-by-paragraph analysis")
    terms: List[TermDef] = Field(description="Key terms extracted from the text")
    key_sentences: List[KeySentence] = Field(description="Important sentences with explanations")


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
    style: str = Field(description="Translation style: literal, legal, or plain")
    label: str = Field(description="Chinese label for the translation style, e.g. 直译版")
    text: str = Field(description="The translated text")

class Improvement(BaseModel):
    original: str = Field(description="Original problematic translation part")
    suggested: str = Field(description="Suggested better translation")
    reason: str = Field(description="Why the suggestion is better")

class Critique(BaseModel):
    score: str = Field(description="Score in format like '85 / 100'")
    feedback: str = Field(description="Overall feedback on the user's translation")
    improvements: List[Improvement] = Field(description="Specific improvement suggestions")

class TermSimple(BaseModel):
    term: str = Field(description="The key term")
    definition_zh: str = Field(description="Chinese definition")

class TranslationResponse(BaseModel):
    variants: List[TranslationVariant] = Field(description="Three translation variants: literal, legal, plain")
    terms: List[TermSimple] = Field(description="Key terms extracted")
    notes: List[str] = Field(description="Translation advice and tips")
    common_errors: List[str] = Field(default_factory=list, description="Common translation mistakes to avoid")
    confidence_hint: str = Field(description="Confidence level: high, medium, or low")
    critique: Optional[Critique] = Field(default=None, description="Critique of user's translation attempt, null if not provided")
