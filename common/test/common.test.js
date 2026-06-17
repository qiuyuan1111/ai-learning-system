/**
 * @ai-edu/common (TypeScript) —— 单元测试（Node 内置 assert，无需额外测试框架）
 *
 * 运行：node test/common.test.js
 * CI 中由 `npm test` 触发。
 */
const assert = require('assert')
const {
  IdGenerator,
  JsonUtils,
  success,
  error,
  paginated,
  ResourceTypeEnum,
  TaskStatusEnum,
  PathNodeStatusEnum,
  IntentEnum,
  ErrorCodeEnum,
} = require('../dist/index.js')

let passed = 0
let failed = 0

function test(name, fn) {
  try {
    fn()
    passed++
    console.log(`  ✓ ${name}`)
  } catch (e) {
    failed++
    console.error(`  ✗ ${name}`)
    console.error(`      ${e.message}`)
    process.exitCode = 1
  }
}

async function testAsync(name, fn) {
  try {
    await fn()
    passed++
    console.log(`  ✓ ${name}`)
  } catch (e) {
    failed++
    console.error(`  ✗ ${name}`)
    console.error(`      ${e.message}`)
    process.exitCode = 1
  }
}

console.log('\n=== @ai-edu/common 单元测试 ===\n')

// ── ID 生成 ──
console.log('[IdGenerator]')
test('sessionId 格式 sess_ + 16 hex', () => {
  const id = IdGenerator.sessionId()
  assert.ok(id.startsWith('sess_'))
  assert.match(id.slice(5), /^[0-9a-f]{16}$/)
})
test('resourceId 格式 res_ + 16 hex', () => {
  const id = IdGenerator.resourceId()
  assert.ok(id.startsWith('res_'))
  assert.match(id.slice(4), /^[0-9a-f]{16}$/)
})
test('taskId 格式 task_ + 16 hex', () => {
  const id = IdGenerator.taskId()
  assert.ok(id.startsWith('task_'))
  assert.match(id.slice(5), /^[0-9a-f]{16}$/)
})
test('pathId 格式 path_ + 16 hex', () => {
  const id = IdGenerator.pathId()
  assert.ok(id.startsWith('path_'))
  assert.match(id.slice(5), /^[0-9a-f]{16}$/)
})
test('requestId 是 UUID', () => {
  assert.match(IdGenerator.requestId(), /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i)
})
test('ID 唯一性（1000 次无碰撞）', () => {
  const ids = new Set(Array.from({ length: 1000 }, () => IdGenerator.sessionId()))
  assert.strictEqual(ids.size, 1000)
})

// ── 枚举 ──
console.log('[Enums]')
test('资源类型 5 种', () => {
  const vals = Object.values(ResourceTypeEnum)
  assert.deepStrictEqual(vals.sort(), ['doc', 'mindmap', 'pdf', 'ppt', 'video'])
})
test('任务状态 4 种', () => {
  assert.deepStrictEqual(Object.values(TaskStatusEnum).sort(), ['completed', 'failed', 'pending', 'processing'])
})
test('错误码数值与 api.md 一致', () => {
  assert.strictEqual(ErrorCodeEnum.SUCCESS, 0)
  assert.strictEqual(ErrorCodeEnum.CONTENT_SAFETY_VIOLATION, 3001)
  assert.strictEqual(ErrorCodeEnum.TASK_NOT_FOUND, 2001)
})

// ── 响应体构造 ──
console.log('[Response builders]')
test('success 结构', () => {
  const r = success({ a: 1 }, 'req_x')
  assert.strictEqual(r.code, 0)
  assert.strictEqual(r.message, 'success')
  assert.deepStrictEqual(r.data, { a: 1 })
  assert.strictEqual(r.requestId, 'req_x')
  assert.deepStrictEqual(Object.keys(r).sort(), ['code', 'data', 'message', 'requestId'])
})
test('success 自动生成 requestId', () => {
  const r = success(null)
  assert.ok(r.requestId)
})
test('error 结构', () => {
  const r = error(2001, '任务不存在')
  assert.strictEqual(r.code, 2001)
  assert.strictEqual(r.data, null)
})
test('paginated 自动 totalPages', () => {
  const p = paginated([1], 1, 20, 55)
  assert.strictEqual(p.pageInfo.totalPages, 3)
  assert.deepStrictEqual(Object.keys(p), ['list', 'pageInfo'])
  assert.deepStrictEqual(Object.keys(p.pageInfo).sort(), ['page', 'pageSize', 'total', 'totalPages'])
})

// ── JSON 工具 ──
console.log('[JsonUtils]')
test('safeParse 合法 JSON', () => {
  assert.deepStrictEqual(JsonUtils.safeParse('{"a":1}'), { a: 1 })
})
test('safeParse 非法 JSON 返回 fallback', () => {
  assert.strictEqual(JsonUtils.safeParse('bad'), null)
  assert.deepStrictEqual(JsonUtils.safeParse('bad', []), [])
})

console.log(`\n结果: ${passed} 通过, ${failed} 失败\n`)
if (failed > 0) process.exit(1)
