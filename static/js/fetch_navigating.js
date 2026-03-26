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

function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

function showMessage(text, isSuccess) {
    const box = document.getElementById("custom-message");

    box.textContent = text;
    box.className = "custom-message";

    if (isSuccess) {
        box.classList.add("success");
    } else {
        box.classList.add("error");
    }

    box.classList.remove("hidden");

    setTimeout(() => {
        box.classList.add("hidden");
    }, 3000);
}

//document.addEventListener("DOMContentLoaded", () => {
//    const forms = document.querySelectorAll(".ajax-action-form");
//
  //  forms.forEach(form => {
    //    form.addEventListener("submit", function (e) {
      //      e.preventDefault();
//
  //          const formData = new FormData(form);
//
  //          fetch(form.action, {
    //            method: "POST",
      //          body: formData,
        //        headers: {
          //          "X-CSRFToken": getCookie("csrftoken"),
            //    }
 //           })
   //         .then(response => response.json())
     //       .then(data => {
       //         showMessage(data.message, data.success);
//
  //              if (data.success) {
    //                setTimeout(() => {
      //                  window.location.reload();
        //            }, 800);
          //      }
            //})
     //       .catch(() => {
   //             showMessage("Възникна грешка.", false);
     //       });
       // });
 //   });
//});