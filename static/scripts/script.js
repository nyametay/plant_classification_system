const selectImage = document.querySelector('.select-image');
const inputFile = document.querySelector('#file'); // Correct selector
const imgArea = document.querySelector('.img-area');
const submitImage = document.querySelector('.submit');

selectImage.addEventListener('click', function () {
    inputFile.click();
});

inputFile.addEventListener('change', function () {
    const image = this.files[0];
    if (image.size < 5000000) { // 5MB size limit
        const reader = new FileReader();
        reader.onload = () => {
            const allImg = imgArea.querySelectorAll('img');
            allImg.forEach(item => item.remove());
            const imgUrl = reader.result;
            const img = document.createElement('img');
            img.src = imgUrl;
            imgArea.appendChild(img);
            imgArea.classList.add('active');
            imgArea.dataset.img = image.name;
        };
        reader.readAsDataURL(image);
    } else {
        alert("Image size is more than 2MB");
    }
});

submitImage.addEventListener('click', function (event) {
    // Prevent default form submission to handle via JS if needed
    document.getElementById('uploadForm').submit();
});