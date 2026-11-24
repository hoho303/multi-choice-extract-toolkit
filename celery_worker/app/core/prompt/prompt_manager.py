import os
from typing import Any

from jinja2 import Environment, Template, meta

from loguru import logger
from app.core.prompt.schema import Prompt


class PromptManager:
    """Manages loading, rendering, and saving of prompt templates."""

    def __init__(self, prompt_dir: str = "prompts"):
        self.prompt_dir = prompt_dir
        self.prompts: dict[str, Prompt] = {}
        self.jinja_env = Environment()

        os.makedirs(self.prompt_dir, exist_ok=True)
        self._load_all_prompts()

    def _load_all_prompts(self):
        logger.info(f"Scanning for prompts in directory: '{self.prompt_dir}'")
        for root, _, files in os.walk(self.prompt_dir):
            for filename in files:
                if not filename.endswith(".j2"):
                    continue

                filepath = os.path.join(root, filename)
                try:
                    relative_path = os.path.relpath(root, self.prompt_dir)
                    base_name = filename[: -len(".j2")]

                    if relative_path == ".":
                        prompt_name = base_name
                    else:
                        namespace = relative_path.replace(os.sep, ".")
                        prompt_name = f"{namespace}.{base_name}"

                    with open(filepath, encoding="utf-8") as f:
                        template_content = f.read()

                    ast = self.jinja_env.parse(template_content)
                    variables = sorted(meta.find_undeclared_variables(ast))

                    prompt = Prompt(name=prompt_name, template=template_content, variables=variables)

                    if prompt.name in self.prompts:
                        logger.warning(f"Duplicate prompt name '{prompt.name}' found in {filename}. Overwriting.")
                    self.prompts[prompt.name] = prompt
                except Exception as e:
                    logger.error(f"Failed to load prompt from '{filepath}': {e}")
        logger.info(f"Finished loading prompts. Total: {len(self.prompts)} loaded.")

    def get_prompt(self, name: str) -> Prompt:
        prompt = self.prompts.get(name)
        if not prompt:
            raise ValueError(f"Prompt '{name}' not found.")
        return prompt

    def render(self, name: str, **kwargs: Any) -> str:
        prompt = self.get_prompt(name)
        try:
            template = Template(prompt.template)
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"Error rendering prompt '{name}': {e}")
            raise ValueError(f"Error rendering prompt template '{name}': {e}")

    def save_prompt(self, prompt: Prompt):
        filepath = os.path.join(self.prompt_dir, f"{prompt.name}.j2")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(prompt.template)

            self.prompts[prompt.name] = prompt
            logger.info(f"Prompt '{prompt.name}' saved to '{filepath}'")
        except Exception as e:
            logger.error(f"Error saving prompt '{prompt.name}' to '{filepath}': {e}")
            raise ValueError(f"Could not save prompt to '{filepath}': {e}")

    def list_prompts(self) -> list[str]:
        return list(self.prompts.keys())

prompt_manager = PromptManager(prompt_dir="app/core/prompt/prompt_templates")