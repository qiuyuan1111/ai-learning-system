import dotenv from 'dotenv'
import path from 'path'

// Load environment variables from .env file
dotenv.config({ path: path.resolve(__dirname, '../../../.env') })

export const config = {
  port: parseInt(process.env.PORT || '3000', 10),
  jwtSecret: process.env.JWT_SECRET || 'ai-learning-system-secret',
  mockMode: process.env.MOCK_MODE === 'true',
  
  // Backend Services
  services: {
    profile: process.env.PROFILE_SERVICE_URL || 'ws://localhost:8081',
    tutor: process.env.TUTOR_SERVICE_URL || 'ws://localhost:8082',
    evaluator: process.env.EVALUATOR_SERVICE_URL || 'http://localhost:8080',
    safety: process.env.SAFETY_SERVICE_URL || 'http://localhost:8083',
    resourceGen: process.env.RESOURCE_GEN_SERVICE_URL || 'http://localhost:8090',
    pathPlanner: process.env.PATH_PLANNER_SERVICE_URL || 'http://localhost:8091',
  }
}
