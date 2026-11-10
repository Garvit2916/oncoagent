export default function ShimmerText({
  text,
  className = '',
}: {
  text: string
  className?: string
}) {
  return (
    <span
      className={`bg-clip-text text-transparent text-shimmer ${className}`}
      style={{
        backgroundImage:
          'linear-gradient(110deg, #34d399 28%, #f0fdfa 42%, #67e8f9 50%, #c4b5fd 62%, #34d399 76%)',
      }}
    >
      {text}
    </span>
  )
}