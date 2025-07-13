'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence, Variants } from 'framer-motion'

// Variantes de animación predefinidos
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { duration: 0.3, ease: 'easeOut' }
  },
  exit: { 
    opacity: 0,
    transition: { duration: 0.2, ease: 'easeIn' }
  }
}

export const slideInFromTop: Variants = {
  hidden: { 
    opacity: 0, 
    y: -20,
    scale: 0.95
  },
  visible: { 
    opacity: 1, 
    y: 0,
    scale: 1,
    transition: { 
      duration: 0.4, 
      ease: [0.25, 0.46, 0.45, 0.94],
      staggerChildren: 0.1
    }
  },
  exit: { 
    opacity: 0, 
    y: -20,
    scale: 0.95,
    transition: { duration: 0.2 }
  }
}

export const slideInFromBottom: Variants = {
  hidden: { 
    opacity: 0, 
    y: 20,
    scale: 0.95
  },
  visible: { 
    opacity: 1, 
    y: 0,
    scale: 1,
    transition: { 
      duration: 0.4, 
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  },
  exit: { 
    opacity: 0, 
    y: 20,
    scale: 0.95,
    transition: { duration: 0.2 }
  }
}

export const slideInFromLeft: Variants = {
  hidden: { 
    opacity: 0, 
    x: -20,
    scale: 0.95
  },
  visible: { 
    opacity: 1, 
    x: 0,
    scale: 1,
    transition: { 
      duration: 0.4, 
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  },
  exit: { 
    opacity: 0, 
    x: -20,
    scale: 0.95,
    transition: { duration: 0.2 }
  }
}

export const slideInFromRight: Variants = {
  hidden: { 
    opacity: 0, 
    x: 20,
    scale: 0.95
  },
  visible: { 
    opacity: 1, 
    x: 0,
    scale: 1,
    transition: { 
      duration: 0.4, 
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  },
  exit: { 
    opacity: 0, 
    x: 20,
    scale: 0.95,
    transition: { duration: 0.2 }
  }
}

export const scaleIn: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.8
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { 
      duration: 0.3, 
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.8,
    transition: { duration: 0.2 }
  }
}

export const bounceIn: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.3,
    y: 50
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: { 
      duration: 0.6,
      ease: [0.68, -0.55, 0.265, 1.55]
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.3,
    y: 50,
    transition: { duration: 0.3 }
  }
}

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1
    }
  }
}

export const staggerItem: Variants = {
  hidden: { 
    opacity: 0, 
    y: 20 
  },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.4,
      ease: [0.25, 0.46, 0.45, 0.94]
    }
  }
}

// Componente de animación de entrada
interface AnimatedEntryProps {
  children: React.ReactNode
  animation?: Variants
  delay?: number
  className?: string
  onAnimationComplete?: () => void
}

export function AnimatedEntry({ 
  children, 
  animation = fadeIn, 
  delay = 0, 
  className = '',
  onAnimationComplete 
}: AnimatedEntryProps) {
  return (
    <motion.div
      variants={animation}
      initial="hidden"
      animate="visible"
      exit="exit"
      transition={{ delay }}
      className={className}
      onAnimationComplete={onAnimationComplete}
    >
      {children}
    </motion.div>
  )
}

// Componente de lista animada
interface AnimatedListProps {
  children: React.ReactNode
  className?: string
}

export function AnimatedList({ children, className = '' }: AnimatedListProps) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className={className}
    >
      {children}
    </motion.div>
  )
}

// Componente de item de lista animado
interface AnimatedListItemProps {
  children: React.ReactNode
  className?: string
}

