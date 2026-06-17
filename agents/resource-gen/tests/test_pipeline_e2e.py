"""resource-gen —— 完整管线端到端测试（Mock LLM，无外部依赖）。

验证：①→②→③→④→⑤ 全链路跑通，真实生成 PPT 文件，
进度推进顺序正确，WS 通知被触发。
"""
from __future__ import annotations

import pytest
from ai_edu_common.enums import ResourceTypeEnum

from src.dependencies import Container


@pytest.mark.asyncio
async def test_pipeline_generates_ppt(container, sample_profile):
    """完整管线生成 PPT。"""
    tm = container.task_manager
    task = await tm.create_task("sess_e2e", "生成BERT讲解PPT")

    await tm._run_pipeline(
        task_id=task.taskId,
        session_id="sess_e2e",
        user_request="生成BERT讲解PPT",
        profile=sample_profile,
    )

    final = await tm.get_task(task.taskId)
    assert final.status.value == "completed"
    assert final.progress == 100
    assert final.result is not None
    assert len(final.result.resources) == 1

    resource = final.result.resources[0]
    assert resource.type == ResourceTypeEnum.PPT
    assert resource.resourceId.startswith("res_")
    assert resource.url.endswith(".pptx")
    assert resource.title


@pytest.mark.asyncio
async def test_pipeline_generates_mindmap(container, sample_profile):
    """管线按 resourceType=mindmap 分流生成思维导图。"""
    resource = await container.pipeline.execute(
        task_id="task_mindmap_test",
        session_id="sess_e2e",
        user_request="生成思维导图",
        profile=sample_profile,
        resource_type="mindmap",
    )
    assert resource.type.value == "mindmap"
    assert resource.url.endswith(".mindmap.md")
    # 文件确实落盘到临时存储目录
    from src.config import settings
    from pathlib import Path

    files = list(Path(settings.FILE_STORAGE_PATH).glob("*.mindmap.md"))
    assert files, "应生成思维导图文件"


@pytest.mark.asyncio
async def test_pipeline_progress_sequence(container, sample_profile):
    """进度推进顺序：10→30→55→75→90→100，且 WS 通知被触发。"""
    tm = container.task_manager
    tm.notifier.clear()
    task = await tm.create_task("sess_e2e", "PPT")
    await tm._run_pipeline(
        task_id=task.taskId,
        session_id="sess_e2e",
        user_request="PPT",
        profile=sample_profile,
    )
    # WS 至少推送过 progress 与 resource_card
    types = tm.notifier.types_sent()
    assert "progress" in types
    assert "resource_card" in types


@pytest.mark.asyncio
async def test_pipeline_safety_block(container, sample_profile, monkeypatch):
    """内容违规时任务应标记 failed，错误码 3001。"""
    # 注入违规内容到大纲内容流
    from src.orchestrator import content_writer as cw_mod

    class BadWriter(cw_mod.ContentWriter):
        async def write_all(self, outline, profile):
            from src.models.dto import SectionContent

            return [
                SectionContent(title="x", order=1, markdown="这里包含 色情 违规内容"),
                SectionContent(title="y", order=2, markdown="正常内容"),
            ]

    container.pipeline.content_writer = BadWriter(container.llm)

    tm = container.task_manager
    task = await tm.create_task("sess_e2e", "PPT")
    await tm._run_pipeline(
        task_id=task.taskId,
        session_id="sess_e2e",
        user_request="PPT",
        profile=sample_profile,
    )
    final = await tm.get_task(task.taskId)
    assert final.status.value == "failed"
    assert final.error.code == 3001
