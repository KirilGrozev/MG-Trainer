document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".ajax-action-form").forEach(form => {
        form.addEventListener("submit", async function (e) {
            e.preventDefault();

            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: formData,
                    credentials: "same-origin",
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    alert("Action failed.");
                }
            } catch (error) {
                alert("Something went wrong.");
            }
        });
    });
});