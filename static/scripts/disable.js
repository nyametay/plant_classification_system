const checkbox1 = document.getElementById('option1');
const checkbox2 = document.getElementById('option2');
const form1 = document.getElementById('form1');
const form2 = document.getElementById('form2');
const wrapper1 = document.getElementById('wrapper-1')
const wrapper2 = document.getElementById('wrapper-2')

checkbox1.addEventListener('change', function() {
    if (checkbox1.checked) {
        form2.querySelectorAll('input, button, select, textarea').forEach(element => element.disabled = true);
        wrapper2.style.display = 'none';
    } else {
        form2.querySelectorAll('input, button, select, textarea').forEach(element => element.disabled = false);
        wrapper2.style.display = 'block';
    }
});

checkbox2.addEventListener('change', function() {
    if (checkbox2.checked) {
        form1.querySelectorAll('input, button, select, textarea').forEach(element => element.disabled = true);
        wrapper1.style.display = 'none';
    } else {
        form1.querySelectorAll('input, button, select, textarea').forEach(element => element.disabled = false);
        wrapper1.style.display = 'block';
    }
});