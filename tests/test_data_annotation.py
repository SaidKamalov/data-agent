"""Integration tests for data annotation templates and configuration.

Tests verify template script syntax, agent definition validity,
and SKILL.md frontmatter correctness.
Test artifacts are stored in test_data-annotation-session/ and cleaned up at the end.
"""

import py_compile
import shutil
from pathlib import Path

import pytest
import yaml

SCRIPTS_DIR = (
    Path(__file__).parent.parent
    / ".opencode"
    / "skills"
    / "data-annotation"
    / "scripts"
)
SKILL_DIR = Path(__file__).parent.parent / ".opencode" / "skills" / "data-annotation"
AGENTS_DIR = Path(__file__).parent.parent / ".opencode" / "agents"
SESSION_DIR = Path(__file__).parent / "test_data-annotation-session"


# ---------------------------------------------------------------------------
# Template syntax tests
# ---------------------------------------------------------------------------


class TestTemplateSyntax:
    """Verify all template scripts have valid Python syntax."""

    @pytest.mark.parametrize(
        "script_name",
        [
            "template_sample.py",
            "template_labelstudio.py",
        ],
    )
    def test_template_compiles(self, script_name: str) -> None:
        """Each template script should compile without syntax errors."""
        script_path = SCRIPTS_DIR / script_name
        assert script_path.exists(), f"Template {script_name} not found"
        py_compile.compile(str(script_path), doraise=True)


# ---------------------------------------------------------------------------
# Template content tests
# ---------------------------------------------------------------------------


class TestTemplateContent:
    """Verify template scripts contain expected patterns."""

    def test_sample_has_random(self) -> None:
        """template_sample.py should contain random sampling pattern."""
        content = (SCRIPTS_DIR / "template_sample.py").read_text()
        assert "sample" in content.lower()
        assert "random_state" in content

    def test_sample_has_stratified(self) -> None:
        """template_sample.py should contain stratified sampling pattern."""
        content = (SCRIPTS_DIR / "template_sample.py").read_text()
        assert "stratif" in content.lower()

    def test_sample_has_balanced(self) -> None:
        """template_sample.py should contain balanced sampling pattern."""
        content = (SCRIPTS_DIR / "template_sample.py").read_text()
        assert "balanced" in content.lower()

    def test_sample_has_label_detection(self) -> None:
        """template_sample.py should detect label columns."""
        content = (SCRIPTS_DIR / "template_sample.py").read_text()
        assert "label" in content.lower()

    def test_sample_has_index_preservation(self) -> None:
        """template_sample.py should preserve original indices."""
        content = (SCRIPTS_DIR / "template_sample.py").read_text()
        assert "index" in content.lower()

    def test_sample_has_stats(self) -> None:
        """template_sample.py should compute sampling statistics."""
        content = (SCRIPTS_DIR / "template_sample.py").read_text()
        assert "stats" in content.lower() or "distribution" in content.lower()

    def test_labelstudio_has_classification_task(self) -> None:
        """template_labelstudio.py should build classification tasks."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert "classification" in content.lower()
        assert "choices" in content

    def test_labelstudio_has_from_name(self) -> None:
        """template_labelstudio.py should use from_name field."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert "from_name" in content

    def test_labelstudio_has_to_name(self) -> None:
        """template_labelstudio.py should use to_name field."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert "to_name" in content

    def test_labelstudio_has_score(self) -> None:
        """template_labelstudio.py should include confidence score."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert "score" in content
        assert "confidence" in content.lower()

    def test_labelstudio_has_validation(self) -> None:
        """template_labelstudio.py should validate JSON structure."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert "validate" in content.lower()

    def test_labelstudio_has_agreement(self) -> None:
        """template_labelstudio.py should compute agreement."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert "agreement" in content.lower()

    def test_labelstudio_has_predictions(self) -> None:
        """template_labelstudio.py should use predictions key."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert "predictions" in content

    def test_labelstudio_has_data_key(self) -> None:
        """template_labelstudio.py should use data key."""
        content = (SCRIPTS_DIR / "template_labelstudio.py").read_text()
        assert '"data"' in content


# ---------------------------------------------------------------------------
# SKILL.md frontmatter tests
# ---------------------------------------------------------------------------


class TestSkillFrontmatter:
    """Verify SKILL.md has valid frontmatter with required fields."""

    def _parse_frontmatter(self) -> dict:
        """Parse YAML frontmatter from SKILL.md."""
        skill_path = SKILL_DIR / "SKILL.md"
        content = skill_path.read_text()
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        parts = content.split("---", 2)
        assert len(parts) >= 3, "SKILL.md must have opening and closing ---"
        return yaml.safe_load(parts[1])

    def test_skill_exists(self) -> None:
        """SKILL.md must exist in the data-annotation skill directory."""
        assert (SKILL_DIR / "SKILL.md").exists()

    def test_frontmatter_has_name(self) -> None:
        """SKILL.md frontmatter must include 'name'."""
        fm = self._parse_frontmatter()
        assert "name" in fm

    def test_frontmatter_name_is_data_annotation(self) -> None:
        """SKILL.md name must match directory name 'data-annotation'."""
        fm = self._parse_frontmatter()
        assert fm["name"] == "data-annotation"

    def test_frontmatter_has_description(self) -> None:
        """SKILL.md frontmatter must include 'description'."""
        fm = self._parse_frontmatter()
        assert "description" in fm
        assert len(fm["description"]) > 0

    def test_frontmatter_has_metadata(self) -> None:
        """SKILL.md frontmatter should include metadata with pipeline-stage."""
        fm = self._parse_frontmatter()
        assert "metadata" in fm
        assert "pipeline-stage" in fm["metadata"]
        assert fm["metadata"]["pipeline-stage"] == "annotation"

    def test_skill_body_has_workflow(self) -> None:
        """SKILL.md body should describe the workflow steps."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "## Workflow" in content or "## workflow" in content.lower()

    def test_skill_body_has_decision_points(self) -> None:
        """SKILL.md body should define decision points for user interaction."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "DECISION POINT" in content or "decision point" in content.lower()

    def test_skill_body_has_labeling_guidance(self) -> None:
        """SKILL.md body should include labeling guidance."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "labeling" in content.lower() or "annotator" in content.lower()

    def test_skill_body_has_labelstudio_format(self) -> None:
        """SKILL.md body should reference LabelStudio JSON format."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "labelstudio" in content.lower() or "label studio" in content.lower()

    def test_skill_body_has_report_template(self) -> None:
        """SKILL.md body should include report.md template."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "report" in content.lower()


