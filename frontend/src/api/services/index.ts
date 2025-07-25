// Service instances
export { authService } from './auth'
export { classesService } from './classes'
export { configService } from './config'
export { employeesService } from './employees'
export { exercisesService } from './exercises'
export { membershipsService } from './memberships'
export { paymentsService } from './payments'
export { routinesService } from './routines'
export { usersService } from './users'

// Export service classes for type definitions and static access
// Some services export the instance as default, others export the class, some only have named exports
export { default as AuthService } from './auth' // exports authService instance
export { default as ClassesService } from './classes' // exports classesService instance
export { default as ConfigService } from './config'
export { EmployeesService } from './employees' // only has named export
export { default as ExercisesService } from './exercises'
export { MembershipsService } from './memberships' // only has named export
export { PaymentsService } from './payments' // only has named export
export { default as RoutinesService } from './routines' // exports RoutinesService class
export { default as UsersService } from './users'