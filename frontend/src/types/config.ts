// System Configuration Types
export interface SystemConfig {
  id: string
  gymName: string
  gymDescription?: string
  address: string
  phone: string
  email: string
  website?: string
  timezone: string
  currency: string
  language: string
  dateFormat: string
  timeFormat: string
  businessHours: BusinessHours
  features: SystemFeatures
  integrations: SystemIntegrations
  createdAt: string
  updatedAt: string
}

export interface BusinessHours {
  monday: DaySchedule
  tuesday: DaySchedule
  wednesday: DaySchedule
  thursday: DaySchedule
  friday: DaySchedule
  saturday: DaySchedule
  sunday: DaySchedule
}

export interface DaySchedule {
  isOpen: boolean
  openTime?: string
  closeTime?: string
  breaks?: TimeBreak[]
}

export interface TimeBreak {
  startTime: string
  endTime: string
  description?: string
}

export interface SystemFeatures {
  membershipManagement: boolean
  classBooking: boolean
  personalTraining: boolean
  paymentProcessing: boolean
  inventoryManagement: boolean
  reportingAnalytics: boolean
  mobileApp: boolean
  onlineBooking: boolean
  emailNotifications: boolean
  smsNotifications: boolean
  loyaltyProgram: boolean
  referralProgram: boolean
}

export interface SystemIntegrations {
  paymentGateway?: PaymentGatewayConfig
  emailService?: EmailServiceConfig
  smsService?: SmsServiceConfig
  calendarSync?: CalendarSyncConfig
  socialMedia?: SocialMediaConfig
}

export interface PaymentGatewayConfig {
  provider: 'stripe' | 'paypal' | 'square' | 'other'
  publicKey?: string
  webhookUrl?: string
  isActive: boolean
}

export interface EmailServiceConfig {
  provider: 'smtp' | 'sendgrid' | 'mailgun' | 'ses' | 'other'
  host?: string
  port?: number
  username?: string
  fromEmail: string
  fromName: string
  isActive: boolean
}

export interface SmsServiceConfig {
  provider: 'twilio' | 'nexmo' | 'aws-sns' | 'other'
  fromNumber?: string
  isActive: boolean
}

export interface CalendarSyncConfig {
  provider: 'google' | 'outlook' | 'apple' | 'other'
  isActive: boolean
}

export interface SocialMediaConfig {
  facebook?: string
  instagram?: string
  twitter?: string
  youtube?: string
  linkedin?: string
}

// Brand Configuration
export interface BrandConfig {
  id: string
  logoUrl?: string
  faviconUrl?: string
  primaryColor: string
  secondaryColor: string
  accentColor: string
  backgroundColor: string
  textColor: string
  fontFamily: string
  borderRadius: string
  customCss?: string
  customJs?: string
  createdAt: string
  updatedAt: string
}

// Notification Configuration
export interface NotificationConfig {
  id: string
  emailNotifications: EmailNotificationSettings
  smsNotifications: SmsNotificationSettings
  pushNotifications: PushNotificationSettings
  inAppNotifications: InAppNotificationSettings
  createdAt: string
  updatedAt: string
}

export interface EmailNotificationSettings {
  enabled: boolean
  welcomeEmail: boolean
  membershipExpiry: boolean
  paymentReminder: boolean
  classReminder: boolean
  classConfirmation: boolean
  classCancellation: boolean
  promotionalEmails: boolean
  newsletterEmails: boolean
  systemAlerts: boolean
}

export interface SmsNotificationSettings {
  enabled: boolean
  membershipExpiry: boolean
  paymentReminder: boolean
  classReminder: boolean
  classConfirmation: boolean
  classCancellation: boolean
  emergencyAlerts: boolean
}

export interface PushNotificationSettings {
  enabled: boolean
  classReminder: boolean
  paymentReminder: boolean
  promotionalOffers: boolean
  systemUpdates: boolean
}

export interface InAppNotificationSettings {
  enabled: boolean
  realTimeUpdates: boolean
  systemMessages: boolean
  userMessages: boolean
  adminAlerts: boolean
}

// Request Types
export interface ConfigUpdateRequest {
  gymName?: string
  gymDescription?: string
  address?: string
  phone?: string
  email?: string
  website?: string
  timezone?: string
  currency?: string
  language?: string
  dateFormat?: string
  timeFormat?: string
  businessHours?: Partial<BusinessHours>
  features?: Partial<SystemFeatures>
  integrations?: Partial<SystemIntegrations>
}

export interface BrandConfigUpdateRequest {
  primaryColor?: string
  secondaryColor?: string
  accentColor?: string
  backgroundColor?: string
  textColor?: string
  fontFamily?: string
  borderRadius?: string
  customCss?: string
  customJs?: string
}

export interface NotificationConfigUpdateRequest {
  emailNotifications?: Partial<EmailNotificationSettings>
  smsNotifications?: Partial<SmsNotificationSettings>
  pushNotifications?: Partial<PushNotificationSettings>
  inAppNotifications?: Partial<InAppNotificationSettings>
}

// Search and Filter Types
export interface ConfigSearchParams {
  section?: 'system' | 'brand' | 'notifications'
  feature?: string
  integration?: string
}

// Statistics Types
export interface ConfigStatistics {
  totalConfigurations: number
  activeIntegrations: number
  enabledFeatures: number
  lastUpdated: string
  systemHealth: 'healthy' | 'warning' | 'error'
}

// Validation Types
export interface ConfigValidation {
  isValid: boolean
  errors: ConfigValidationError[]
  warnings: ConfigValidationWarning[]
}

export interface ConfigValidationError {
  field: string
  message: string
  code: string
}

export interface ConfigValidationWarning {
  field: string
  message: string
  suggestion?: string
}

// Export Types
export interface ConfigExportData {
  systemConfig: SystemConfig
  brandConfig: BrandConfig
  notificationConfig: NotificationConfig
  exportedAt: string
  version: string
}

// Import Types
export interface ConfigImportRequest {
  data: ConfigExportData
  overwrite: boolean
  validateOnly?: boolean
}

export interface ConfigImportResult {
  success: boolean
  imported: number
  skipped: number
  errors: ConfigValidationError[]
  warnings: ConfigValidationWarning[]
}