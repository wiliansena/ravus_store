const menu = document.getElementById('app-menu');
const menuTriggers = document.querySelectorAll('[data-open-menu]');
if (menu) {
  menuTriggers.forEach(button => button.addEventListener('click', () => {
    menu.showModal();
    document.body.classList.add('menu-open');
    menuTriggers.forEach(trigger => trigger.setAttribute('aria-expanded', 'true'));
  }));
  menu.querySelector('[data-close-menu]').addEventListener('click', () => menu.close());
  menu.addEventListener('click', event => {
    const bounds = menu.getBoundingClientRect();
    if (event.target === menu && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) menu.close();
  });
  menu.addEventListener('close', () => {
    document.body.classList.remove('menu-open');
    menuTriggers.forEach(trigger => trigger.setAttribute('aria-expanded', 'false'));
  });
}

// Add mobile labels without replacing the table or its form controls.
document.querySelectorAll('.app-page main table').forEach(table => {
  if (table.closest('.receipt')) return;
  const headings = Array.from(table.querySelectorAll('thead th'), th => th.textContent.trim());
  if (!headings.length) return;
  table.classList.add('responsive-table');
  table.querySelectorAll('tbody tr').forEach(row => {
    Array.from(row.cells).forEach((cell, index) => {
      if (cell.colSpan > 1) cell.classList.add('empty-cell');
      else cell.dataset.label = headings[index] || 'Ações';
    });
  });
});
