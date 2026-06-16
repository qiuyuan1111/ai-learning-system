import { SessionPayload } from '../utils/jwt'

declare global {
  namespace Express {
    interface Request {
      session?: SessionPayload
      traceId?: string
    }
  }
}
