(function () {
  const modal = document.getElementById("modal");
  const btn = document.getElementById("modal-btn");
  const span = document.getElementsByClassName("close")[0];
  const dependentFormElement = document.getElementById("permission-select");
  const formInQuestion = document.getElementById("share-form");
  const emailError = document.getElementById("email-error");

  if (btn && modal && span && dependentFormElement && formInQuestion) {
    btn.onclick = function () {
      const selectedOption = dependentFormElement.options[dependentFormElement.selectedIndex].text;
      const emailValue = formInQuestion["email"].value.trim();
      const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue);

      if (selectedOption === "Owner" && emailValid) {
        modal.style.display = "block";
      } else if (emailValid) {
        formInQuestion.submit();
      } else if (emailError) {
        emailError.style.display = "block";
      }
    };

    span.onclick = function () {
      modal.style.display = "none";
    };

    window.addEventListener("click", (event) => {
      if (event.target === modal) {
        modal.style.display = "none";
      }
    });

    formInQuestion["email"]?.addEventListener("input", () => {
      if (emailError) {
        emailError.style.display = "none";
      }
    });
  }

  const roleSelects = document.querySelectorAll("[data-role-select]");

  roleSelects.forEach((select) => {
    select.addEventListener("change", () => {
      const form = select.closest("[data-role-form]");
      if (!form) {
        return;
      }

      const originalValue = select.dataset.originalValue || "";
      const nextValue = select.value;
      const username = form.querySelector('input[name="username"]')?.value || "this user";

      let confirmed = true;

      if (nextValue === "owner") {
        confirmed = window.confirm(
          `Give ${username} owner access? Owners can change permissions and delete the project.`
        );
      } else if (nextValue === "remove") {
        confirmed = window.confirm(`Remove ${username}'s access to this project?`);
      }

      if (!confirmed) {
        select.value = originalValue;
        return;
      }

      form.submit();
    });
  });
})();
