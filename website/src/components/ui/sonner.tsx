// src/components/ui/sonner.tsx
// --- START OF FILE ---
import { useTheme } from "next-themes" // Keep this if you still want dark mode adaptation, though we override base colors below
import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  // theme might not be directly needed now if we force the blue style,
  // but keeping it doesn't hurt if other elements might adapt.
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]} // Keep theme prop
      className="toaster group" // Keep base className
      toastOptions={{
        classNames: {
          // --- MODIFICATION START ---
          toast:
            "group toast group-[.toaster]:bg-blue-600 group-[.toaster]:text-white group-[.toaster]:border-blue-700 group-[.toaster]:shadow-lg", // Force blue background, white text, adjust border
          description: "group-[.toast]:text-blue-100", // Lighter text for description on blue bg
          actionButton:
            "group-[.toast]:bg-white group-[.toast]:text-blue-700 group-[.toast]:border-blue-200", // Example: White button with blue text
          cancelButton:
            "group-[.toast]:bg-blue-700 group-[.toast]:text-blue-100 group-[.toast]:border-blue-800", // Example: Darker blue button
          // --- MODIFICATION END ---
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
// --- END OF FILE ---