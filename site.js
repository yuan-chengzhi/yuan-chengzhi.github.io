/* Progressive enhancement only: all content and the diagram work without JS. */
(() => {
  'use strict';
  const switcher = document.querySelector('.language-switch');
  if (switcher) {
    const base = switcher.getAttribute('href');
    const update = () => { switcher.setAttribute('href', base + window.location.hash); };
    update();
    window.addEventListener('hashchange', update);
  }
  const graph = document.querySelector('.research-map');
  if (graph) {
    const mark = (row) => {
      graph.querySelectorAll('[data-row]').forEach((el) => {
        el.classList.toggle('is-active', Boolean(row) && el.dataset.row === row);
      });
    };
    let hoveredRow = null;
    let focusedRow = null;
    const rowAt = (target) => target instanceof Element
      ? target.closest('.map-node')?.dataset.row || null : null;
    const refresh = () => mark(hoveredRow || focusedRow);
    graph.addEventListener('pointerover', (event) => {
      hoveredRow = rowAt(event.target); refresh();
    });
    graph.addEventListener('pointerleave', () => {
      hoveredRow = null; refresh();
    });
    graph.addEventListener('focusin', (event) => {
      focusedRow = rowAt(event.target); refresh();
    });
    graph.addEventListener('focusout', () => {
      focusedRow = null; refresh();
    });
  }
  document.querySelectorAll('[data-print]').forEach((button) => {
    button.hidden = false;
    button.addEventListener('click', () => window.print());
  });
})();