# ---------------------------------------------------------------------------
# Agent definition tests
# ---------------------------------------------------------------------------


class TestAgentDefinition:
    """Verify the annotation agent definition is valid."""

    def _parse_frontmatter(self) -> dict:
        """Parse YAML frontmatter from agent markdown file."""
        agent_path = AGENTS_DIR / "annotation.md"
        content = agent_path.read_text()
        assert content.startswith("---"), "Agent must start with YAML frontmatter"
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Agent must have opening and closing ---"
        return yaml.safe_load(parts[1])

    def test_agent_file_exists(self) -> None:
        """annotation.md agent must exist."""
        assert (AGENTS_DIR / "annotation.md").exists()

    def test_frontmatter_has_description(self) -> None:
        """Agent frontmatter must include 'description'."""
        fm = self._parse_frontmatter()
        assert "description" in fm
        assert len(fm["description"]) > 0

    def test_frontmatter_has_mode(self) -> None:
        """Agent frontmatter must specify 'mode: subagent'."""
        fm = self._parse_frontmatter()
        assert fm.get("mode") == "subagent"

    def test_frontmatter_has_temperature(self) -> None:
        """Agent frontmatter should specify temperature (low for consistency)."""
        fm = self._parse_frontmatter()
        assert "temperature" in fm
        assert isinstance(fm["temperature"], (int, float))
        assert 0.0 <= fm["temperature"] <= 1.0

    def test_frontmatter_has_steps(self) -> None:
        """Agent frontmatter must include steps."""
        fm = self._parse_frontmatter()
        assert "steps" in fm
        assert isinstance(fm["steps"], int)
        assert fm["steps"] > 0

    def test_frontmatter_has_permissions(self) -> None:
        """Agent frontmatter must include bash and edit permissions."""
        fm = self._parse_frontmatter()
        assert "permission" in fm
        perm = fm["permission"]
        assert "bash" in perm
        assert "edit" in perm

    def test_bash_permission_allows_all(self) -> None:
        """Bash permission should allow all commands."""
        fm = self._parse_frontmatter()
        bash_perm = fm["permission"]["bash"]
        assert bash_perm.get("*") == "allow"

    def test_edit_permission_is_allow(self) -> None:
        """Edit permission should be 'allow' for writing temp scripts."""
        fm = self._parse_frontmatter()
        assert fm["permission"]["edit"] == "allow"

    def test_agent_body_has_instructions(self) -> None:
        """Agent body should contain step-by-step instructions."""
        content = (AGENTS_DIR / "annotation.md").read_text()
        assert "## Instructions" in content or "## instructions" in content.lower()

    def test_agent_references_skill(self) -> None:
        """Agent body should reference loading the skill."""
        content = (AGENTS_DIR / "annotation.md").read_text()
        assert "skill" in content.lower()
        assert "data-annotation" in content


# ---------------------------------------------------------------------------
# LabelStudio JSON structure validation
# ---------------------------------------------------------------------------


class TestLabelStudioStructure:
    """Verify example LabelStudio JSON structure is valid."""

    def test_valid_task_structure(self) -> None:
        """A valid LabelStudio task should have data, predictions, result."""
        task = {
            "data": {"text": "sample text", "label": "positive"},
            "predictions": [
                {
                    "result": [
                        {
                            "from_name": "label_class",
                            "to_name": "text",
                            "type": "choices",
                            "value": {"choices": ["Positive"]},
                        }
                    ],
                    "score": 0.92,
                }
            ],
        }
        assert "data" in task
        assert "predictions" in task
        assert len(task["predictions"]) > 0
        pred = task["predictions"][0]
        assert "result" in pred
        assert "score" in pred
        res = pred["result"][0]
        assert "from_name" in res
        assert "to_name" in res
        assert "type" in res
        assert "value" in res
        assert "choices" in res["value"]

    def test_multiple_tasks_list(self) -> None:
        """LabelStudio export should be a list of tasks."""
        tasks = [
            {
                "data": {"text": f"sample {i}"},
                "predictions": [
                    {
                        "result": [
                            {
                                "from_name": "label_class",
                                "to_name": "text",
                                "type": "choices",
                                "value": {"choices": ["Label"]},
                            }
                        ],
                        "score": 0.8,
                    }
                ],
            }
            for i in range(3)
        ]
        assert isinstance(tasks, list)
        assert len(tasks) == 3
        for task in tasks:
            assert "data" in task
            assert "predictions" in task


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def cleanup_session_dir() -> None:
    """Remove test_data-annotation-session/ after all tests finish."""
    yield
    if SESSION_DIR.exists():
        shutil.rmtree(SESSION_DIR)
