document.addEventListener('DOMContentLoaded', () => {
    const alert = document.getElementById('formAlert');
    if (alert?.classList.contains('is-visible')) {
        alert.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});