export function AnimatedListItem({ children, className = '' }: AnimatedListItemProps) {
  return (
    <motion.div
      variants={staggerItem}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// Componente de página con animación
interface AnimatedPageProps {
  children: React.ReactNode
  className?: string
}

export function AnimatedPage({ children, className = '' }: AnimatedPageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ 
        duration: 0.4,
        ease: [0.25, 0.46, 0.45, 0.94]
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// Componente de hover con animación
interface AnimatedHoverProps {
  children: React.ReactNode
  className?: string
  scale?: number
  duration?: number
}

export function AnimatedHover({ 
  children, 
  className = '', 
  scale = 1.05, 
  duration = 0.2 
}: AnimatedHoverProps) {
  return (
    <motion.div
      whileHover={{ 
        scale,
        transition: { duration }
      }}
      whileTap={{ 
        scale: 0.95,
        transition: { duration: 0.1 }
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// Componente de botón animado
interface AnimatedButtonProps {
  children: React.ReactNode
  onClick?: () => void
  className?: string
  disabled?: boolean
  loading?: boolean
}

export function AnimatedButton({ 
  children, 
  onClick, 
  className = '', 
  disabled = false,
  loading = false
}: AnimatedButtonProps) {
  return (
    <motion.button
      whileHover={{ 
        scale: disabled ? 1 : 1.05,
        transition: { duration: 0.2 }
      }}
      whileTap={{ 
        scale: disabled ? 1 : 0.95,
        transition: { duration: 0.1 }
      }}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        relative overflow-hidden transition-colors duration-200
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${className}
      `}
    >
      {children}
      {loading && (
        <motion.div
          className="absolute inset-0 bg-white/20"
          initial={{ x: '-100%' }}
          animate={{ x: '100%' }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        />
      )}
    </motion.button>
  )
}

// Componente de skeleton animado
interface AnimatedSkeletonProps {
  className?: string
  lines?: number
}

export function AnimatedSkeleton({ className = '', lines = 1 }: AnimatedSkeletonProps) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <motion.div
          key={i}
          className="h-4 bg-gray-200 dark:bg-gray-700 rounded"
          initial={{ opacity: 0.6 }}
          animate={{ opacity: 1 }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
          style={{
            animationDelay: `${i * 0.1}s`
          }}
        />
      ))}
    </div>
  )
}

// Componente de progreso animado
interface AnimatedProgressProps {
  value: number
  max?: number
  className?: string
  color?: string
}

export function AnimatedProgress({ 
  value, 
  max = 100, 
  className = '',
  color = 'primary'
}: AnimatedProgressProps) {
  const percentage = Math.min((value / max) * 100, 100)

  return (
    <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 ${className}`}>
      <motion.div
        className={`h-2 rounded-full bg-${color}`}
        initial={{ width: 0 }}
        animate={{ width: `${percentage}%` }}
        transition={{ 
          duration: 0.8,
          ease: [0.25, 0.46, 0.45, 0.94]
        }}
      />
    </div>
  )
}

// Componente de contador animado
interface AnimatedCounterProps {
  value: number
  duration?: number
  className?: string
  format?: (value: number) => string
}

export function AnimatedCounter({ 
  value, 
  duration = 1, 
  className = '',
  format = (val) => val.toString()
}: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    const startValue = displayValue
    const endValue = value
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / (duration * 1000), 1)
      
      const currentValue = Math.floor(startValue + (endValue - startValue) * progress)
      setDisplayValue(currentValue)

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    animate()
  }, [value, duration, displayValue])

  return (
    <span className={className}>
      {format(displayValue)}
    </span>
  )
}

// Hook para animaciones basadas en scroll
export function useScrollAnimation() {
  const [isInView, setIsInView] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsInView(entry.isIntersecting)
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current)
      }
    }
  }, [])

  return { ref, isInView }
}

// Componente de animación basada en scroll
interface ScrollAnimatedProps {
  children: React.ReactNode
  animation?: Variants
  className?: string
  threshold?: number
}

export function ScrollAnimated({ 
  children, 
  animation = fadeIn, 
  className = '',
  threshold = 0.1
}: ScrollAnimatedProps) {
  const { ref, isInView } = useScrollAnimation()

  return (
    <motion.div
      ref={ref}
      variants={animation}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// Componente de transición de página
interface PageTransitionProps {
  children: React.ReactNode
  className?: string
}

export function PageTransition({ children, className = '' }: PageTransitionProps) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ 
          duration: 0.3,
          ease: [0.25, 0.46, 0.45, 0.94]
        }}
        className={className}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
} 