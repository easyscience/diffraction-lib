;(function () {
  'use strict'

  const header = document.getElementsByTagName('header')[0]

  function toggleHeaderShadow() {
    if (!header) return
    if (window.pageYOffset <= 0) {
      header.classList.remove('md-header--shadow')
    } else {
      header.classList.add('md-header--shadow')
    }
  }

  function themeName() {
    return document.documentElement.getAttribute('data-md-color-scheme') === 'slate'
      ? 'dark'
      : 'light'
  }

  function themeColors() {
    if (themeName() === 'dark') {
      return {
        background: '#262626',
        foreground: '#a3a3a3',
        grid: 'rgba(163, 163, 163, 0.22)',
      }
    }
    return {
      background: '#fafafa',
      foreground: '#525252',
      grid: 'rgba(82, 82, 82, 0.18)',
    }
  }

  function syncPlotlyTheme() {
    if (!window.Plotly) return
    const colors = themeColors()
    document.querySelectorAll('.plotly-graph-div').forEach((plot) => {
      if (!plot.layout) return
      const update = {
        paper_bgcolor: colors.background,
        plot_bgcolor: colors.background,
        'font.color': colors.foreground,
        'legend.font.color': colors.foreground,
      }
      Object.keys(plot.layout).forEach((key) => {
        if (/^[xy]axis[0-9]*$/.test(key)) {
          update[`${key}.color`] = colors.foreground
          update[`${key}.gridcolor`] = colors.grid
          update[`${key}.linecolor`] = colors.grid
          update[`${key}.zerolinecolor`] = colors.grid
        }
      })
      try {
        window.Plotly.relayout(plot, update)
      } catch (_error) {
        // Keep one stale chart from blocking the rest of the page theme update.
      }
    })
  }

  function syncCrysviewTheme() {
    const next = themeName()
    document.querySelectorAll('.crysview').forEach((viewer) => {
      viewer.classList.toggle('cv-host-theme-dark', next === 'dark')
      viewer.classList.toggle('cv-host-theme-light', next !== 'dark')
      if (typeof viewer.__crysviewApplyTheme === 'function') {
        viewer.__crysviewApplyTheme(next)
      }
    })
  }

  function syncThemeAwareOutputs() {
    syncPlotlyTheme()
    syncCrysviewTheme()
  }

  window.addEventListener('load', function () {
    toggleHeaderShadow()
    syncThemeAwareOutputs()
  })

  window.addEventListener('scroll', function () {
    toggleHeaderShadow()
  })

  if (window.MutationObserver) {
    new MutationObserver(syncThemeAwareOutputs).observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-md-color-scheme'],
    })
  }
})()
