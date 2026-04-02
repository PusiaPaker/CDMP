document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("calendar-event-modal");
    if (!modal) {
        return;
    }

    const editForm = document.getElementById("calendar-event-edit-form");
    const deleteForm = document.getElementById("calendar-event-delete-form");
    const modalTitle = document.getElementById("calendar-event-modal-title");
    const modalProject = document.getElementById("calendar-event-modal-project");
    const titleInput = document.getElementById("modal-title-input");
    const startInput = document.getElementById("modal-start-input");
    const endInput = document.getElementById("modal-end-input");
    const descriptionInput = document.getElementById("modal-description-input");
    const projectSelect = document.getElementById("modal-project-select");

    function openModal(trigger) {
        editForm.action = trigger.dataset.updateUrl;
        deleteForm.action = trigger.dataset.deleteUrl;

        modalTitle.textContent = trigger.dataset.title || "Edit Event";
        modalProject.textContent = trigger.dataset.projectLabel || "Calendar Event";

        titleInput.value = trigger.dataset.title || "";
        startInput.value = trigger.dataset.start || "";
        endInput.value = trigger.dataset.end || "";
        descriptionInput.value = trigger.dataset.description || "";
        projectSelect.value = trigger.dataset.projectId || "";

        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");
        titleInput.focus();
    }

    function closeModal() {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");
    }

    for (const trigger of document.querySelectorAll(".calendar-event-trigger")) {
        trigger.addEventListener("click", function () {
            openModal(trigger);
        });
    }

    for (const closeTrigger of modal.querySelectorAll("[data-modal-close]")) {
        closeTrigger.addEventListener("click", closeModal);
    }

    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && modal.classList.contains("is-open")) {
            closeModal();
        }
    });
});
