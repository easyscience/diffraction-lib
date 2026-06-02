/*
 * Shared lazy loader for EasyDiffraction interactive figures.
 *
 * Loaded once per docs page (mkdocs `extra_javascript`). Plotly figures
 * emitted in SHARED embedding mode are inert placeholders carrying their
 * spec as `application/json`; this loader renders each one lazily when it
 * scrolls near the viewport (IntersectionObserver), behind a "Loading…"
 * skeleton. It also centralizes the theme-sync, resize, and legend-toggle
 * behavior that used to be duplicated inline in every figure.
 *
 * Three.js structure scenes manage their own lazy boot (they are ES
 * modules resolved through the page-level import map); this file handles
 * Plotly only.
 *
 * Source of truth for behavior:
 * src/easydiffraction/display/plotters/plotly.py. Theme colors arrive in
 * each figure's payload (`edTheme`) so Python stays the single source.
 */
(function () {
  'use strict';

  var FIGURE_SELECTOR = '.ed-figure[data-ed-figure="plotly"]';
  var ROOT_MARGIN = '200px';

  function plotlyConfig() {
    return {
      displayModeBar: true,
      displaylogo: false,
      responsive: true,
      modeBarButtonsToRemove: [
        'select2d',
        'lasso2d',
        'zoomIn2d',
        'zoomOut2d',
        'autoScale2d',
      ],
    };
  }

  function readSpec(figureEl) {
    var specEl = figureEl.querySelector('script.ed-figure-spec');
    if (!specEl) {
      return null;
    }
    try {
      return JSON.parse(specEl.textContent);
    } catch (err) {
      return null;
    }
  }

  function hostTheme() {
    var scheme =
      (document.body && document.body.getAttribute('data-md-color-scheme')) ||
      (document.documentElement &&
        document.documentElement.getAttribute('data-md-color-scheme'));
    return scheme === 'slate' ? 'dark' : 'light';
  }

  // ---- Theme sync -----------------------------------------------------

  function axisNames(graphDiv) {
    var names = { xaxis: true, yaxis: true };
    [graphDiv.layout, graphDiv._fullLayout].forEach(function (layout) {
      if (!layout) {
        return;
      }
      Object.keys(layout).forEach(function (key) {
        if (/^[xyz]axis[0-9]*$/.test(key)) {
          names[key] = true;
        }
      });
    });
    return Object.keys(names);
  }

  function correlationColorscale(colors) {
    return [
      [0.0, '#d73027'],
      [0.5, colors.background],
      [1.0, '#4575b4'],
    ];
  }

  function rgbaFromColor(color, alpha) {
    var hexMatch = color.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
    var red;
    var green;
    var blue;
    if (hexMatch) {
      var hex = hexMatch[1];
      if (hex.length === 3) {
        hex = hex
          .split('')
          .map(function (part) {
            return part + part;
          })
          .join('');
      }
      red = parseInt(hex.slice(0, 2), 16);
      green = parseInt(hex.slice(2, 4), 16);
      blue = parseInt(hex.slice(4, 6), 16);
    } else {
      var parts = color.match(/(\d+(?:\.\d+)?)/g);
      if (!parts || parts.length < 3) {
        return color;
      }
      red = Number(parts[0]);
      green = Number(parts[1]);
      blue = Number(parts[2]);
    }
    return 'rgba(' + red + ', ' + green + ', ' + blue + ', ' + alpha + ')';
  }

  function installModebarIconStyle(graphDiv, mode, colors) {
    graphDiv.classList.add('ed-plotly-themed-modebar');
    var styleId = 'ed-plotly-modebar-icon-style';
    var style = document.getElementById(styleId);
    if (!style) {
      style = document.createElement('style');
      style.id = styleId;
      document.head.appendChild(style);
    }
    var inactive = rgbaFromColor(colors.foreground, mode === 'dark' ? 0.62 : 0.55);
    var active = rgbaFromColor(colors.foreground, mode === 'dark' ? 0.95 : 0.9);
    style.textContent =
      '.ed-plotly-themed-modebar .modebar-btn path { fill: ' + inactive + ' !important; }' +
      '.ed-plotly-themed-modebar .modebar-btn:hover path,' +
      '.ed-plotly-themed-modebar .modebar-btn.active path { fill: ' + active + ' !important; }';
  }

  function applyTheme(graphDiv, theme, themeSync) {
    if (!graphDiv || !window.Plotly || !theme) {
      return;
    }
    var mode = hostTheme();
    var colors = theme[mode] || theme.light;
    if (!colors) {
      return;
    }
    installModebarIconStyle(graphDiv, mode, colors);
    var paperBackground = colors.paperBackground || 'rgba(0, 0, 0, 0)';
    var transparentPlot = themeSync && themeSync.correlationHeatmap === true;
    var modebarColor = rgbaFromColor(colors.foreground, mode === 'dark' ? 0.62 : 0.42);
    var modebarActiveColor = rgbaFromColor(colors.foreground, mode === 'dark' ? 0.95 : 0.85);
    var update = {
      paper_bgcolor: paperBackground,
      plot_bgcolor: transparentPlot ? paperBackground : colors.background,
      'modebar.bgcolor': paperBackground,
      'modebar.color': modebarColor,
      'modebar.activecolor': modebarActiveColor,
      'font.color': colors.foreground,
      'title.font.color': colors.foreground,
      'legend.bgcolor': colors.legend,
      'legend.font.color': colors.foreground,
      'hoverlabel.bgcolor': colors.hoverBackground,
      'hoverlabel.bordercolor': colors.axisFrame,
      'hoverlabel.font.color': colors.foreground,
    };
    axisNames(graphDiv).forEach(function (name) {
      update[name + '.color'] = colors.foreground;
      update[name + '.gridcolor'] = colors.innerTickGrid;
      update[name + '.linecolor'] = colors.axisFrame;
      update[name + '.zerolinecolor'] = colors.innerTickGrid;
      update[name + '.title.font.color'] = colors.foreground;
      update[name + '.tickfont.color'] = colors.foreground;
    });
    var annotations =
      (graphDiv.layout && graphDiv.layout.annotations) ||
      (graphDiv._fullLayout && graphDiv._fullLayout.annotations) ||
      [];
    annotations.forEach(function (_unused, index) {
      update['annotations[' + index + '].font.color'] = colors.foreground;
    });
    if (themeSync && Array.isArray(themeSync.axisFrameShapeIndexes)) {
      themeSync.axisFrameShapeIndexes.forEach(function (shapeIndex) {
        if (Number.isInteger(shapeIndex) && shapeIndex >= 0) {
          update['shapes[' + shapeIndex + '].line.color'] = colors.axisFrame;
        }
      });
    }
    try {
      var pending = [window.Plotly.relayout(graphDiv, update)];
      if (themeSync && themeSync.correlationHeatmap) {
        (graphDiv.data || []).forEach(function (trace, index) {
          if (trace && trace.type === 'heatmap') {
            pending.push(
              window.Plotly.restyle(
                graphDiv,
                { colorscale: [correlationColorscale(colors)] },
                [index],
              ),
            );
          }
        });
      }
      Promise.all(
        pending.filter(function (item) {
          return item && typeof item.then === 'function';
        }),
      );
    } catch (err) {
      /* keep theme switching from breaking interaction with the figure */
    }
  }

  function watchTheme(graphDiv, theme, themeSync) {
    applyTheme(graphDiv, theme, themeSync);
    if (!window.MutationObserver) {
      return;
    }
    var observer = new MutationObserver(function () {
      applyTheme(graphDiv, theme, themeSync);
    });
    var filter = {
      attributes: true,
      attributeFilter: ['data-md-color-scheme'],
    };
    observer.observe(document.documentElement, filter);
    if (document.body) {
      observer.observe(document.body, filter);
    }
  }

  // ---- Resize ---------------------------------------------------------

  function watchResize(graphDiv) {
    if (!window.Plotly || !window.Plotly.Plots) {
      return;
    }
    var pending = false;
    function resize() {
      if (pending) {
        return;
      }
      pending = true;
      window.requestAnimationFrame(function () {
        pending = false;
        if (!graphDiv.isConnected || graphDiv.offsetParent === null) {
          return;
        }
        window.Plotly.Plots.resize(graphDiv);
      });
    }
    if (window.ResizeObserver) {
      var observer = new ResizeObserver(resize);
      observer.observe(graphDiv);
      if (graphDiv.parentElement) {
        observer.observe(graphDiv.parentElement);
      }
    }
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) {
        resize();
      }
    });
    window.addEventListener('pageshow', resize);
  }

  // ---- Legend toggle modebar button -----------------------------------

  function readLegendVisible(graphDiv) {
    var legend = graphDiv.querySelector('.legend');
    if (legend) {
      var style = window.getComputedStyle(legend);
      return style.display !== 'none' && style.visibility !== 'hidden';
    }
    if (graphDiv._fullLayout && typeof graphDiv._fullLayout.showlegend === 'boolean') {
      return graphDiv._fullLayout.showlegend;
    }
    return true;
  }

  function setLegendVisible(graphDiv, visible) {
    var legend = graphDiv.querySelector('.legend');
    if (legend) {
      legend.style.display = visible ? 'inline' : 'none';
      legend.style.visibility = visible ? 'visible' : 'hidden';
      legend.style.pointerEvents = visible ? '' : 'none';
    }
    if (graphDiv.layout) {
      graphDiv.layout.showlegend = visible;
    }
    var button = graphDiv.querySelector('[data-legend-toggle="true"]');
    if (button) {
      button.classList.toggle('active', visible);
      button.setAttribute('aria-pressed', String(visible));
    }
  }

  function installLegendToggle(graphDiv) {
    function build() {
      var modebar = graphDiv.querySelector('.modebar');
      if (!modebar || !modebar.querySelector('.modebar-group')) {
        return;
      }
      var button = modebar.querySelector('[data-legend-toggle="true"]');
      if (!button) {
        var group = document.createElement('div');
        group.className = 'modebar-group';
        button = document.createElement('a');
        button.className = 'modebar-btn';
        button.href = 'javascript:void(0)';
        button.setAttribute('data-title', 'Toggle legend');
        button.setAttribute('data-legend-toggle', 'true');
        button.setAttribute('aria-label', 'Toggle legend');
        button.setAttribute('role', 'button');
        button.setAttribute('tabindex', '0');
        button.innerHTML =
          '<svg viewBox="0 0 1000 1000" class="icon" height="1em" width="1em"' +
          ' aria-hidden="true"><path d="M120 160H240V280H120z M120 440H240V560H120z' +
          ' M120 720H240V840H120z M320 200H880V240H320z M320 480H880V520H320z' +
          ' M320 760H880V800H320z"></path></svg>';
        group.appendChild(button);
        modebar.appendChild(group);
      }
      function toggle(event) {
        if (event) {
          event.preventDefault();
          event.stopPropagation();
        }
        setLegendVisible(graphDiv, !readLegendVisible(graphDiv));
      }
      button.onclick = toggle;
      button.onkeydown = function (event) {
        if (event.key === 'Enter' || event.key === ' ') {
          toggle(event);
        }
      };
      setLegendVisible(graphDiv, readLegendVisible(graphDiv));
    }
    if (graphDiv.on) {
      graphDiv.on('plotly_afterplot', build);
    }
    window.requestAnimationFrame(build);
  }

  // ---- Activation -----------------------------------------------------

  function render(figureEl) {
    if (figureEl.getAttribute('data-ed-rendered') === 'true') {
      return;
    }
    var spec = readSpec(figureEl);
    var target = figureEl.querySelector('.ed-figure-target');
    if (!spec || !target || !window.Plotly) {
      return;
    }
    figureEl.setAttribute('data-ed-rendered', 'true');
    var config = spec.config || plotlyConfig();
    window.Plotly.newPlot(target, spec.data || [], spec.layout || {}, config).then(
      function () {
        figureEl.classList.add('ed-figure--ready');
        watchTheme(target, spec.edTheme, spec.edThemeSync);
        watchResize(target);
        if (spec.edHasLegend) {
          installLegendToggle(target);
        }
      },
    );
  }

  function activate() {
    var figures = document.querySelectorAll(FIGURE_SELECTOR);
    if (!figures.length) {
      return;
    }
    var list = Array.prototype.slice.call(figures);
    var eager =
      !('IntersectionObserver' in window) ||
      (window.matchMedia && window.matchMedia('print').matches);
    if (eager) {
      list.forEach(render);
      return;
    }
    var observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            render(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { rootMargin: ROOT_MARGIN },
    );
    list.forEach(function (figureEl) {
      observer.observe(figureEl);
    });
    // Render everything before printing so off-screen figures appear.
    window.addEventListener('beforeprint', function () {
      list.forEach(render);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', activate);
  } else {
    activate();
  }
})();
