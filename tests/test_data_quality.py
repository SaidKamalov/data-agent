"""Integration tests for data quality templates and configuration.

Tests verify template script syntax, agent definition validity,
and SKILL.md frontmatter correctness.
Test artifacts are stored in test_data-quality-session/ and cleaned up at the end.
"""

import py_compile
import shutil
from pathlib import Path

import pytest
import yaml

SCRIPTS_DIR = (
    Path(__file__).parent.parent / ".opencode" / "skills" / "data-quality" / "scripts"
)
SKILL_DIR = Path(__file__).parent.parent / ".opencode" / "skills" / "data-quality"
AGENTS_DIR = Path(__file__).parent.parent / ".opencode" / "agents"
SESSION_DIR = Path(__file__).parent / "test_data-quality-session"


# ---------------------------------------------------------------------------
# Template syntax tests
# ---------------------------------------------------------------------------


class TestTemplateSyntax:
    """Verify all template scripts have valid Python syntax."""

    @pytest.mark.parametrize(
        "script_name",
        [
            "template_read_data.py",
            "template_missing_values.py",
            "template_duplicates.py",
            "template_outliers_iqr.py",
            "template_impute_missing.py",
        ],
    )
    def test_template_compiles(self, script_name: str) -> None:
        """Each template script should compile without syntax errors."""
        script_path = SCRIPTS_DIR / script_name
        assert script_path.exists(), f"Template {script_name} not found"
        py_compile.compile(str(script_path), doraise=True)


