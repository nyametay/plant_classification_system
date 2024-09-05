// Get references to the elements
const choosePathButton = document.getElementById('choose_path');
const modal = document.getElementById('modal');
const closeModalButton = document.getElementById('closeModal');
const textButton = document.getElementById('textButton');
const imageButton = document.getElementById('imageButton');

// URLs for redirection
const textURL = '/search'; 
const imageURL = '/scan'; 

// Function to open the modal
function openModal() {
    modal.classList.add('active');
}

// Function to close the modal
function closeModal() {
    modal.classList.remove('active');
}

// Event listeners
choosePathButton.addEventListener('click', function(e) {
    e.preventDefault(); // Prevent the default anchor behavior
    openModal();
});

closeModalButton.addEventListener('click', closeModal);

// Redirect on button click
textButton.addEventListener('click', function() {
    window.location.href = textURL;
});

imageButton.addEventListener('click', function() {
    window.location.href = imageURL;
});

// Optionally, close modal when clicking outside of content
modal.querySelector('.overlay').addEventListener('click', closeModal);