import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#000',
          color: '#fff',
          fontFamily: 'var(--font-sans)',
          padding: '2rem',
        }}>
          <div style={{ textAlign: 'center', maxWidth: 500 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
            <h2 style={{ fontFamily: 'var(--font-sans)', marginBottom: 8 }}>
              Something went wrong
            </h2>
            <p style={{ color: '#a3a3a3', fontSize: 14, marginBottom: 24 }}>
              {this.state.error?.message || 'Unknown error'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.reload()
              }}
              style={{
                padding: '8px 24px',
                background: '#FFA028',
                color: '#fff',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
                fontWeight: 600,
                fontSize: 14,
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
