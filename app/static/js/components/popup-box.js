const popupBoxOverlay = document.querySelector("[data-popup-box]");

if (popupBoxOverlay) {
    const closePopupBox = () => {
        popupBoxOverlay.remove();
        document.removeEventListener("keydown", onPopupBoxKeyDown);
    };

    const onPopupBoxKeyDown = (event) => {
        if (event.key === "Escape") {
            closePopupBox();
        }
    };

    popupBoxOverlay.querySelectorAll("[data-popup-box-close]").forEach((button) => {
        button.addEventListener("click", closePopupBox);
    });

    popupBoxOverlay.addEventListener("click", (event) => {
        if (event.target === popupBoxOverlay) {
            closePopupBox();
        }
    });

    document.addEventListener("keydown", onPopupBoxKeyDown);
}
