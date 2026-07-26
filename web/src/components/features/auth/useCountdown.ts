import { useEffect, useState } from 'react'

/** Contagem regressiva em segundos. Usada tanto pelo FloodWait quanto pelo
 *  cooldown do "reenviar código". */
export function useCountdown(seconds: number | null | undefined) {
  const target = seconds ?? 0

  // Reinício por estado derivado durante o render — reagir a `seconds` dentro
  // de um efeito dispararia renders em cascata (e o lint reclama, com razão).
  const [synced, setSynced] = useState(target)
  const [remaining, setRemaining] = useState(target)
  if (target !== synced) {
    setSynced(target)
    setRemaining(target)
  }

  const done = remaining <= 0

  useEffect(() => {
    if (target <= 0 || done) return
    const id = setInterval(
      () => setRemaining((value) => (value <= 1 ? 0 : value - 1)),
      1000,
    )
    return () => clearInterval(id)
  }, [target, done])

  return remaining
}

export function formatCountdown(seconds: number) {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}min ${String(s).padStart(2, '0')}s`
}
