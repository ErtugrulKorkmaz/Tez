// Temel JavaScript fonksiyonları
document.addEventListener('DOMContentLoaded', function() {
    console.log('Uygulama yüklendi');
    
    // Hisse tablosunu yenile butonu
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            location.reload();
        });
    }
});

document.getElementById('stock-list').addEventListener('click', function(e) {
    const row = e.target.closest('tr');
    if(row) {
        const symbol = row.firstElementChild.textContent;
        window.location.href = `/stock/${encodeURIComponent(symbol)}`;
    }
});