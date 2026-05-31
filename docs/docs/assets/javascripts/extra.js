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
    const materialScheme =
      document.body?.getAttribute('data-md-color-scheme') ||
      document.documentElement.getAttribute('data-md-color-scheme')
    if (materialScheme === 'slate') return 'dark'
    if (materialScheme === 'default') return 'light'

    const jupyterThemeLight =
      document.body?.getAttribute('data-jp-theme-light') ||
      document.documentElement.getAttribute('data-jp-theme-light')
    if (jupyterThemeLight === 'false') return 'dark'
    if (jupyterThemeLight === 'true') return 'light'

    return 'light'
  }

  function themeColors() {
    if (themeName() === 'dark') {
      return {
        background: 'rgba(0, 0, 0, 0)',
        foreground: '#e6e8ee',
        grid: 'rgba(110, 145, 190, 0.35)',
        hoverBackground: '#212121',
        legend: 'rgba(0, 0, 0, 0.5)',
      }
    }
    return {
      background: 'rgba(0, 0, 0, 0)',
      foreground: '#222222',
      grid: 'rgba(120, 140, 160, 0.28)',
      hoverBackground: '#ffffff',
      legend: 'rgba(255, 255, 255, 0.5)',
    }
  }

  function plotlyAxisNames(plot) {
    const names = new Set(['xaxis', 'yaxis'])
    ;[plot.layout, plot._fullLayout].forEach((layout) => {
      if (!layout) return
      Object.keys(layout).forEach((key) => {
        if (/^[xyz]axis[0-9]*$/.test(key)) {
          names.add(key)
        }
      })
    })
    return names
  }

  function syncPlotlyTheme() {
    if (!window.Plotly) return
    const colors = themeColors()
    document.querySelectorAll('.plotly-graph-div').forEach((plot) => {
      if (!plot.layout && !plot._fullLayout) return
      const update = {
        paper_bgcolor: colors.background,
        plot_bgcolor: colors.background,
        'font.color': colors.foreground,
        'title.font.color': colors.foreground,
        'legend.bgcolor': colors.legend,
        'legend.font.color': colors.foreground,
        'hoverlabel.bgcolor': colors.hoverBackground,
        'hoverlabel.font.color': colors.foreground,
      }
      plotlyAxisNames(plot).forEach((key) => {
        update[`${key}.color`] = colors.foreground
        update[`${key}.gridcolor`] = colors.grid
        update[`${key}.linecolor`] = colors.grid
        update[`${key}.zerolinecolor`] = colors.grid
        update[`${key}.title.font.color`] = colors.foreground
        update[`${key}.tickfont.color`] = colors.foreground
      })
      try {
        const result = window.Plotly.relayout(plot, update)
        if (result && typeof result.then === 'function') {
          result.then(function () {
            window.Plotly.redraw(plot)
          })
        } else {
          window.Plotly.redraw(plot)
        }
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
    const themeObserver = new MutationObserver(syncThemeAwareOutputs)
    const attributeFilter = [
      'data-md-color-scheme',
      'data-jp-theme-light',
      'data-jp-theme-name',
    ]
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter,
    })
    if (document.body) {
      themeObserver.observe(document.body, {
        attributes: true,
        attributeFilter,
      })
    }
  }
})()
