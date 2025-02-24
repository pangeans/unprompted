import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-base shadow-sm",
          "transition-all duration-200 ease-in-out",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium",
          "placeholder:text-muted-foreground placeholder:transition-opacity placeholder:duration-200",
          "focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:ring-opacity-50",
          "focus:placeholder:opacity-75",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "empty:animate-pulse",
          "caret-blue-500 animate-caret-blink",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
