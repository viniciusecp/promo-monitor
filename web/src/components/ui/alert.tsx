import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const alertVariants = cva(
  "flex w-full items-start gap-3 rounded-lg border px-3 py-2.5 text-[13px] leading-relaxed [&>svg]:mt-0.5 [&>svg]:size-4 [&>svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "border-zinc-800 bg-zinc-900 text-zinc-300",
        destructive: "border-red-900/60 bg-red-950/40 text-red-300",
        warning: "border-amber-900/60 bg-amber-950/40 text-amber-300",
        success: "border-emerald-900/60 bg-emerald-950/40 text-emerald-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Alert({
  className,
  variant,
  ...props
}: React.ComponentProps<"div"> & VariantProps<typeof alertVariants>) {
  return (
    <div
      role="alert"
      data-slot="alert"
      className={cn(alertVariants({ variant }), className)}
      {...props}
    />
  )
}

function AlertTitle({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      data-slot="alert-title"
      className={cn("font-medium", className)}
      {...props}
    />
  )
}

function AlertDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="alert-description"
      className={cn("opacity-90", className)}
      {...props}
    />
  )
}

export { Alert, AlertTitle, AlertDescription, alertVariants }
