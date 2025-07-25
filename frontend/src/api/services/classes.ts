import { apiClient } from '../client'
import { API_ENDPOINTS } from '../config'
import {
  GymClass,
  ClassSchedule,
  ClassBooking,
  ClassCategory,
  CreateClassRequest,
  UpdateClassRequest,
  ClassSearchParams,
  ClassListResponse,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  ScheduleSearchParams,
  ScheduleListResponse,
  BookClassRequest,
  BookingSearchParams,
  BookingListResponse,
  ClassStatistics,
  ClassAttendance,
  ClassRating,
  ClassWaitlist,
  RecurringSchedule,

  ClassPackage,
  UserClassPackage,

} from '../../types'

export class ClassesService {
  // Classes
  async getClasses(params?: ClassSearchParams): Promise<ClassListResponse> {
    return apiClient.get(API_ENDPOINTS.CLASSES.CLASSES, { params })
  }

  async getClass(id: number): Promise<GymClass> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.CLASSES}/${id}`)
  }

  async createClass(data: CreateClassRequest): Promise<GymClass> {
    const formData = new FormData()
    
    // Add text fields
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'image' && value !== undefined) {
        if (Array.isArray(value)) {
          formData.append(key, JSON.stringify(value))
        } else {
          formData.append(key, String(value))
        }
      }
    })
    
    // Add image file
    if (data.image) formData.append('image', data.image)
    
    const response = await apiClient.postRaw(API_ENDPOINTS.CLASSES.CLASSES, formData)
    return response.data.data
  }

  async updateClass(id: number, data: UpdateClassRequest): Promise<GymClass> {
    const formData = new FormData()
    
    // Add text fields
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'image' && value !== undefined) {
        if (Array.isArray(value)) {
          formData.append(key, JSON.stringify(value))
        } else {
          formData.append(key, String(value))
        }
      }
    })
    
    // Add image file
    if (data.image) formData.append('image', data.image)
    
    const response = await apiClient.postRaw(`${API_ENDPOINTS.CLASSES.CLASSES}/${id}`, formData)
    return response.data.data
  }

  async deleteClass(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.CLASSES.CLASSES}/${id}`)
  }

  async toggleClassStatus(id: number): Promise<GymClass> {
    return apiClient.patch(`${API_ENDPOINTS.CLASSES.CLASSES}/${id}/toggle-status`)
  }

  // Class Categories
  async getClassCategories(): Promise<ClassCategory[]> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.CLASSES}/categories`)
  }

  async createClassCategory(data: {
    name: string
    description: string
    icon?: string
    color?: string
  }): Promise<ClassCategory> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.CLASSES}/categories`, data)
  }

  async updateClassCategory(id: number, data: {
    name?: string
    description?: string
    icon?: string
    color?: string
    is_active?: boolean
  }): Promise<ClassCategory> {
    return apiClient.put(`${API_ENDPOINTS.CLASSES.CLASSES}/categories/${id}`, data)
  }

  async deleteClassCategory(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.CLASSES.CLASSES}/categories/${id}`)
  }

  // Class Schedules
  async getSchedules(params?: ScheduleSearchParams): Promise<ScheduleListResponse> {
    return apiClient.get(API_ENDPOINTS.CLASSES.SCHEDULES, { params })
  }

  async getSchedule(id: number): Promise<ClassSchedule> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${id}`)
  }

  async createSchedule(data: CreateScheduleRequest): Promise<ClassSchedule> {
    return apiClient.post(API_ENDPOINTS.CLASSES.SCHEDULES, data)
  }

  async updateSchedule(id: number, data: UpdateScheduleRequest): Promise<ClassSchedule> {
    return apiClient.put(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${id}`, data)
  }

  async deleteSchedule(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${id}`)
  }

  async cancelSchedule(id: number, data: {
    reason: string
    notify_participants?: boolean
    refund_policy?: 'full' | 'partial' | 'none'
  }): Promise<ClassSchedule> {
    return apiClient.patch(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${id}/cancel`, data)
  }

  // Recurring Schedules
  async createRecurringSchedule(data: {
    class_id: number
    instructor_id: number
    room: string
    start_date: string
    end_date?: string
    recurrence_pattern: {
      type: 'daily' | 'weekly' | 'monthly'
      interval: number
      days_of_week?: number[]
      day_of_month?: number
    }
    time_slots: Array<{
      start_time: string
      end_time: string
      max_participants: number
      price?: number
    }>
    exceptions?: string[]
  }): Promise<RecurringSchedule> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.SCHEDULES}/recurring`, data)
  }

  async updateRecurringSchedule(id: number, data: {
    end_date?: string
    recurrence_pattern?: any
    time_slots?: any[]
    exceptions?: string[]
    apply_to_future?: boolean
  }): Promise<RecurringSchedule> {
    return apiClient.put(`${API_ENDPOINTS.CLASSES.SCHEDULES}/recurring/${id}`, data)
  }

  async deleteRecurringSchedule(id: number, data: {
    delete_future_only?: boolean
    notify_participants?: boolean
  }): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.CLASSES.SCHEDULES}/recurring/${id}`, { data })
  }

  // Class Bookings
  async getBookings(params?: BookingSearchParams): Promise<BookingListResponse> {
    return apiClient.get(API_ENDPOINTS.CLASSES.BOOKINGS, { params })
  }

  async getBooking(id: number): Promise<ClassBooking> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.BOOKINGS}/${id}`)
  }

  async createBooking(data: BookClassRequest): Promise<ClassBooking> {
    return apiClient.post(API_ENDPOINTS.CLASSES.BOOKINGS, data)
  }

  async cancelBooking(id: number, data?: {
    reason?: string
    refund_requested?: boolean
  }): Promise<ClassBooking> {
    return apiClient.patch(`${API_ENDPOINTS.CLASSES.BOOKINGS}/${id}/cancel`, data)
  }

  async checkInBooking(id: number): Promise<ClassBooking> {
    return apiClient.patch(`${API_ENDPOINTS.CLASSES.BOOKINGS}/${id}/check-in`)
  }

  async noShowBooking(id: number, reason?: string): Promise<ClassBooking> {
    return apiClient.patch(`${API_ENDPOINTS.CLASSES.BOOKINGS}/${id}/no-show`, { reason })
  }

  // Waitlist
  async joinWaitlist(scheduleId: number, data?: {
    user_id?: number
    priority?: number
    notes?: string
  }): Promise<ClassWaitlist> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${scheduleId}/waitlist`, data)
  }

  async leaveWaitlist(waitlistId: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.CLASSES.SCHEDULES}/waitlist/${waitlistId}`)
  }

  async getWaitlist(scheduleId: number): Promise<ClassWaitlist[]> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${scheduleId}/waitlist`)
  }

  async processWaitlist(scheduleId: number, data: {
    auto_book?: boolean
    notification_message?: string
  }): Promise<{
    processed: number
    booked: number
    notified: number
  }> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${scheduleId}/process-waitlist`, data)
  }

  // Class Attendance
  async markAttendance(scheduleId: number, data: {
    attendees: Array<{
      user_id: number
      status: 'present' | 'absent' | 'late'
      check_in_time?: string
      notes?: string
    }>
  }): Promise<ClassAttendance[]> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${scheduleId}/attendance`, data)
  }

  async getAttendance(scheduleId: number): Promise<ClassAttendance[]> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${scheduleId}/attendance`)
  }

  async updateAttendance(attendanceId: number, data: {
    status?: 'present' | 'absent' | 'late'
    check_in_time?: string
    notes?: string
  }): Promise<ClassAttendance> {
    return apiClient.put(`${API_ENDPOINTS.CLASSES.SCHEDULES}/attendance/${attendanceId}`, data)
  }

  // Class Ratings
  async rateClass(scheduleId: number, data: {
    rating: number
    review?: string
    instructor_rating?: number
    facility_rating?: number
    difficulty_rating?: number
  }): Promise<ClassRating> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.SCHEDULES}/${scheduleId}/rate`, data)
  }

  async getClassRatings(classId: number, params?: {
    limit?: number
    offset?: number
    min_rating?: number
  }): Promise<{ items: ClassRating[]; total: number; average_rating: number }> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.CLASSES}/${classId}/ratings`, { params })
  }

  async updateRating(ratingId: number, data: {
    rating?: number
    review?: string
    instructor_rating?: number
    facility_rating?: number
    difficulty_rating?: number
  }): Promise<ClassRating> {
    return apiClient.put(`${API_ENDPOINTS.CLASSES.SCHEDULES}/ratings/${ratingId}`, data)
  }

  async deleteRating(ratingId: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.CLASSES.SCHEDULES}/ratings/${ratingId}`)
  }

  // Class Packages
  async getClassPackages(): Promise<ClassPackage[]> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.CLASSES}/packages`)
  }

  async createClassPackage(data: {
    name: string
    description: string
    class_credits: number
    price: number
    validity_days: number
    applicable_classes?: number[]
    max_bookings_per_day?: number
    is_transferable?: boolean
  }): Promise<ClassPackage> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.CLASSES}/packages`, data)
  }

  async updateClassPackage(id: number, data: {
    name?: string
    description?: string
    class_credits?: number
    price?: number
    validity_days?: number
    applicable_classes?: number[]
    max_bookings_per_day?: number
    is_transferable?: boolean
    is_active?: boolean
  }): Promise<ClassPackage> {
    return apiClient.put(`${API_ENDPOINTS.CLASSES.CLASSES}/packages/${id}`, data)
  }

  async deleteClassPackage(id: number): Promise<void> {
    return apiClient.delete(`${API_ENDPOINTS.CLASSES.CLASSES}/packages/${id}`)
  }

  // User Class Packages
  async getUserClassPackages(userId: number): Promise<UserClassPackage[]> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.CLASSES}/users/${userId}/packages`)
  }

  async purchaseClassPackage(data: {
    user_id: number
    package_id: number
    payment_method_id?: number
    discount_code?: string
  }): Promise<UserClassPackage> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.CLASSES}/packages/purchase`, data)
  }

  async transferClassPackage(packageId: number, data: {
    to_user_id: number
    credits_to_transfer: number
    reason?: string
  }): Promise<UserClassPackage> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.CLASSES}/user-packages/${packageId}/transfer`, data)
  }

  // Class Statistics
  async getClassStatistics(): Promise<ClassStatistics> {
    return apiClient.get(API_ENDPOINTS.CLASSES.STATS)
  }

  async getClassUsageStats(classId: number): Promise<{
    total_schedules: number
    total_bookings: number
    total_attendees: number
    average_attendance_rate: number
    average_rating: number
    revenue_generated: number
    popular_time_slots: Array<{
      time_slot: string
      booking_count: number
    }>
  }> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.CLASSES}/${classId}/usage-stats`)
  }

  async getInstructorStats(instructorId: number): Promise<{
    total_classes_taught: number
    total_students: number
    average_class_rating: number
    total_revenue: number
    popular_classes: Array<{
      class_id: number
      class_name: string
      sessions_count: number
    }>
  }> {
    return apiClient.get(`${API_ENDPOINTS.CLASSES.CLASSES}/instructors/${instructorId}/stats`)
  }

  // Bulk Operations
  async bulkCreateSchedules(data: {
    schedules: Array<{
      class_id: number
      instructor_id: number
      start_time: string
      end_time: string
      room: string
      max_participants: number
      price?: number
    }>
  }): Promise<{
    successful: number
    failed: number
    errors: Array<{ index: number; error: string }>
  }> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.SCHEDULES}/bulk-create`, data)
  }

  async bulkCancelBookings(data: {
    booking_ids: number[]
    reason: string
    refund_policy?: 'full' | 'partial' | 'none'
    notify_users?: boolean
  }): Promise<{
    successful: number
    failed: number
    errors: Array<{ booking_id: number; error: string }>
  }> {
    return apiClient.post(`${API_ENDPOINTS.CLASSES.BOOKINGS}/bulk-cancel`, data)
  }

  async exportClassData(params?: {
    class_id?: number
    date_from?: string
    date_to?: string
    include_bookings?: boolean
    include_attendance?: boolean
    include_ratings?: boolean
  }): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.CLASSES.CLASSES}/export`, { params })
  }

  async exportSchedules(params?: {
    date_from?: string
    date_to?: string
    instructor_id?: number
    room?: string
  }): Promise<Blob> {
    return apiClient.downloadFile(`${API_ENDPOINTS.CLASSES.SCHEDULES}/export`, { params })
  }
}

export const classesService = new ClassesService()
export default classesService