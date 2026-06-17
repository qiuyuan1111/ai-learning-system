## 变更描述
<!-- 简要描述本次 PR 的内容和目的 -->

## 关联 Issue
<!-- Closes #xxx -->

## 变更类型
- [ ] feat: 新功能
- [ ] fix: Bug 修复
- [ ] refactor: 重构
- [ ] docs: 文档更新
- [ ] test: 测试
- [ ] chore: 构建/工具

## 涉及模块
- [ ] common（共享库，**改动需通知全员**）
- [ ] agents/resource-gen
- [ ] agents/path-planner
- [ ] gateway / 前端（他人模块）
- [ ] docs / scripts / CI

## 契约影响（重要）
- [ ] 本次未修改任何请求体 / 响应体 / DTO 字段 / 错误码
- [ ] 本次修改了对外契约（必须同步更新 docs/api.md 并说明）

## 测试情况
- [ ] 单元测试已添加/更新
- [ ] 本地 `pytest` / `npm test` 通过
- [ ] 接口契约符合 docs/api.md

## Review Checklist
- [ ] 代码符合编码规范
- [ ] 接口兼容已有契约（无破坏性变更，或已沟通）
- [ ] 错误处理完整
- [ ] 无硬编码密钥/凭据（.env 已加入 .gitignore）
