"""
Prompt Template Engine — Jinja2 模板 + JSON Schema 约束 + Pydantic 校验

后端维护人员通过编辑 prompts/*.j2 文件来定义 AI 生成的标准化模版。
前端用户通过 UI 选项注入模板变量，最终生成标准化、高质量的内容。
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple, Type

from jinja2 import Environment, FileSystemLoader, Undefined
from pydantic import BaseModel


# Prompt 文件目录
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


def _strip_optional_wrapper(schema: dict) -> dict:
    """Remove Pydantic v2 anyOf wrappers for Optional fields so that LLM
    providers that don't understand 'anyOf' still get a clean schema."""
    if not isinstance(schema, dict):
        return schema

    # Process $defs
    defs = schema.get("$defs", {})
    for key in defs:
        defs[key] = _strip_optional_wrapper(defs[key])

    props = schema.get("properties", {})
    for key, prop in list(props.items()):
        # Pydantic v2 wraps Optional[X] as {"anyOf": [X_schema, {"type": "null"}]}
        if "anyOf" in prop:
            non_null = [s for s in prop["anyOf"] if s.get("type") != "null"]
            if len(non_null) == 1:
                merged = {**prop}
                del merged["anyOf"]
                merged.update(non_null[0])
                props[key] = merged

        # Recurse into nested objects/arrays
        if props[key].get("type") == "object":
            props[key] = _strip_optional_wrapper(props[key])
        if props[key].get("type") == "array" and isinstance(props[key].get("items"), dict):
            props[key]["items"] = _strip_optional_wrapper(props[key]["items"])

    return schema


class PromptEngine:
    """
    核心模板引擎。

    使用方式：
        response = await prompt_engine.generate(
            template_name="topic_generate.j2",
            response_model=TopicGenerateResponse,
            topics=["international arbitration"],
            level="intermediate",
            ...
        )
    """

    SECTION_SEPARATOR = "\n---\n"

    def __init__(self, prompts_dir: str | None = None):
        self._dir = prompts_dir or _PROMPTS_DIR
        self.env = Environment(
            loader=FileSystemLoader(self._dir),
            # 保留未定义变量为空字符串（而非报错），方便模板编写
            undefined=_SilentUndefined,
            # 去除模板块前后多余空行
            trim_blocks=True,
            lstrip_blocks=True,
            # 热更新：每次渲染都检查文件是否被修改
            auto_reload=True,
        )
        # 注册常用 filter
        self.env.filters["join_or_default"] = _join_or_default

    # ──────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────

    def render(self, template_name: str, **variables: Any) -> Tuple[str, str]:
        """
        渲染 Jinja2 模板，返回 (system_prompt, user_prompt)。

        模板内使用 ``---`` 分隔 system 部分和 user 部分。
        """
        template = self.env.get_template(template_name)
        rendered = template.render(**variables)
        return self._split_sections(rendered)

    def get_response_schema(self, response_model: Type[BaseModel]) -> dict:
        """从 Pydantic model 生成 JSON Schema，并清理 Optional 包装。"""
        schema = response_model.model_json_schema()
        return _strip_optional_wrapper(schema)

    async def generate(
        self,
        template_name: str,
        response_model: Type[BaseModel],
        *,
        max_tokens: int = 4000,
        **variables: Any,
    ) -> BaseModel:
        """
        一站式调用：
        1. 渲染 Jinja2 模板
        2. 生成 JSON Schema
        3. 调用 LLM（带 schema 约束）
        4. Pydantic 校验 & 返回类型安全的对象
        """
        system_prompt, user_prompt = self.render(template_name, **variables)
        schema = self.get_response_schema(response_model)

        # 延迟导入，避免循环依赖
        from services.llm import call_llm_with_schema

        raw = await call_llm_with_schema(
            system_prompt, user_prompt, schema, max_tokens=max_tokens
        )
        return response_model.model_validate(raw)

    # ──────────────────────────────────────────────
    #  Internal helpers
    # ──────────────────────────────────────────────

    def _split_sections(self, rendered: str) -> Tuple[str, str]:
        """
        按 ``---`` 分隔符拆分为 system / user 两段。
        如果没有分隔符，整段作为 user prompt，system 留空。
        """
        if self.SECTION_SEPARATOR in rendered:
            parts = rendered.split(self.SECTION_SEPARATOR, 1)
            return parts[0].strip(), parts[1].strip()
        return "", rendered.strip()


# ──────────────────────────────────────────────
#  Jinja2 helpers
# ──────────────────────────────────────────────


class _SilentUndefined(Undefined):
    """Jinja2 undefined 策略：未定义变量返回空字符串，不报错。"""

    def __str__(self):
        return ""

    def __iter__(self):
        return iter([])

    def __bool__(self):
        return False

    def __getattr__(self, name):
        return self


def _join_or_default(value, sep=", ", default="General") -> str:
    """Jinja2 filter: join list or return default string."""
    if not value:
        return default
    if isinstance(value, str):
        return value
    return sep.join(str(v) for v in value)


# ──────────────────────────────────────────────
#  Singleton
# ──────────────────────────────────────────────

prompt_engine = PromptEngine()
