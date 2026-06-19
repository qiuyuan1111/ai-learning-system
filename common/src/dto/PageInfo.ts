/**
 * 分页信息
 */
export interface PageInfo {
  /** 当前页码，从 1 开始 */
  page: number
  /** 每页记录数 */
  pageSize: number
  /** 总记录数 */
  total: number
  /** 总页数 */
  totalPages: number
}

/**
 * 分页响应数据包装
 */
export interface PaginatedData<T> {
  list: T[]
  pageInfo: PageInfo
}

/**
 * 构造分页数据，自动计算 totalPages。
 */
export function paginated<T>(list: T[], page: number, pageSize: number, total: number): PaginatedData<T> {
  return {
    list,
    pageInfo: {
      page,
      pageSize,
      total,
      totalPages: pageSize > 0 ? Math.ceil(total / pageSize) : 0,
    },
  }
}