class TestTemplateContent:
    """Verify template scripts contain expected patterns."""

    def test_read_data_has_csv_pattern(self) -> None:
        """template_read_data.py should contain CSV reading patterns."""
        content = (SCRIPTS_DIR / "template_read_data.py").read_text()
        assert "pd.read_csv" in content
        assert "encoding" in content

    def test_read_data_has_parquet_pattern(self) -> None:
        """template_read_data.py should contain Parquet reading patterns."""
        content = (SCRIPTS_DIR / "template_read_data.py").read_text()
        assert "pd.read_parquet" in content

    def test_read_data_has_excel_pattern(self) -> None:
        """template_read_data.py should contain Excel reading patterns."""
        content = (SCRIPTS_DIR / "template_read_data.py").read_text()
        assert "pd.read_excel" in content

    def test_read_data_has_inspection(self) -> None:
        """template_read_data.py should contain initial inspection patterns."""
        content = (SCRIPTS_DIR / "template_read_data.py").read_text()
        assert "df.shape" in content
        assert "df.dtypes" in content

    def test_missing_values_has_summary(self) -> None:
        """template_missing_values.py should contain missing summary patterns."""
        content = (SCRIPTS_DIR / "template_missing_values.py").read_text()
        assert "isnull().sum()" in content
        assert "isnull().mean()" in content

    def test_missing_values_has_correlated(self) -> None:
        """template_missing_values.py should contain correlated missingness."""
        content = (SCRIPTS_DIR / "template_missing_values.py").read_text()
        assert "correlated_missing" in content or "corr" in content

    def test_missing_values_has_classification(self) -> None:
        """template_missing_values.py should classify missingness types."""
        content = (SCRIPTS_DIR / "template_missing_values.py").read_text()
        assert "MCAR" in content
        assert "MAR" in content
        assert "MNAR" in content

    def test_duplicates_has_exact(self) -> None:
        """template_duplicates.py should detect exact duplicates."""
        content = (SCRIPTS_DIR / "template_duplicates.py").read_text()
        assert "duplicated()" in content

    def test_duplicates_has_fuzzy(self) -> None:
        """template_duplicates.py should have near-duplicate detection."""
        content = (SCRIPTS_DIR / "template_duplicates.py").read_text()
        assert "SequenceMatcher" in content

    def test_duplicates_has_impact(self) -> None:
        """template_duplicates.py should analyze dedup impact."""
        content = (SCRIPTS_DIR / "template_duplicates.py").read_text()
        assert "dedup_impact" in content or "impact" in content.lower()

    def test_outliers_has_iqr(self) -> None:
        """template_outliers_iqr.py should compute IQR bounds."""
        content = (SCRIPTS_DIR / "template_outliers_iqr.py").read_text()
        assert "quantile(0.25)" in content
        assert "quantile(0.75)" in content
        assert "IQR" in content or "iqr" in content

    def test_outliers_has_zscore(self) -> None:
        """template_outliers_iqr.py should support z-score detection."""
        content = (SCRIPTS_DIR / "template_outliers_iqr.py").read_text()
        assert "zscore" in content

    def test_outliers_has_distribution_comparison(self) -> None:
        """template_outliers_iqr.py should compare distributions."""
        content = (SCRIPTS_DIR / "template_outliers_iqr.py").read_text()
        assert "before" in content
        assert "after" in content

    def test_impute_has_drop(self) -> None:
        """template_impute_missing.py should support dropping rows."""
        content = (SCRIPTS_DIR / "template_impute_missing.py").read_text()
        assert "dropna" in content

    def test_impute_has_statistical(self) -> None:
        """template_impute_missing.py should support mean/median/mode."""
        content = (SCRIPTS_DIR / "template_impute_missing.py").read_text()
        assert "median" in content
        assert "mean" in content

    def test_impute_has_fill(self) -> None:
        """template_impute_missing.py should support forward/backward fill."""
        content = (SCRIPTS_DIR / "template_impute_missing.py").read_text()
        assert "ffill" in content
        assert "bfill" in content

    def test_impute_has_sklearn(self) -> None:
        """template_impute_missing.py should use sklearn SimpleImputer."""
        content = (SCRIPTS_DIR / "template_impute_missing.py").read_text()
        assert "SimpleImputer" in content

    def test_impute_has_distribution_check(self) -> None:
        """template_impute_missing.py should check distribution preservation."""
        content = (SCRIPTS_DIR / "template_impute_missing.py").read_text()
        assert "skew" in content


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
        """SKILL.md must exist in the data-quality skill directory."""
        assert (SKILL_DIR / "SKILL.md").exists()

    def test_frontmatter_has_name(self) -> None:
        """SKILL.md frontmatter must include 'name'."""
        fm = self._parse_frontmatter()
        assert "name" in fm

    def test_frontmatter_name_is_data_quality(self) -> None:
        """SKILL.md name must match directory name 'data-quality'."""
        fm = self._parse_frontmatter()
        assert fm["name"] == "data-quality"

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
        assert fm["metadata"]["pipeline-stage"] == "quality"

    def test_skill_body_has_workflow(self) -> None:
        """SKILL.md body should describe the workflow steps."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "## Workflow" in content or "## workflow" in content.lower()

    def test_skill_body_has_expert_analysis(self) -> None:
        """SKILL.md body should reference expert analysis prompts."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "EXPERT ANALYSIS" in content or "expert analysis" in content.lower()

    def test_skill_body_has_decision_points(self) -> None:
        """SKILL.md body should define decision points for user interaction."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "DECISION POINT" in content or "decision point" in content.lower()

    def test_skill_body_has_report_template(self) -> None:
        """SKILL.md body should include report.md template."""
        content = (SKILL_DIR / "SKILL.md").read_text()
        assert "report" in content.lower()


# ---------------------------------------------------------------------------
# Agent definition tests
# ---------------------------------------------------------------------------


class TestAgentDefinition:
    """Verify the data-quality agent definition is valid."""

    def _parse_frontmatter(self) -> dict:
        """Parse YAML frontmatter from agent markdown file."""
        agent_path = AGENTS_DIR / "data-quality.md"
        content = agent_path.read_text()
        assert content.startswith("---"), "Agent must start with YAML frontmatter"
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Agent must have opening and closing ---"
        return yaml.safe_load(parts[1])

    def test_agent_file_exists(self) -> None:
        """data-quality.md agent must exist."""
        assert (AGENTS_DIR / "data-quality.md").exists()

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
        """Agent frontmatter should specify temperature (low for analysis)."""
        fm = self._parse_frontmatter()
        assert "temperature" in fm
        assert isinstance(fm["temperature"], (int, float))
        assert 0.0 <= fm["temperature"] <= 1.0

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
        content = (AGENTS_DIR / "data-quality.md").read_text()
        assert "## Instructions" in content or "## instructions" in content.lower()

    def test_agent_references_skill(self) -> None:
        """Agent body should reference loading the skill."""
        content = (AGENTS_DIR / "data-quality.md").read_text()
        assert "skill" in content.lower()
        assert "data-quality" in content


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def cleanup_session_dir() -> None:
    """Remove test_data-quality-session/ after all tests finish."""
    yield
    if SESSION_DIR.exists():
        shutil.rmtree(SESSION_DIR)
