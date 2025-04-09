"""
LLM client for extracting company purpose statements.
"""

import json
import logging
from typing import Dict, Optional, Any

from openai import OpenAI

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_PROMPT_TEMPLATE_PATH,
)

# Configure logging
logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with the LLM API to extract company purpose."""

    def __init__(
        self,
        api_key: str = LLM_API_KEY,
        base_url: str = LLM_BASE_URL,
        model: str = LLM_MODEL,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
        prompt_template_path: str = LLM_PROMPT_TEMPLATE_PATH,
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: API key for the LLM service
            base_url: Base URL for the LLM service
            model: Model name to use
            temperature: Temperature for generation (0-2)
            max_tokens: Maximum tokens for generation
            prompt_template_path: Path to the prompt template file
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = self._load_prompt_template(prompt_template_path)

    @staticmethod
    def _load_prompt_template(path: str) -> str:
        """
        Load the prompt template from file.

        Args:
            path: Path to the prompt template file

        Returns:
            str: Prompt template
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
                # Verify the prompt contains the required placeholders
                if "{url}" not in prompt_template or "{text}" not in prompt_template:
                    logger.warning(
                        "Prompt template is missing {url} or {text} placeholders"
                    )
                return prompt_template
        except Exception as e:
            logger.error(f"Error loading prompt template from {path}: {e}")
            # Fallback to a simple prompt template

    def extract_purpose(self, url: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract company purpose from text using the LLM.

        Args:
            url: URL of the company website
            text: Text from which to extract the purpose

        Returns:
            Optional[Dict[str, Any]]: Extracted purpose information or None if error
        """
        try:
            # Prepare prompt
            prompt = self.prompt_template.format(
                url=url, text=text[:4000]
            )  # Limit text length

            # Call the LLM API
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cautious assistant extracting company purposes.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                stream=False,
            )

            # Extract and parse response
            result = response.choices[0].message.content

            # Clean JSON string if needed
            cleaned_json = result
            if "```json" in result:
                cleaned_json = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                cleaned_json = result.split("```")[1].strip()

            # Parse JSON
            purpose_data = json.loads(cleaned_json)

            return purpose_data

        except Exception as e:
            logger.error(f"Error extracting purpose with LLM: {e}")
            return None
