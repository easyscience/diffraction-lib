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
        background: 'rgba(0, 0, 0, 0)', // DARK_BACKGROUND_COLOR
        foreground: '#e6e8ee', // DARK_FOREGROUND_COLOR
        axisFrame: '#333', // DARK_AXIS_FRAME_COLOR
        innerTickGrid: '#1e1e1e', // DARK_INNER_TICK_GRID_COLOR
        hoverBackground: '#212121', // DARK_HOVER_BACKGROUND_COLOR
        legend: 'rgba(0, 0, 0, 0.5)', // DARK_LEGEND_BACKGROUND_COLOR
      }
    }
    return {
      background: 'rgba(0, 0, 0, 0)', // LIGHT_BACKGROUND_COLOR
      foreground: '#222222', // LIGHT_FOREGROUND_COLOR
      axisFrame: '#e2e2e2', // LIGHT_AXIS_FRAME_COLOR
      innerTickGrid: '#f2f2f2', // LIGHT_INNER_TICK_GRID_COLOR
      hoverBackground: '#ffffff', // LIGHT_HOVER_BACKGROUND_COLOR
      legend: 'rgba(255, 255, 255, 0.5)', // LIGHT_LEGEND_BACKGROUND_COLOR
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

  function installPlotlyModebarThemeStyle() {
    const styleId = 'ed-plotly-modebar-theme-style'
    if (document.getElementById(styleId)) return

    const style = document.createElement('style')
    style.id = styleId
    style.textContent = [
      '.plotly-graph-div.ed-plotly-themed-modebar .modebar-btn path {',
      '  fill: var(--ed-plotly-modebar-icon-color) !important;',
      '  opacity: var(--ed-plotly-modebar-icon-opacity) !important;',
      '}',
      '.plotly-graph-div.ed-plotly-themed-modebar .modebar-btn:hover path,',
      '.plotly-graph-div.ed-plotly-themed-modebar .modebar-btn.active path {',
      '  fill: var(--ed-plotly-modebar-icon-color) !important;',
      '  opacity: var(--ed-plotly-modebar-icon-hover-opacity) !important;',
      '}',
    ].join('\n')
    document.head.appendChild(style)
  }

  function syncPlotlyModebarTheme(plot, colors) {
    installPlotlyModebarThemeStyle()
    plot.classList.add('ed-plotly-themed-modebar')
    plot.style.setProperty('--ed-plotly-modebar-icon-color', colors.foreground)
    plot.style.setProperty(
      '--ed-plotly-modebar-icon-opacity',
      themeName() === 'dark' ? '0.62' : '0.42',
    )
    plot.style.setProperty(
      '--ed-plotly-modebar-icon-hover-opacity',
      themeName() === 'dark' ? '0.95' : '0.85',
    )
  }

  function syncPlotlyTheme() {
    if (!window.Plotly) return
    const colors = themeColors()
    document.querySelectorAll('.plotly-graph-div').forEach((plot) => {
      if (!plot.layout && !plot._fullLayout) return
      syncPlotlyModebarTheme(plot, colors)
      const update = {
        paper_bgcolor: colors.background,
        plot_bgcolor: colors.background,
        'modebar.bgcolor': colors.background,
        'font.color': colors.foreground,
        'title.font.color': colors.foreground,
        'legend.bgcolor': colors.legend,
        'legend.font.color': colors.foreground,
        'hoverlabel.bgcolor': colors.hoverBackground,
        'hoverlabel.font.color': colors.foreground,
      }
      plotlyAxisNames(plot).forEach((key) => {
        update[`${key}.color`] = colors.foreground
        update[`${key}.gridcolor`] = colors.innerTickGrid
        update[`${key}.linecolor`] = colors.axisFrame
        update[`${key}.zerolinecolor`] = colors.innerTickGrid
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

  function syncPandasTableTheme() {
    const colors = themeColors()
    document.querySelectorAll('.ed-themed-table').forEach((table) => {
      // TABLE_AXIS_FRAME_CSS_VAR
      table.style.setProperty('--ed-axis-frame-color', colors.axisFrame)
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
    syncPandasTableTheme()
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
