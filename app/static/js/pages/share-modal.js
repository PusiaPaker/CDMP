const modal = document.getElementById("modal");

// Get the button that opens the modal
const btn = document.getElementById("modal-btn");

// Get the <span> element that closes the modal
const span = document.getElementsByClassName("close")[0];

const dependent_form_element = document.getElementById("permission-select");
const form_in_question = document.getElementById("share-form");

const username_error = document.getElementById("username-error");

// When the user clicks on the button, open the modal
btn.onclick = function() {
  var selectedOption = dependent_form_element.options[dependent_form_element.selectedIndex].text;
  let usernameValue = form_in_question["username"].value;

  const usernameValid = usernameValue.length >= 3;

  if (selectedOption === "Owner" && usernameValid) {
    modal.style.display = "block";
  } else if (usernameValid) {
    form_in_question.submit();
  } else {
    username_error.style.display = "block";
  }
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}