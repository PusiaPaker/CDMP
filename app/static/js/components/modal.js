const modal = document.getElementById("modal");

// Get the button that opens the modal
const btn = document.getElementById("modal-btn");

// Get the <span> element that closes the modal
const span = document.getElementsByClassName("close")[0];

if (modal && btn && span) {
  const openModal = function() {
    modal.style.display = "block";
    document.body.classList.add("modal-open");
  };

  const closeModal = function() {
    modal.style.display = "none";
    document.body.classList.remove("modal-open");
  };

  btn.onclick = openModal;
  span.onclick = closeModal;

  window.addEventListener("click", function(event) {
    if (event.target === modal) {
      closeModal();
    }
  });

  window.addEventListener("keydown", function(event) {
    if (event.key === "Escape" && modal.style.display === "block") {
      closeModal();
    }
  });
}
