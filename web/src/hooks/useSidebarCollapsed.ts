import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'promo-monitor:sidebar-collapsed'

function readStored(): boolean {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(STORAGE_KEY) === '1'
}

/**
 * Estado de "menu comprimido" do desktop, persistido em localStorage.
 * A leitura é feita no inicializador do useState para o primeiro paint já sair
 * na largura certa — ler num efeito daria um flash da sidebar aberta.
 */
export function useSidebarCollapsed() {
  const [collapsed, setCollapsed] = useState(readStored)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, collapsed ? '1' : '0')
  }, [collapsed])

  const toggle = useCallback(() => setCollapsed((value) => !value), [])

  return { collapsed, toggle }
}
