document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("student-search");
    const box = document.getElementById("suggestions-box");

    input.addEventListener("input", function () {
        const query = input.value.trim();

        if (!query) {
            box.hidden = true;
            box.innerHTML = "";
            return;
        }

        fetch(`/teacher/students/suggestions/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (!data.length) {
                    box.hidden = true;
                    box.innerHTML = "";
                    return;
                }

                let html = "<ul>";
                data.forEach(student => {
                    html += `
                        <li class="suggestion-item" data-email="${student.email}">
                            ${student.email}
                            (Absences: ${student.absence_count})
                            ${student.is_banned ? " - Banned" : ""}
                        </li>
                    `;
                });
                html += "</ul>";

                box.innerHTML = html;
                box.hidden = false;

                document.querySelectorAll(".suggestion-item").forEach(item => {
                    item.addEventListener("click", function () {
                        input.value = this.dataset.email;
                        box.hidden = true;
                        box.innerHTML = "";
                    });
                });
            });
    });

    document.addEventListener("click", function (e) {
        if (!box.contains(e.target) && e.target !== input) {
            box.hidden = true;
        }
    });
});