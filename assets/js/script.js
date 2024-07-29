// scripts.js

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
    document.querySelector('.content').classList.toggle('blurred');
    document.getElementById('overlay').classList.toggle('active');
}


// JavaScript for adjusting maximum slider values
const dailyLimitSlider = document.getElementById('dailyLimit');
const monthlyLimitSlider = document.getElementById('monthlyLimit');
const yearlyLimitSlider = document.getElementById('yearlyLimit');

// Set initial maximum values
// dailyLimitSlider.setAttribute('max', '50000');
// monthlyLimitSlider.setAttribute('max', '50000');
// yearlyLimitSlider.setAttribute('max', '50000');

// Event listeners to update display values
dailyLimitSlider.addEventListener('input', function() {
    document.getElementById('dailyLimitValue').textContent = `${this.value}`;
});

monthlyLimitSlider.addEventListener('input', function() {
    document.getElementById('monthlyLimitValue').textContent = `${this.value}`;
});

yearlyLimitSlider.addEventListener('input', function() {
    document.getElementById('yearlyLimitValue').textContent = `${this.value}`;
});




